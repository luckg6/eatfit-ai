from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.memory import MemoryItem
from app.schemas.memory import MemoryItemCreate, MemoryItemUpdate


class MemoryTool:
    """MCP-ready memory tool for managing user long-term memories."""

    def __init__(self, db: Session):
        self.db = db

    def search_memories(
        self,
        user_id: int,
        query: Optional[str] = None,
        memory_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search memories for a user."""
        q = self.db.query(MemoryItem).filter(MemoryItem.user_id == user_id)
        if memory_types:
            q = q.filter(MemoryItem.memory_type.in_(memory_types))
        if query:
            q = q.filter(MemoryItem.content.contains(query))
        return [
            {
                "id": m.id,
                "memory_type": m.memory_type,
                "content": m.content,
                "importance_score": m.importance_score,
                "source": m.source,
                "created_at": m.created_at.isoformat()
            }
            for m in q.order_by(MemoryItem.importance_score.desc()).all()
        ]

    def upsert_memory(
        self,
        user_id: int,
        memory_type: str,
        content: str,
        importance_score: int = 5,
        source: str = "manual"
    ) -> MemoryItem:
        """Create or update a memory."""
        memory = MemoryItem(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            importance_score=importance_score,
            source=source
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def delete_memory(self, memory_id: int, user_id: int) -> bool:
        """Delete a specific memory."""
        memory = self.db.query(MemoryItem).filter(
            MemoryItem.id == memory_id,
            MemoryItem.user_id == user_id
        ).first()
        if memory:
            self.db.delete(memory)
            self.db.commit()
            return True
        return False

    def list_memories(self, user_id: int) -> List[Dict[str, Any]]:
        """List all memories for a user."""
        memories = self.db.query(MemoryItem).filter(
            MemoryItem.user_id == user_id
        ).order_by(MemoryItem.importance_score.desc(), MemoryItem.created_at.desc()).all()
        return [
            {
                "id": m.id,
                "memory_type": m.memory_type,
                "content": m.content,
                "importance_score": m.importance_score,
                "source": m.source,
                "created_at": m.created_at.isoformat()
            }
            for m in memories
        ]

    def update_memory(
        self,
        memory_id: int,
        user_id: int,
        memory_type: Optional[str] = None,
        content: Optional[str] = None,
        importance_score: Optional[int] = None
    ) -> Optional[MemoryItem]:
        """Update a memory's content or importance."""
        memory = self.db.query(MemoryItem).filter(
            MemoryItem.id == memory_id,
            MemoryItem.user_id == user_id
        ).first()
        if not memory:
            return None
        if memory_type:
            memory.memory_type = memory_type
        if content:
            memory.content = content
        if importance_score is not None:
            memory.importance_score = importance_score
        self.db.commit()
        self.db.refresh(memory)
        return memory