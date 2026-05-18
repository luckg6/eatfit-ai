from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.models.meal_log import MealLog


class MealLogTool:
    """MCP-ready meal log tool."""

    def __init__(self, db: Session):
        self.db = db

    def create_meal_log(self, user_id: int, meal_data: Dict[str, Any]) -> MealLog:
        """Create a new meal log entry."""
        meal = MealLog(
            user_id=user_id,
            meal_type=meal_data.get("meal_type"),
            meal_time=meal_data.get("meal_time"),
            food_text=meal_data.get("food_text"),
            scenario=meal_data.get("scenario"),
            estimated_calories=meal_data.get("estimated_calories"),
            estimated_protein=meal_data.get("estimated_protein"),
            estimated_carbs=meal_data.get("estimated_carbs"),
            estimated_fat=meal_data.get("estimated_fat"),
            health_score=meal_data.get("health_score"),
            sleep_impact=meal_data.get("sleep_impact", "UNKNOWN"),
            ai_comment=meal_data.get("ai_comment")
        )
        self.db.add(meal)
        self.db.commit()
        self.db.refresh(meal)
        return meal

    def list_today_meals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all meals for today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        meals = self.db.query(MealLog).filter(
            MealLog.user_id == user_id,
            MealLog.meal_time >= today_start
        ).order_by(MealLog.meal_time.asc()).all()

        return [self._meal_to_dict(m) for m in meals]

    def list_recent_meals(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent meals."""
        meals = self.db.query(MealLog).filter(
            MealLog.user_id == user_id
        ).order_by(MealLog.meal_time.desc()).limit(limit).all()

        return [self._meal_to_dict(m) for m in meals]

    def summarize_daily_intake(self, user_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Summarize daily nutrition intake."""
        if target_date is None:
            target_date = datetime.now().date()

        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        meals = self.db.query(MealLog).filter(
            MealLog.user_id == user_id,
            MealLog.meal_time >= start,
            MealLog.meal_time <= end
        ).all()

        total_cal = sum(float(m.estimated_calories or 0) for m in meals)
        total_protein = sum(float(m.estimated_protein or 0) for m in meals)
        total_carbs = sum(float(m.estimated_carbs or 0) for m in meals)
        total_fat = sum(float(m.estimated_fat or 0) for m in meals)

        return {
            "date": target_date.isoformat(),
            "total_calories": round(total_cal, 1),
            "total_protein": round(total_protein, 1),
            "total_carbs": round(total_carbs, 1),
            "total_fat": round(total_fat, 1),
            "meal_count": len(meals),
            "meals": [self._meal_to_dict(m) for m in meals]
        }

    def summarize_weekly_intake(self, user_id: int) -> Dict[str, Any]:
        """Summarize weekly nutrition intake."""
        today = datetime.now().date()
        week_start = today - timedelta(days=6)

        daily_summaries = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            daily_summaries.append(self.summarize_daily_intake(user_id, day))

        total_cal = sum(d["total_calories"] for d in daily_summaries)
        total_protein = sum(d["total_protein"] for d in daily_summaries)
        total_carbs = sum(d["total_carbs"] for d in daily_summaries)
        total_fat = sum(d["total_fat"] for d in daily_summaries)
        total_meals = sum(d["meal_count"] for d in daily_summaries)

        return {
            "start_date": week_start.isoformat(),
            "end_date": today.isoformat(),
            "total_calories": round(total_cal, 1),
            "total_protein": round(total_protein, 1),
            "total_carbs": round(total_carbs, 1),
            "total_fat": round(total_fat, 1),
            "total_meals": total_meals,
            "daily_breakdown": daily_summaries
        }

    def _meal_to_dict(self, meal: MealLog) -> Dict[str, Any]:
        return {
            "id": meal.id,
            "meal_type": meal.meal_type,
            "meal_time": meal.meal_time.isoformat() if meal.meal_time else None,
            "food_text": meal.food_text,
            "scenario": meal.scenario,
            "estimated_calories": float(meal.estimated_calories) if meal.estimated_calories else 0,
            "estimated_protein": float(meal.estimated_protein) if meal.estimated_protein else 0,
            "estimated_carbs": float(meal.estimated_carbs) if meal.estimated_carbs else 0,
            "estimated_fat": float(meal.estimated_fat) if meal.estimated_fat else 0,
            "health_score": meal.health_score,
            "sleep_impact": meal.sleep_impact,
            "ai_comment": meal.ai_comment
        }