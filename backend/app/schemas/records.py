from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class WeightRecordBase(BaseModel):
    weight_kg: float
    record_date: date
    note: Optional[str] = None


class WeightRecordResponse(WeightRecordBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BodyFatRecordBase(BaseModel):
    body_fat_percent: float
    record_date: date
    note: Optional[str] = None


class BodyFatRecordResponse(BodyFatRecordBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingRecordBase(BaseModel):
    training_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    intensity: Optional[str] = None
    record_date: date
    note: Optional[str] = None


class TrainingRecordResponse(TrainingRecordBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True