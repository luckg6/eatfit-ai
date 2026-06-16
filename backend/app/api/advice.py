import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.advice import AdviceSession
from app.models.chat_message import ChatMessage
from app.schemas.advice import (
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse,
    SendMessageRequest,
)
from starlette.responses import StreamingResponse

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
    from app.services.chat_service import stream_chat_turn

    logger.info(f"[send_message_stream] user_id={current_user.id}, message='{request.message[:80]}...'")
    return StreamingResponse(
        stream_chat_turn(db=db, current_user=current_user, request=request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
