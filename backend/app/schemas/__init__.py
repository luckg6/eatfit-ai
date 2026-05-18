from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from app.schemas.profile import UserFoodProfileBase, UserFoodProfileResponse, UserFoodProfileUpdate
from app.schemas.memory import MemoryItemBase, MemoryItemResponse, MemoryItemCreate, MemoryItemUpdate, AutoMemoryUpdate
from app.schemas.meal import MealLogBase, MealLogResponse, MealLogCreate, MealLogUpdate, MealSummary
from app.schemas.advice import (
    AdviceRequest, AdviceResponse, AdviceSessionResponse,
    RecommendedOption, NotRecommendedOption,
    DailyPlanRequest, DailyPlanResponse, WeeklyReviewResponse
)
from app.schemas.records import (
    WeightRecordBase, WeightRecordResponse,
    BodyFatRecordBase, BodyFatRecordResponse,
    TrainingRecordBase, TrainingRecordResponse
)

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse",
    "UserFoodProfileBase", "UserFoodProfileResponse", "UserFoodProfileUpdate",
    "MemoryItemBase", "MemoryItemResponse", "MemoryItemCreate", "MemoryItemUpdate", "AutoMemoryUpdate",
    "MealLogBase", "MealLogResponse", "MealLogCreate", "MealLogUpdate", "MealSummary",
    "AdviceRequest", "AdviceResponse", "AdviceSessionResponse",
    "RecommendedOption", "NotRecommendedOption",
    "DailyPlanRequest", "DailyPlanResponse", "WeeklyReviewResponse",
    "WeightRecordBase", "WeightRecordResponse",
    "BodyFatRecordBase", "BodyFatRecordResponse",
    "TrainingRecordBase", "TrainingRecordResponse",
]