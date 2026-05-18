from sqlalchemy import Column, BigInteger, String, DateTime, DECIMAL, Text, Integer, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    meal_type = Column(String(64), nullable=False)
    meal_time = Column(DateTime, nullable=False)
    food_text = Column(Text, nullable=False)
    scenario = Column(String(64))
    estimated_calories = Column(DECIMAL(8, 2))
    estimated_protein = Column(DECIMAL(8, 2))
    estimated_carbs = Column(DECIMAL(8, 2))
    estimated_fat = Column(DECIMAL(8, 2))
    calorie_confidence = Column(DECIMAL(4, 2), default=0.70)
    nutrition_source = Column(String(64), default="llm_estimate")  # llm_estimate, manual, food_database
    source_message_id = Column(BigInteger, nullable=True)
    health_score = Column(Integer)
    sleep_impact = Column(String(64), default="UNKNOWN")
    ai_comment = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="meal_logs")