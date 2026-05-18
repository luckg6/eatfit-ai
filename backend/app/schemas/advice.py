from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, datetime


class AdviceRequest(BaseModel):
    question: str
    context: Optional[str] = None
    is_training_day: bool = False
    scenario: Optional[str] = "OTHER"


class RecommendedOption(BaseModel):
    name: str
    why_recommended: str
    estimated_calories: int
    estimated_protein: int
    estimated_carbs: int
    estimated_fat: int
    order_modification: str
    suitable_for: List[str]
    score: int


class NotRecommendedOption(BaseModel):
    name: str
    reason: str
    better_alternative: str


class AdviceResponse(BaseModel):
    situation_summary: str
    goal_analysis: str
    recommendation_strategy: str
    recommended_options: List[RecommendedOption]
    not_recommended: List[NotRecommendedOption]
    today_remaining_advice: str
    sleep_friendly_tips: str
    training_day_tips: str
    next_meal_advice: str
    risk_level: str
    risk_warnings: List[str]
    one_sentence_summary: str


class AdviceSessionResponse(BaseModel):
    id: int
    title: Optional[str]
    user_question: str
    context_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DailyPlanRequest(BaseModel):
    is_training_day: bool = False


class DailyPlanResponse(BaseModel):
    breakfast_suggestion: str
    lunch_suggestion: str
    dinner_suggestion: str
    snack_suggestion: str
    protein_focus: str
    avoid_today: List[str]
    sleep_reminder: str
    one_day_strategy: str


class WeeklyReviewResponse(BaseModel):
    week_summary: str
    what_went_well: List[str]
    main_problems: List[str]
    protein_consistency: str
    sleep_impact_analysis: str
    eating_out_pattern: str
    weight_and_body_fat_trend: str
    next_week_strategy: str
    next_week_actions: List[str]
    warnings: List[str]


class ChatMessageCreate(BaseModel):
    role: str
    content: str
    action_type: Optional[str] = None
    action_status: Optional[str] = None
    action_data: Optional[Any] = None


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    action_type: Optional[str]
    action_status: Optional[str]
    action_data: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    scenario: Optional[str] = "OTHER"
    is_training_day: bool = False


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    scenario: Optional[str]
    is_training_day: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    message: str
    scenario: Optional[str] = "OTHER"
    is_training_day: bool = False
    session_id: Optional[int] = None


class SendMessageResponse(BaseModel):
    session_id: int
    message_id: int
    response: AdviceResponse
    pending_meal_action: Optional[dict] = None