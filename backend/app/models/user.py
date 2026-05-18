from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True)
    email = Column(String(128), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    auto_memory_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    food_profile = relationship("UserFoodProfile", back_populates="user", uselist=False)
    memories = relationship("MemoryItem", back_populates="user")
    meal_logs = relationship("MealLog", back_populates="user")
    advice_sessions = relationship("AdviceSession", back_populates="user")
    weight_records = relationship("WeightRecord", back_populates="user")
    body_fat_records = relationship("BodyFatRecord", back_populates="user")
    training_records = relationship("TrainingRecord", back_populates="user")