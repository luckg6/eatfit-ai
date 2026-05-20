from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.meal_log import MealLog
from app.schemas.meal import MealLogResponse, MealLogCreate, MealLogUpdate, MealSummary

router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.post("", response_model=MealLogResponse)
def create_meal(
    meal_data: MealLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Handle meal_time - default to now if not provided
    meal_time = meal_data.meal_time
    if meal_time is None:
        meal_time = datetime.now()

    meal = MealLog(
        user_id=current_user.id,
        meal_type=meal_data.meal_type,
        meal_time=meal_time,
        food_text=meal_data.food_text,
        scenario=meal_data.scenario,
        estimated_calories=meal_data.estimated_calories,
        estimated_protein=meal_data.estimated_protein,
        estimated_carbs=meal_data.estimated_carbs,
        estimated_fat=meal_data.estimated_fat,
        health_score=meal_data.health_score,
        sleep_impact=meal_data.sleep_impact,
        ai_comment=meal_data.ai_comment
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


@router.get("/today", response_model=List[MealLogResponse])
def list_today_meals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return db.query(MealLog).filter(
        MealLog.user_id == current_user.id,
        MealLog.meal_time >= today_start
    ).order_by(MealLog.meal_time.asc()).all()


@router.get("/recent", response_model=List[MealLogResponse])
def list_recent_meals(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(MealLog).filter(
        MealLog.user_id == current_user.id
    ).order_by(MealLog.meal_time.desc()).limit(limit).all()


@router.get("/{meal_id}", response_model=MealLogResponse)
def get_meal(meal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meal = db.query(MealLog).filter(
        MealLog.id == meal_id,
        MealLog.user_id == current_user.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal


@router.put("/{meal_id}", response_model=MealLogResponse)
def update_meal(
    meal_id: int,
    meal_data: MealLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meal = db.query(MealLog).filter(
        MealLog.id == meal_id,
        MealLog.user_id == current_user.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    update_data = meal_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(meal, key, value)

    db.commit()
    db.refresh(meal)
    return meal


@router.delete("/{meal_id}")
def delete_meal(meal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meal = db.query(MealLog).filter(
        MealLog.id == meal_id,
        MealLog.user_id == current_user.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    db.delete(meal)
    db.commit()
    return {"message": "Meal deleted"}


@router.get("/summary/daily", response_model=MealSummary)
def get_daily_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    meals = db.query(MealLog).filter(
        MealLog.user_id == current_user.id,
        MealLog.meal_time >= today_start
    ).all()

    total_calories = sum(float(m.estimated_calories or 0) for m in meals)
    total_protein = sum(float(m.estimated_protein or 0) for m in meals)
    total_carbs = sum(float(m.estimated_carbs or 0) for m in meals)
    total_fat = sum(float(m.estimated_fat or 0) for m in meals)

    return MealSummary(
        date=today_start.strftime("%Y-%m-%d"),
        total_calories=total_calories,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        meals=meals
    )


@router.get("/summary/weekly")
def get_weekly_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    week_start = datetime.now() - timedelta(days=7)
    meals = db.query(MealLog).filter(
        MealLog.user_id == current_user.id,
        MealLog.meal_time >= week_start
    ).all()

    daily_data = {}
    for meal in meals:
        date_key = meal.meal_time.strftime("%Y-%m-%d")
        if date_key not in daily_data:
            daily_data[date_key] = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "meals": []}
        daily_data[date_key]["calories"] += float(meal.estimated_calories or 0)
        daily_data[date_key]["protein"] += float(meal.estimated_protein or 0)
        daily_data[date_key]["carbs"] += float(meal.estimated_carbs or 0)
        daily_data[date_key]["fat"] += float(meal.estimated_fat or 0)
        daily_data[date_key]["meals"].append(meal)

    return {"days": daily_data, "total_meals": len(meals)}