from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.memory import MemoryItem
from app.schemas.memory import MemoryItemResponse, MemoryItemCreate, MemoryItemUpdate

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("", response_model=List[MemoryItemResponse])
def list_memories(
    memory_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(MemoryItem).filter(MemoryItem.user_id == current_user.id)
    # Default to active memories only
    if status_filter:
        query = query.filter(MemoryItem.status == status_filter)
    else:
        query = query.filter(MemoryItem.status == "active")
    if memory_type:
        query = query.filter(MemoryItem.memory_type == memory_type)
    return query.order_by(MemoryItem.importance_score.desc(), MemoryItem.created_at.desc()).all()


@router.post("", response_model=MemoryItemResponse)
def create_memory(
    memory_data: MemoryItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memory = MemoryItem(
        user_id=current_user.id,
        memory_type=memory_data.memory_type,
        content=memory_data.content,
        importance_score=memory_data.importance_score,
        source=memory_data.source,
        status=memory_data.status,
        confidence_score=memory_data.confidence_score
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


@router.put("/{memory_id}", response_model=MemoryItemResponse)
def update_memory(
    memory_id: int,
    memory_data: MemoryItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memory = db.query(MemoryItem).filter(
        MemoryItem.id == memory_id,
        MemoryItem.user_id == current_user.id
    ).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    update_data = memory_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(memory, key, value)

    db.commit()
    db.refresh(memory)
    return memory


@router.delete("/{memory_id}")
def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memory = db.query(MemoryItem).filter(
        MemoryItem.id == memory_id,
        MemoryItem.user_id == current_user.id
    ).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Soft delete: set status to inactive instead of physical delete
    memory.status = "inactive"
    db.commit()
    return {"message": "Memory disabled"}


@router.delete("")
def delete_all_memories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Soft delete all: set status to inactive
    db.query(MemoryItem).filter(
        MemoryItem.user_id == current_user.id,
        MemoryItem.status == "active"
    ).update({"status": "inactive"})
    db.commit()
    return {"message": "All active memories disabled"}