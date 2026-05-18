from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MemoryItemBase(BaseModel):
    memory_type: str
    content: str
    importance_score: int = 5
    source: str = "manual"
    status: str = "active"
    confidence_score: float = 0.80


class MemoryItemResponse(MemoryItemBase):
    id: int
    user_id: int
    source_message_id: Optional[int] = None
    last_used_at: Optional[datetime] = None
    metadata_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemoryItemCreate(MemoryItemBase):
    pass


class MemoryItemUpdate(BaseModel):
    memory_type: Optional[str] = None
    content: Optional[str] = None
    importance_score: Optional[int] = None
    status: Optional[str] = None


class AutoMemoryUpdate(BaseModel):
    auto_memory_enabled: bool