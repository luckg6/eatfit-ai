"""
Enhanced meal tools for the EatFit Agent.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.models.meal_log import MealLog


class MealTools:
    """Tools for managing meal logs in the agent system."""

    def __init__(self, db: Session):
        self.db = db

    def get_today_meals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all meals for today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        meals = self.db.query(MealLog).filter(
            MealLog.user_id == user_id,
            MealLog.meal_time >= today_start
        ).order_by(MealLog.meal_time.asc()).all()

        return [self._meal_to_dict(m) for m in meals]

    def get_recent_meals(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent meals."""
        meals = self.db.query(MealLog).filter(
            MealLog.user_id == user_id
        ).order_by(MealLog.meal_time.desc()).limit(limit).all()

        return [self._meal_to_dict(m) for m in meals]

    def parse_meal_from_text(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse meal information from user text using pattern matching.
        Returns parsed meal data with estimates.
        """
        # Extract clean food description (remove conversational context)
        food_text = self._extract_food_text(text)
        meal_type = self._infer_meal_type(text)
        # Infer meal_time from meal_type
        meal_time = self._infer_meal_time(meal_type)

        result = {
            "food_text": food_text,
            "meal_type": meal_type,
            "scenario": self._infer_scenario(text),
            "meal_time": meal_time,
        }
        return result

    def _extract_food_text(self, text: str) -> str:
        """Extract clean food description from user message."""
        import re
        # Remove common conversational patterns
        patterns_to_remove = [
            r'^我今天[早晚中午晚]?[上中下]?[餐饭]?[上]?吃了',
            r'^我吃了',
            r'^今天[早晚中午晚]?[上中下]?[餐饭]?吃了',
            r'^[早晚中午晚]?[上中下]?[餐饭]?吃了',
            r'^刚刚吃了',
            r'^吃了',
            r'^我刚吃了',
            r'^我.*?吃了',
        ]
        cleaned = text.strip()
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned)
        # Remove trailing particles
        cleaned = re.sub(r'^[的得]$', '', cleaned).strip()
        # If cleaned is empty, fallback to original
        return cleaned if cleaned else text.strip()

    def _infer_meal_time(self, meal_type: str) -> datetime:
        """Infer meal_time from meal_type based on current date."""
        now = datetime.now()
        if meal_type == "BREAKFAST":
            return now.replace(hour=8, minute=0, second=0, microsecond=0)
        elif meal_type == "LUNCH":
            return now.replace(hour=12, minute=0, second=0, microsecond=0)
        elif meal_type == "DINNER":
            return now.replace(hour=18, minute=0, second=0, microsecond=0)
        elif meal_type == "SNACK":
            return now.replace(hour=22, minute=0, second=0, microsecond=0)
        return now

    def create_pending_meal_action(self, user_id: int, parsed_meal: Dict[str, Any],
                                   estimated_calories: float = 0,
                                   estimated_protein: float = 0,
                                   estimated_carbs: float = 0,
                                   estimated_fat: float = 0,
                                   calorie_confidence: float = 0.7,
                                   source_message_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a pending meal action data structure for confirmation card."""
        # Convert meal_time to ISO string for JSON serialization
        meal_time = parsed_meal.get("meal_time")
        if isinstance(meal_time, datetime):
            meal_time = meal_time.isoformat()

        return {
            "action_type": "meal_log",
            "action_status": "pending",
            "action_data": {
                "food_text": parsed_meal.get("food_text"),
                "meal_type": parsed_meal.get("meal_type", "SNACK"),
                "scenario": parsed_meal.get("scenario"),
                "meal_time": meal_time,  # ISO string for JSON serialization
                "estimated_calories": estimated_calories,
                "estimated_protein": estimated_protein,
                "estimated_carbs": estimated_carbs,
                "estimated_fat": estimated_fat,
                "calorie_confidence": calorie_confidence,
                "nutrition_source": "llm_estimate",
                "source_message_id": source_message_id,
            }
        }

    def create_meal_log(self, user_id: int, meal_data: Dict[str, Any], source_message_id: Optional[int] = None) -> MealLog:
        """Create a new meal log entry from confirmed action."""
        meal_time = meal_data.get("meal_time")
        if isinstance(meal_time, str):
            meal_time = datetime.fromisoformat(meal_time.replace("Z", "+00:00"))
        elif meal_time is None:
            meal_time = datetime.now()

        meal = MealLog(
            user_id=user_id,
            meal_type=meal_data.get("meal_type", "SNACK"),
            meal_time=meal_time,
            food_text=meal_data.get("food_text"),
            scenario=meal_data.get("scenario"),
            estimated_calories=meal_data.get("estimated_calories"),
            estimated_protein=meal_data.get("estimated_protein"),
            estimated_carbs=meal_data.get("estimated_carbs"),
            estimated_fat=meal_data.get("estimated_fat"),
            calorie_confidence=meal_data.get("calorie_confidence", 0.7),
            nutrition_source=meal_data.get("nutrition_source", "llm_estimate"),
            source_message_id=source_message_id or meal_data.get("source_message_id"),
            health_score=meal_data.get("health_score"),
            sleep_impact=meal_data.get("sleep_impact", "UNKNOWN"),
            ai_comment=meal_data.get("ai_comment")
        )
        self.db.add(meal)
        self.db.commit()
        self.db.refresh(meal)
        return meal

    def get_daily_summary(self, user_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Get daily nutrition summary."""
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

    def get_meals_by_scope(self, user_id: int, scope: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get meals by time scope.
        scope: 'today' | 'recent' | 'this_week'
        - today: today 00:00 → now
        - recent: last 7 days
        - this_week: current week (Monday → now)
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if scope == "today":
            start = today_start
            end = now
        elif scope == "recent":
            start = today_start - timedelta(days=7)
            end = now
        elif scope == "this_week":
            # Get Monday of current week
            days_since_monday = now.weekday()
            start = (today_start - timedelta(days=days_since_monday))
            end = now
        else:
            start = today_start
            end = now

        meals = self.db.query(MealLog).filter(
            MealLog.user_id == user_id,
            MealLog.meal_time >= start,
            MealLog.meal_time <= end
        ).order_by(MealLog.meal_time.desc()).limit(limit).all()

        total_cal = sum(float(m.estimated_calories or 0) for m in meals)
        total_protein = sum(float(m.estimated_protein or 0) for m in meals)
        total_carbs = sum(float(m.estimated_carbs or 0) for m in meals)
        total_fat = sum(float(m.estimated_fat or 0) for m in meals)

        return {
            "scope": scope,
            "start_date": start.date().isoformat() if hasattr(start, 'date') else start.isoformat(),
            "end_date": end.date().isoformat() if hasattr(end, 'date') else end.isoformat(),
            "total_calories": round(total_cal, 1),
            "total_protein": round(total_protein, 1),
            "total_carbs": round(total_carbs, 1),
            "total_fat": round(total_fat, 1),
            "meal_count": len(meals),
            "meals": [self._meal_to_dict(m) for m in meals]
        }

    def update_meal_log(self, meal_id: int, user_id: int, updates: Dict[str, Any]) -> Optional[MealLog]:
        """Update an existing meal log."""
        meal = self.db.query(MealLog).filter(
            MealLog.id == meal_id,
            MealLog.user_id == user_id
        ).first()

        if not meal:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(meal, key):
                setattr(meal, key, value)

        self.db.commit()
        self.db.refresh(meal)
        return meal

    def delete_meal_log(self, meal_id: int, user_id: int) -> bool:
        """Delete a meal log."""
        meal = self.db.query(MealLog).filter(
            MealLog.id == meal_id,
            MealLog.user_id == user_id
        ).first()

        if not meal:
            return False

        self.db.delete(meal)
        self.db.commit()
        return True

    def _infer_meal_type(self, text: str) -> str:
        """Infer meal type from text."""
        text_lower = text.lower()
        if any(k in text_lower for k in ["早饭", "早餐", "早", "Morning"]):
            return "BREAKFAST"
        elif any(k in text_lower for k in ["午饭", "午餐", "中午", "Lunch", " midday"]):
            return "LUNCH"
        elif any(k in text_lower for k in ["晚饭", "晚餐", "晚上", "Dinner"]):
            return "DINNER"
        elif any(k in text_lower for k in ["宵夜", "夜宵", "snack", "夜"]):
            return "SNACK"
        return "SNACK"  # Default

    def _infer_scenario(self, text: str) -> str:
        """Infer eating scenario from text."""
        text_lower = text.lower()
        if any(k in text_lower for k in ["食堂", "school canteen"]):
            return "SCHOOL_CANTERIA"
        elif any(k in text_lower for k in ["外卖", "delivery", "deliveroo"]):
            return "TAKEOUT"
        elif any(k in text_lower for k in ["餐厅", "饭馆", "餐馆", "restaurant"]):
            return "RESTAURANT"
        elif any(k in text_lower for k in ["便利店", "convenience", "711", "全家"]):
            return "CONVENIENCE"
        elif any(k in text_lower for k in ["快餐", "kfc", "mc", "burger"]):
            return "FAST_FOOD"
        return "OTHER"

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
            "calorie_confidence": float(meal.calorie_confidence) if meal.calorie_confidence else 0.7,
            "nutrition_source": meal.nutrition_source or "llm_estimate",
            "source_message_id": meal.source_message_id,
            "health_score": meal.health_score,
            "sleep_impact": meal.sleep_impact,
            "ai_comment": meal.ai_comment,
            "created_at": meal.created_at.isoformat(),
        }