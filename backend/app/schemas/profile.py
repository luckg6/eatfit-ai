from pydantic import BaseModel
from typing import Optional, List


class UserFoodProfileBase(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    target_weight_kg: Optional[float] = None
    primary_goal: Optional[str] = None
    activity_level: Optional[str] = None
    training_frequency: Optional[int] = None
    training_type: Optional[str] = None
    food_preferences: Optional[str] = None
    food_dislikes: Optional[str] = None
    allergies: Optional[str] = None
    budget_per_meal: Optional[float] = None
    common_eating_scenarios: Optional[str] = None
    sleep_sensitive: bool = False
    sleep_notes: Optional[str] = None
    notes: Optional[str] = None


class UserFoodProfileResponse(UserFoodProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class UserFoodProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    target_weight_kg: Optional[float] = None
    primary_goal: Optional[str] = None
    activity_level: Optional[str] = None
    training_frequency: Optional[int] = None
    training_type: Optional[str] = None
    food_preferences: Optional[str] = None
    food_dislikes: Optional[str] = None
    allergies: Optional[str] = None
    budget_per_meal: Optional[float] = None
    common_eating_scenarios: Optional[str] = None
    sleep_sensitive: Optional[bool] = None
    sleep_notes: Optional[str] = None
    notes: Optional[str] = None