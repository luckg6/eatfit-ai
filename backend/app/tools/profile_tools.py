"""
Profile tools for the EatFit Agent.
"""

from typing import Dict, Any, Optional
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
