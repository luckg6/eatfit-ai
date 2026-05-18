from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.food_profile import UserFoodProfile
from app.schemas.profile import UserFoodProfileResponse, UserFoodProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=UserFoodProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserFoodProfile).filter(UserFoodProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("", response_model=UserFoodProfileResponse)
def update_profile(
    profile_data: UserFoodProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserFoodProfile).filter(UserFoodProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserFoodProfile(user_id=current_user.id)
        db.add(profile)

    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/init", response_model=UserFoodProfileResponse)
def init_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(UserFoodProfile).filter(UserFoodProfile.user_id == current_user.id).first()
    if existing:
        return existing

    profile = UserFoodProfile(user_id=current_user.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile