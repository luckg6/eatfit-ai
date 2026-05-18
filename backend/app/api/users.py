from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/auto-memory")
def update_auto_memory(
    auto_memory_enabled: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.auto_memory_enabled = auto_memory_enabled
    db.commit()
    return {"auto_memory_enabled": auto_memory_enabled}