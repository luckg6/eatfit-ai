from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MealLogBase(BaseModel):
    meal_type: str
    meal_time: datetime
    food_text: str
    scenario: Optional[str] = None
    estimated_calories: Optional[float] = None
    estimated_protein: Optional[float] = None
    estimated_carbs: Optional[float] = None
    estimated_fat: Optional[float] = None
    health_score: Optional[int] = None
    sleep_impact: Optional[str] = "UNKNOWN"
    ai_comment: Optional[str] = None


class MealLogResponse(MealLogBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class MealLogCreate(MealLogBase):
    pass


class MealLogUpdate(BaseModel):
    meal_type: Optional[str] = None
    meal_time: Optional[datetime] = None
    food_text: Optional[str] = None
    scenario: Optional[str] = None
    estimated_calories: Optional[float] = None
    estimated_protein: Optional[float] = None
    estimated_carbs: Optional[float] = None
    estimated_fat: Optional[float] = None
    health_score: Optional[int] = None
    sleep_impact: Optional[str] = None
    ai_comment: Optional[str] = None


class MealSummary(BaseModel):
    date: str
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    meals: List[MealLogResponse]