from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, DECIMAL, Text, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserFoodProfile(Base):
    __tablename__ = "user_food_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    nickname = Column(String(64))
    gender = Column(String(32))
    age = Column(BigInteger)
    height_cm = Column(DECIMAL(5, 2))
    weight_kg = Column(DECIMAL(5, 2))
    body_fat_percent = Column(DECIMAL(5, 2))
    target_weight_kg = Column(DECIMAL(5, 2))
    primary_goal = Column(String(64))
    activity_level = Column(String(64))
    training_frequency = Column(BigInteger)
    training_type = Column(String(128))
    food_preferences = Column(Text)
    food_dislikes = Column(Text)
    allergies = Column(Text)
    budget_per_meal = Column(DECIMAL(8, 2))
    common_eating_scenarios = Column(Text)
    sleep_sensitive = Column(Boolean, nullable=False, default=False)
    sleep_notes = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="food_profile")