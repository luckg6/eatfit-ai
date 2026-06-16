"""
Chat turn orchestration service.

Owns one chat turn end-to-end and yields SSE-formatted event frames:

  - agent_step  : per ReAct step in agent_response.steps
  - action_pending: assistant reply carries a pending action
  - message_done: assistant reply is direct text (no pending action)
  - memory_pending: low-importance memory candidate awaiting confirmation
  - error       : any unexpected exception during agent run or persistence

Pure structural extraction from app/api/advice.py's send_message_stream
closure — every commit/refresh/yield/except behaviour matches the original
event_generator verbatim. Caller wraps this generator in a StreamingResponse.
"""
import json
import logging
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.models.advice import AdviceSession
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.advice import SendMessageRequest

# Reuse the same logger name as the original advice.py module so that any
# downstream log filters keyed on logger=='eatfit.advice' keep matching.
logger = logging.getLogger("eatfit.advice")


async def stream_chat_turn(
    *,
    db: Session,
    current_user: User,
    request: SendMessageRequest,
) -> AsyncGenerator[str, None]:
    """Run one chat turn and yield SSE-formatted event frames.

    The caller wraps this generator in a StreamingResponse.
    """
    # Lazy import kept on purpose — matches the original closure's import
    # location, avoids any future circular-import risk between api/ and agent/.
    from app.agent.orchestrator import Orchestrator

    agent = Orchestrator(db, current_user, request.latitude, request.longitude)

    # Create or get session
    session = None
    if request.session_id:
        session = db.query(AdviceSession).filter(
            AdviceSession.id == request.session_id,
            AdviceSession.user_id == current_user.id
        ).first()

    if not session:
        session = AdviceSession(
            user_id=current_user.id,
            title=request.message[:50] if len(request.message) > 50 else request.message,
            scenario=request.scenario or "OTHER",
            # PG 端是 BOOLEAN，不要再传 int
            is_training_day=bool(request.is_training_day)
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        user_id=current_user.id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # NOTE: 之前这里会先 yield 一条 `event: intent_detected\ndata: {}` 占位事件，
    # 然后 agent 跑完又会把自己的 INTENT_DETECTED 步骤塞进 agent_response.steps，
    # 再由下面的循环 yield 一遍 —— 结果前端会看到两条"意图识别"重复步骤。
    # 删掉占位事件，意图识别只走 agent_step 通道，保证 1:1 真实回放。

    # Run agent loop
    try:
        agent_response = await agent.run(request.message, session.id)
    except Exception as e:
        logger.error(f"[send_message_stream] agent.run failed: {e}", exc_info=True)
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        return

    # Yield agent steps
    for step in agent_response.steps:
        yield f"event: agent_step\ndata: {json.dumps(step)}\n\n"

    # Yield pending action or direct response
    try:
        if agent_response.action:
            ai_msg = ChatMessage(
                session_id=session.id,
                user_id=current_user.id,
                role="assistant",
                content=agent_response.text,
                action_type=agent_response.action.get("action_type"),
                action_status=agent_response.action.get("action_status"),
                action_data=agent_response.action.get("action_data")
            )
            db.add(ai_msg)
            db.commit()
            db.refresh(ai_msg)
            yield f"event: action_pending\ndata: {json.dumps({'message_id': ai_msg.id, 'action': agent_response.action})}\n\n"
        else:
            ai_msg = ChatMessage(
                session_id=session.id,
                user_id=current_user.id,
                role="assistant",
                content=agent_response.text
            )
            db.add(ai_msg)
            db.commit()
            db.refresh(ai_msg)

        yield f"event: message_done\ndata: {json.dumps({'message_id': ai_msg.id, 'session_id': session.id, 'content': agent_response.text})}\n\n"

        # Memory extraction if enabled
        if current_user.auto_memory_enabled and agent_response.memory_action:
            memory_msg = ChatMessage(
                session_id=session.id,
                user_id=current_user.id,
                role="assistant",
                content=agent_response.text + "\n\n" + agent_response.memory_action.get("display_text", ""),
                action_type="memory_confirm",
                action_status="pending",
                action_data=agent_response.memory_action
            )
            db.add(memory_msg)
            db.commit()
            db.refresh(memory_msg)
            yield f"event: memory_pending\ndata: {json.dumps({'message_id': memory_msg.id, 'memory_action': agent_response.memory_action})}\n\n"
    except Exception as e:
        logger.error(f"[send_message_stream] yielding response failed: {e}", exc_info=True)
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
