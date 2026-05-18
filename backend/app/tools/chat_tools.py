"""
Enhanced chat tools for the EatFit Agent.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.advice import AdviceSession


class ChatTools:
    """Tools for managing chat messages and sessions."""

    def __init__(self, db: Session):
        self.db = db

    def save_message(self, session_id: int, user_id: int, role: str, content: str,
                     action_type: Optional[str] = None, action_status: Optional[str] = None,
                     action_data: Optional[Dict] = None) -> ChatMessage:
        """Save a chat message to the database."""
        message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            action_type=action_type,
            action_status=action_status,
            action_data=action_data
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_session_messages(self, session_id: int, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all messages in a session."""
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()

        return [self._message_to_dict(m) for m in messages]

    def get_recent_messages(self, session_id: int, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages in a session."""
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

        return [self._message_to_dict(m) for m in reversed(messages)]

    def update_message_action(self, message_id: int, action_status: str, action_data: Optional[Dict] = None) -> Optional[ChatMessage]:
        """Update message action status and data."""
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            return None

        if action_status:
            message.action_status = action_status
        if action_data is not None:
            message.action_data = action_data

        self.db.commit()
        self.db.refresh(message)
        return message

    def get_pending_actions(self, session_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get all pending actions in a session."""
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id,
            ChatMessage.action_status == "pending",
            ChatMessage.action_type.isnot(None)
        ).all()

        return [
            {
                "message_id": m.id,
                "action_type": m.action_type,
                "action_data": m.action_data,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]

    def create_or_get_session(self, user_id: int, title: Optional[str] = None,
                               scenario: str = "OTHER", is_training_day: bool = False) -> AdviceSession:
        """Create a new session or get existing one."""
        # Try to get most recent session
        session = self.db.query(AdviceSession).filter(
            AdviceSession.user_id == user_id
        ).order_by(AdviceSession.created_at.desc()).first()

        if not session:
            session = AdviceSession(
                user_id=user_id,
                title=title or "新对话",
                scenario=scenario,
                is_training_day=1 if is_training_day else 0
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

        return session

    def get_chat_context_for_advice(self, user_id: int, session_id: int) -> Dict[str, Any]:
        """Aggregate context for advice generation."""
        messages = self.get_recent_messages(session_id, user_id, limit=10)

        # Extract pending actions
        pending_meal_logs = []
        pending_profile_updates = []
        pending_memory_confirms = []

        for msg in messages:
            if msg.get("action_status") == "pending":
                if msg.get("action_type") == "meal_log":
                    pending_meal_logs.append(msg)
                elif msg.get("action_type") == "profile_update":
                    pending_profile_updates.append(msg)
                elif msg.get("action_type") == "memory_confirm":
                    pending_memory_confirms.append(msg)

        return {
            "recent_messages": messages,
            "pending_actions": {
                "meal_logs": pending_meal_logs,
                "profile_updates": pending_profile_updates,
                "memory_confirms": pending_memory_confirms
            }
        }

    def _message_to_dict(self, message: ChatMessage) -> Dict[str, Any]:
        return {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "action_type": message.action_type,
            "action_status": message.action_status,
            "action_data": message.action_data,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat() if message.updated_at else None,
        }