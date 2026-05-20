import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.advice import AdviceSession
from app.models.chat_message import ChatMessage
from app.schemas.advice import (
    AdviceRequest, AdviceResponse,
    DailyPlanRequest, DailyPlanResponse, WeeklyReviewResponse,
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse,
    SendMessageRequest, SendMessageResponse,
    RestaurantDetailRequest, RestaurantDetailResponse
)
from app.services.llm_service import get_llm_service
from app.services.advice_service import AdviceService
from app.services.memory_extractor import MemoryExtractor

logger = logging.getLogger("eatfit.advice")
router = APIRouter(prefix="/api/advice", tags=["advice"])


# ---- Session management ----

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    session = AdviceSession(
        user_id=current_user.id,
        title=data.title or "新对话",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        scenario=data.scenario or "OTHER",
        is_training_day=data.is_training_day,
        created_at=session.created_at
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_sessions(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's chat sessions."""
    sessions = db.query(AdviceSession).filter(
        AdviceSession.user_id == current_user.id
    ).order_by(AdviceSession.created_at.desc()).limit(limit).all()

    return [
        ChatSessionResponse(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            scenario=getattr(s, 'scenario', 'OTHER'),
            is_training_day=getattr(s, 'is_training_day', False),
            created_at=s.created_at
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a session."""
    session = db.query(AdviceSession).filter(
        AdviceSession.id == session_id,
        AdviceSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()

    return [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            action_type=m.action_type,
            action_status=m.action_status,
            action_data=m.action_data,
            created_at=m.created_at
        )
        for m in messages
    ]


@router.patch("/sessions/{session_id}/messages/{message_id}", response_model=ChatMessageResponse)
def update_message(
    session_id: int,
    message_id: int,
    data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a message (e.g., confirm a pending action)."""
    msg = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.session_id == session_id,
        ChatMessage.user_id == current_user.id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if data.action_status is not None:
        msg.action_status = data.action_status
    if data.action_data is not None:
        msg.action_data = data.action_data

    db.commit()
    db.refresh(msg)

    return ChatMessageResponse(
        id=msg.id,
        session_id=msg.session_id,
        role=msg.role,
        content=msg.content,
        action_type=msg.action_type,
        action_status=msg.action_status,
        action_data=msg.action_data,
        created_at=msg.created_at
    )


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a session and all its messages."""
    session = db.query(AdviceSession).filter(
        AdviceSession.id == session_id,
        AdviceSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)  # cascade deletes chat_messages
    db.commit()
    return {"status": "ok"}


# ---- SSE Streaming chat send message ----

@router.post("/send-stream")
async def send_message_stream(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response via SSE streaming."""
    from app.agent.diet_agent_loop import DietAgentLoop

    logger.info(f"[send_message_stream] user_id={current_user.id}, message='{request.message[:80]}...'")

    async def event_generator():
        from app.services.llm_service import get_llm_service

        # Load restaurant_context from session if exists
        session_rc = None
        if request.session_id:
            session = db.query(AdviceSession).filter(
                AdviceSession.id == request.session_id,
                AdviceSession.user_id == current_user.id
            ).first()
            if session and session.restaurant_context:
                session_rc = session.restaurant_context

        agent = DietAgentLoop(db, current_user, request.latitude, request.longitude, restaurant_context=session_rc)

        # Create or get session
        session = None
        if request.session_id:
            session = db.query(AdviceSession).filter(
                AdviceSession.id == request.session_id,
                AdviceSession.user_id == current_user.id
            ).first()

        if not session:
            # No session_id or session not found -> create NEW session
            session = AdviceSession(
                user_id=current_user.id,
                title=request.message[:50] if len(request.message) > 50 else request.message,
                user_question=request.message[:200] if request.message else "新对话",
                scenario=request.scenario or "OTHER",
                is_training_day=1 if request.is_training_day else 0
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

        # Yield intent detected
        import json
        yield f"event: intent_detected\ndata: {json.dumps({'intent': 'pending', 'confidence': 0.5})}\n\n"

        # Run agent loop
        try:
            agent_response = await agent.run(request.message, session.id)
        except Exception as e:
            logger.error(f"[send_message_stream] agent.run failed: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            return

        # Save restaurant_context back to session if it was updated
        if agent._restaurant_context:
            session.restaurant_context = agent._restaurant_context
            db.commit()

        # Yield agent steps
        for step in agent_response.steps:
            yield f"event: agent_step\ndata: {json.dumps(step)}\n\n"

        # Yield pending action if exists
        try:
            if agent_response.action:
                # Save assistant message with pending action
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
                # Save assistant message without pending action
                ai_msg = ChatMessage(
                    session_id=session.id,
                    user_id=current_user.id,
                    role="assistant",
                    content=agent_response.text
                )
                db.add(ai_msg)
                db.commit()
                db.refresh(ai_msg)

            # Yield message done
            yield f"event: message_done\ndata: {json.dumps({'message_id': ai_msg.id, 'session_id': session.id, 'content': agent_response.text})}\n\n"

            # Memory extraction if enabled
            if current_user.auto_memory_enabled and agent_response.memory_action:
                # Save memory pending action
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

    from starlette.responses import StreamingResponse
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response, with meal/training detection."""
    logger.info(f"[send_message] user_id={current_user.id}, message='{request.message[:80]}...'")
    logger.info(f"[send_message] scenario={request.scenario}, is_training_day={request.is_training_day}, session_id={request.session_id}")

    # Find or create session
    session = None
    if request.session_id:
        session = db.query(AdviceSession).filter(
            AdviceSession.id == request.session_id,
            AdviceSession.user_id == current_user.id
        ).first()
        if session:
            logger.info(f"[send_message] Using provided session_id={session.id}")

    if not session:
        session = db.query(AdviceSession).filter(
            AdviceSession.user_id == current_user.id
        ).order_by(AdviceSession.created_at.desc()).first()

    if not session:
        logger.info(f"[send_message] Creating new session for user {current_user.id}")
        session = AdviceSession(
            user_id=current_user.id,
            title=request.message[:50] if len(request.message) > 50 else request.message,
            user_question=request.message[:200] if request.message else "新对话",
            scenario=request.scenario or "OTHER",
            is_training_day=request.is_training_day or False
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    else:
        logger.info(f"[send_message] Using existing session_id={session.id}")

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
    logger.info(f"[send_message] User message saved, id={user_msg.id}")

    # Get context for LLM
    advice_service = AdviceService(db, current_user)
    profile = advice_service._get_profile()
    memories = advice_service._get_memories()
    today_meals = advice_service._get_today_meals()
    recent_trainings = advice_service._get_recent_trainings()
    logger.info(f"[send_message] Context loaded - profile={profile is not None}, memories={len(memories)}, today_meals={len(today_meals)}")

    # Generate advice
    from app.prompts.diet_advice import DietAdvicePromptBuilder
    system_prompt, user_prompt = DietAdvicePromptBuilder.build(
        user_question=request.message,
        context=None,
        profile=profile,
        memories=memories,
        today_meals=today_meals,
        recent_trainings=recent_trainings,
        is_training_day=request.is_training_day,
        scenario=request.scenario
    )

    logger.info("[send_message] Calling LLM...")
    llm = get_llm_service()
    response_text = await llm.generate(system_prompt, user_prompt)
    logger.info(f"[send_message] LLM response received, length={len(response_text)}, preview='{response_text[:200]}...'")

    # Parse response
    import json
    try:
        response_data = json.loads(response_text)
        logger.info(f"[send_message] JSON parsed successfully, keys={list(response_data.keys())}")
    except json.JSONDecodeError as e:
        logger.error(f"[send_message] JSON parse failed: {e}, response_text='{response_text[:300]}...'")
        response_data = {
            "situation_summary": "无法解析AI回复",
            "goal_analysis": "",
            "recommendation_strategy": "请稍后重试",
            "recommended_options": [],
            "not_recommended": [],
            "today_remaining_advice": "",
            "sleep_friendly_tips": "",
            "training_day_tips": "",
            "next_meal_advice": "",
            "risk_level": "MEDIUM",
            "risk_warnings": ["AI回复解析失败"],
            "one_sentence_summary": "请稍后重试"
        }

    # Save AI response as message
    ai_msg = ChatMessage(
        session_id=session.id,
        user_id=current_user.id,
        role="assistant",
        content=response_text  # Store raw LLM response for display
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    logger.info(f"[send_message] AI message saved, id={ai_msg.id}")

    # Proactive memory extraction
    if current_user.auto_memory_enabled:
        logger.info("[send_message] Triggering memory extraction...")
        await MemoryExtractor.extract_and_save(
            db=db,
            user=current_user,
            user_question=request.message,
            ai_response=response_data
        )
        logger.info("[send_message] Memory extraction completed")
    else:
        logger.info("[send_message] Memory extraction skipped (auto_memory_enabled=False)")

    # Return response
    logger.info(f"[send_message] Returning response, session_id={session.id}, message_id={ai_msg.id}")
    return SendMessageResponse(
        session_id=session.id,
        message_id=ai_msg.id,
        response=response_data,
        pending_meal_action=None
    )


# ---- Original endpoints (kept for compatibility) ----

@router.post("/generate", response_model=AdviceResponse)
async def generate_advice(
    request: AdviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    advice_service = AdviceService(db, current_user)
    result = await advice_service.generate_advice(
        question=request.question,
        context=request.context,
        is_training_day=request.is_training_day,
        scenario=request.scenario
    )
    return result


@router.get("/history", response_model=List[dict])
def list_advice_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(AdviceSession).filter(
        AdviceSession.user_id == current_user.id
    ).order_by(AdviceSession.created_at.desc()).limit(limit).all()

    return [
        {
            "id": s.id,
            "title": s.title,
            "user_question": s.user_question,
            "created_at": s.created_at.isoformat()
        }
        for s in sessions
    ]


@router.get("/history/{session_id}")
def get_advice_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(AdviceSession).filter(
        AdviceSession.id == session_id,
        AdviceSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "title": session.title,
        "user_question": session.user_question,
        "context_text": session.context_text,
        "ai_response": session.ai_response_json,
        "created_at": session.created_at.isoformat()
    }


@router.post("/daily-plan", response_model=DailyPlanResponse)
async def generate_daily_plan(
    request: DailyPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    advice_service = AdviceService(db, current_user)
    result = await advice_service.generate_daily_plan(is_training_day=request.is_training_day)
    return result


@router.post("/weekly-review", response_model=WeeklyReviewResponse)
async def generate_weekly_review(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    advice_service = AdviceService(db, current_user)
    result = await advice_service.generate_weekly_review()
    return result


@router.post("/restaurant-detail", response_model=RestaurantDetailResponse)
async def get_restaurant_detail(
    request: RestaurantDetailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed info for a restaurant and analyze using LLM with user context."""
    from app.tools.restaurant_tools import RestaurantTools

    logger.info(f"[get_restaurant_detail] uid={request.uid}, name={request.name}")

    tools = RestaurantTools(db)
    details = await tools.get_restaurant_details(request.uid)
    logger.info(f"[get_restaurant_detail] raw details: {details}")

    if not details:
        return RestaurantDetailResponse(content=f'抱歉，无法获取"{request.name}"的详细信息。')

    # Get user profile and memories for context
    advice_service = AdviceService(db, current_user)
    profile = advice_service._get_profile()
    memories = advice_service._get_memories()

    # Format details for LLM
    detail_info = details.get("detail_info", {})
    content_tag = detail_info.get("content_tag", "")
    classified_tag = detail_info.get("classified_poi_tag", "")

    restaurant_info = {
        "name": request.name,
        "address": details.get("address", ""),
        "telephone": details.get("telephone", ""),
        "rating": detail_info.get("overall_rating", ""),
        "price": detail_info.get("price", ""),
        "tag": detail_info.get("tag", ""),
        "shop_hours": detail_info.get("shop_hours", ""),
        "classified_tag": classified_tag,
        "content_tag": content_tag,
    }

    # Build context for LLM analysis
    context_parts = [f"餐厅信息:\n{json.dumps(restaurant_info, ensure_ascii=False, indent=2)}"]

    if profile:
        context_parts.append(f"\n用户画像:")
        if profile.get("primary_goal"):
            goal_map = {"FAT_LOSS": "减脂", "MUSCLE_GAIN": "增肌", "MAINTAIN": "维持"}
            context_parts.append(f"- 目标: {goal_map.get(profile['primary_goal'], profile['primary_goal'])}")
        if profile.get("budget_per_meal"):
            context_parts.append(f"- 预算: {profile['budget_per_meal']}元/餐")
        if profile.get("weight_kg"):
            context_parts.append(f"- 体重: {profile['weight_kg']}kg")
        if profile.get("food_preferences"):
            context_parts.append(f"- 饮食偏好: {profile['food_preferences']}")
        if profile.get("food_dislikes"):
            context_parts.append(f"- 不喜欢: {profile['food_dislikes']}")
        if profile.get("allergies"):
            context_parts.append(f"- 过敏: {profile['allergies']}")

    if memories:
        context_parts.append(f"\n用户记忆:")
        for m in memories[:5]:
            context_parts.append(f"- [{m['memory_type']}] {m['content']}")

    # Call LLM for personalized analysis
    system_prompt = """你是一个专业的饮食顾问。根据餐厅详细信息和用户上下文，给出个性化的饮食建议。

分析要点：
1. 根据用户目标（增肌/减脂/维持）分析餐厅菜品是否适合
2. 考虑用户的预算、饮食偏好、过敏情况
3. 结合餐厅类型和标签给出具体建议
4. 如果有过敏或不耐受，务必提醒

回复格式：
先用 markdown 格式展示餐厅基本信息，然后给出针对用户目标的个性化分析和建议。"""

    user_prompt = "\n".join(context_parts) + "\n\n请分析这家餐厅是否符合用户的饮食目标，并给出建议。"

    llm = get_llm_service()
    analysis = await llm.generate(system_prompt, user_prompt)

    logger.info(f"[get_restaurant_detail] LLM analysis length={len(analysis)}")
    return RestaurantDetailResponse(content=analysis)