from sqlalchemy import Column, BigInteger, String, DateTime, Text, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("advice_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), nullable=False)  # 'user' or 'assistant' or 'system' or 'tool'
    content = Column(Text, nullable=False)
    action_type = Column(String(64))
    action_status = Column(String(64))  # pending, confirmed, cancelled, executed
    action_data = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    session = relationship("AdviceSession", back_populates="chat_messages")
    user = relationship("User")