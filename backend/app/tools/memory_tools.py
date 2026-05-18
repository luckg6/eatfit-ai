"""
Enhanced memory tools for the EatFit Agent.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.memory import MemoryItem


class MemoryTools:
    """Tools for managing user memories in the agent system."""

    # Memory types for the agent system
    MEMORY_TYPES = [
        "diet_preference",      # 饮食偏好
        "food_dislike",         # 不喜欢的食物
        "allergy_intolerance",  # 过敏/不耐受
        "goal",                 # 长期目标
        "budget",               # 预算偏好
        "location",             # 常用位置
        "scenario",             # 常见饮食场景
        "sleep",                # 睡眠相关
        "body_response",        # 身体反应
        "restriction",          # 现实限制
        "habit",                # 饮食习惯
        "other",                # 其他
    ]

    # High-importance memory types that require user confirmation
    HIGH_IMPORTANCE_TYPES = [
        "allergy_intolerance",
        "body_response",
        "goal",
        "restriction",
        "food_dislike",
    ]

    def __init__(self, db: Session):
        self.db = db

    def get_active_memories(self, user_id: int, memory_types: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all active memories for a user."""
        query = self.db.query(MemoryItem).filter(
            MemoryItem.user_id == user_id,
            MemoryItem.status == "active"
        )
        if memory_types:
            query = query.filter(MemoryItem.memory_type.in_(memory_types))

        memories = query.order_by(MemoryItem.importance_score.desc(), MemoryItem.created_at.desc()).limit(limit).all()
        return [self._memory_to_dict(m) for m in memories]

    def get_relevant_memories(self, user_id: int, intent: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get memories relevant to a specific intent."""
        # Map intents to relevant memory types
        intent_memory_map = {
            "diet_advice": ["goal", "diet_preference", "food_dislike", "allergy_intolerance", "budget", "sleep", "restriction", "habit"],
            "meal_log": ["habit", "scenario", "diet_preference"],
            "profile_update": ["goal", "budget", "restriction"],
            "dashboard_query": ["goal", "habit", "budget"],
        }

        memory_types = intent_memory_map.get(intent, None)
        return self.get_active_memories(user_id, memory_types, limit)

    def create_memory(self, user_id: int, memory_type: str, content: str, importance_score: int = 5,
                      source: str = "auto_extracted", source_message_id: Optional[int] = None,
                      confidence_score: float = 0.8, metadata: Optional[Dict] = None) -> MemoryItem:
        """Create a new memory item."""
        memory = MemoryItem(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            importance_score=importance_score,
            source=source,
            source_message_id=source_message_id,
            confidence_score=confidence_score,
            status="active",
            metadata_json=metadata
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def create_pending_memory(self, user_id: int, memory_type: str, content: str,
                              importance_score: int = 5, source: str = "auto_extracted",
                              source_message_id: Optional[int] = None, confidence_score: float = 0.8) -> Dict[str, Any]:
        """Create a pending memory action data structure for confirmation card."""
        # Check if this is a high-importance memory type
        is_high_importance = memory_type in self.HIGH_IMPORTANCE_TYPES

        return {
            "memory_type": memory_type,
            "content": content,
            "importance_score": importance_score,
            "confidence_score": confidence_score,
            "source": source,
            "source_message_id": source_message_id,
            "is_high_importance": is_high_importance,
            "display_text": self._generate_memory_confirm_text(memory_type, content, is_high_importance)
        }

    def confirm_memory(self, memory_id: int, user_id: int) -> Optional[MemoryItem]:
        """Confirm a pending memory (change status to active)."""
        memory = self.db.query(MemoryItem).filter(
            MemoryItem.id == memory_id,
            MemoryItem.user_id == user_id
        ).first()

        if not memory:
            return None

        memory.status = "active"
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def mark_memory_inactive(self, memory_id: int, user_id: int) -> bool:
        """Soft delete a memory (set status to inactive)."""
        memory = self.db.query(MemoryItem).filter(
            MemoryItem.id == memory_id,
            MemoryItem.user_id == user_id
        ).first()

        if not memory:
            return False

        memory.status = "inactive"
        self.db.commit()
        return True

    def update_memory(self, memory_id: int, user_id: int, content: Optional[str] = None,
                      memory_type: Optional[str] = None, importance_score: Optional[int] = None) -> Optional[MemoryItem]:
        """Update a memory's content or properties."""
        memory = self.db.query(MemoryItem).filter(
            MemoryItem.id == memory_id,
            MemoryItem.user_id == user_id
        ).first()

        if not memory:
            return None

        if content is not None:
            memory.content = content
        if memory_type is not None:
            memory.memory_type = memory_type
        if importance_score is not None:
            memory.importance_score = importance_score

        self.db.commit()
        self.db.refresh(memory)
        return memory

    def supersede_old_memory(self, user_id: int, memory_type: str, new_content: str) -> Optional[MemoryItem]:
        """When a new memory conflicts with an old one, mark old as superseded."""
        old_memory = self.db.query(MemoryItem).filter(
            MemoryItem.user_id == user_id,
            MemoryItem.memory_type == memory_type,
            MemoryItem.status == "active"
        ).first()

        if old_memory:
            old_memory.status = "superseded"
            self.db.commit()

        # Create new memory
        new_memory = self.create_memory(
            user_id=user_id,
            memory_type=memory_type,
            content=new_content,
            importance_score=old_memory.importance_score if old_memory else 5,
            source="auto_extracted"
        )

        return new_memory

    def update_last_used(self, memory_id: int) -> None:
        """Update the last_used_at timestamp when memory is recalled."""
        memory = self.db.query(MemoryItem).filter(MemoryItem.id == memory_id).first()
        if memory:
            memory.last_used_at = datetime.now()
            self.db.commit()

    def _memory_to_dict(self, memory: MemoryItem) -> Dict[str, Any]:
        return {
            "id": memory.id,
            "memory_type": memory.memory_type,
            "content": memory.content,
            "importance_score": memory.importance_score,
            "confidence_score": float(memory.confidence_score) if memory.confidence_score else 0.8,
            "source": memory.source,
            "source_message_id": memory.source_message_id,
            "status": memory.status,
            "last_used_at": memory.last_used_at.isoformat() if memory.last_used_at else None,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
        }

    def _generate_memory_confirm_text(self, memory_type: str, content: str, is_high_importance: bool) -> str:
        """Generate confirmation text for memory confirmation card."""
        type_names = {
            "allergy_intolerance": "过敏/不耐受",
            "diet_preference": "饮食偏好",
            "food_dislike": "不喜欢食物",
            "goal": "长期目标",
            "budget": "预算偏好",
            "location": "常用位置",
            "scenario": "饮食场景",
            "sleep": "睡眠相关",
            "body_response": "身体反应",
            "restriction": "现实限制",
            "habit": "饮食习惯",
            "other": "其他",
        }

        type_name = type_names.get(memory_type, memory_type)

        if is_high_importance:
            return f"我可以记住：你{content}。以后推荐饮食时会参考这条信息。是否确认？"
        else:
            return f"记住：{content}"