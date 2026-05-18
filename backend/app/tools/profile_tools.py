"""
Enhanced profile tools for the EatFit Agent.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.food_profile import UserFoodProfile


class ProfileTools:
    """Tools for managing user food profiles in the agent system."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user food profile."""
        profile = self.db.query(UserFoodProfile).filter(
            UserFoodProfile.user_id == user_id
        ).first()

        if not profile:
            return None

        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "nickname": profile.nickname,
            "gender": profile.gender,
            "age": profile.age,
            "height_cm": float(profile.height_cm) if profile.height_cm else None,
            "weight_kg": float(profile.weight_kg) if profile.weight_kg else None,
            "body_fat_percent": float(profile.body_fat_percent) if profile.body_fat_percent else None,
            "target_weight_kg": float(profile.target_weight_kg) if profile.target_weight_kg else None,
            "primary_goal": profile.primary_goal or "GENERAL_HEALTH",
            "activity_level": profile.activity_level or "MODERATE",
            "training_frequency": profile.training_frequency or 0,
            "training_type": profile.training_type,
            "food_preferences": profile.food_preferences,
            "food_dislikes": profile.food_dislikes,
            "allergies": profile.allergies,
            "budget_per_meal": float(profile.budget_per_meal) if profile.budget_per_meal else None,
            "common_eating_scenarios": profile.common_eating_scenarios,
            "sleep_sensitive": profile.sleep_sensitive,
            "sleep_notes": profile.sleep_notes,
        }

    def update_profile_fields(self, user_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update profile fields. Does NOT commit - caller decides when to commit."""
        profile = self.db.query(UserFoodProfile).filter(
            UserFoodProfile.user_id == user_id
        ).first()

        if not profile:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)

        self.db.refresh(profile)
        return self.get_user_profile(user_id)

    def create_pending_profile_update(self, user_id: int, field: str, old_value: Any, new_value: Any) -> Dict[str, Any]:
        """Create a pending profile update action data structure."""
        return {
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "display_text": f"检测到你想更新{field}为{new_value}，是否确认？"
        }

    def apply_profile_update(self, user_id: int, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Apply a confirmed profile update."""
        profile = self.db.query(UserFoodProfile).filter(
            UserFoodProfile.user_id == user_id
        ).first()

        if not profile:
            return None

        setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)

        return self.get_user_profile(user_id)

    def get_profile_summary_for_context(self, user_id: int) -> str:
        """Get a brief text summary of profile for context display."""
        profile = self.get_user_profile(user_id)
        if not profile:
            return "未设置饮食画像"

        parts = []
        if profile.get("primary_goal"):
            goal_map = {
                "FAT_LOSS": "减脂",
                "MUSCLE_GAIN": "增肌",
                "MAINTAIN": "维持",
                "SUGAR_CONTROL": "控糖",
                "SLEEP_IMPROVEMENT": "改善睡眠",
                "GENERAL_HEALTH": "一般健康",
            }
            parts.append(f"目标: {goal_map.get(profile['primary_goal'], profile['primary_goal'])}")

        if profile.get("budget_per_meal"):
            parts.append(f"预算: {profile['budget_per_meal']}元/餐")

        if profile.get("weight_kg"):
            parts.append(f"当前体重: {profile['weight_kg']}kg")

        if profile.get("sleep_sensitive"):
            parts.append("睡眠敏感")

        return ", ".join(parts) if parts else "饮食画像已设置"