from sqlalchemy import Column, BigInteger, String, DateTime, Text, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class AdviceSession(Base):
    __tablename__ = "advice_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    user_question = Column(Text)
    context_text = Column(Text)
    ai_response_json = Column(JSON)
    scenario = Column(String(64), default="OTHER")
    # 修复 boolean 映射: MySQL 时代是 tinyint(1)，PG 端是 BOOLEAN
    is_training_day = Column(Boolean, default=False)
    # Stores restaurant search results for the session (used when user selects a restaurant)
    restaurant_context = Column(JSON, default=dict)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="advice_sessions")
    diet_advice_records = relationship("DietAdviceRecord", back_populates="session")
    chat_messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class DietAdviceRecord(Base):
    __tablename__ = "diet_advice_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(BigInteger, ForeignKey("advice_sessions.id", ondelete="CASCADE"), nullable=False)
    situation_summary = Column(Text)
    recommendation_strategy = Column(Text)
    recommended_options_json = Column(JSON)
    not_recommended_json = Column(JSON)
    estimated_summary_json = Column(JSON)
    next_meal_advice = Column(Text)
    sleep_friendly_tips = Column(Text)
    risk_level = Column(String(64), default="LOW")
    created_at = Column(DateTime, nullable=False, default=func.now())

    user = relationship("User")
    session = relationship("AdviceSession", back_populates="diet_advice_records")