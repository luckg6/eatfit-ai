from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.food_profile import UserFoodProfile


class ProfileTool:
    """MCP-ready profile tool for managing user food profiles."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_food_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
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
            "primary_goal": profile.primary_goal,
            "activity_level": profile.activity_level,
            "training_frequency": profile.training_frequency,
            "training_type": profile.training_type,
            "food_preferences": profile.food_preferences,
            "food_dislikes": profile.food_dislikes,
            "allergies": profile.allergies,
            "budget_per_meal": float(profile.budget_per_meal) if profile.budget_per_meal else None,
            "common_eating_scenarios": profile.common_eating_scenarios,
            "sleep_sensitive": profile.sleep_sensitive,
            "sleep_notes": profile.sleep_notes,
            "notes": profile.notes
        }

    def update_user_food_profile(self, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user food profile."""
        profile = self.db.query(UserFoodProfile).filter(
            UserFoodProfile.user_id == user_id
        ).first()

        if not profile:
            return None

        for key, value in update_data.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)

        self.db.commit()
        self.db.refresh(profile)

        return self.get_user_food_profile(user_id)

    def infer_missing_profile_fields(self, user_id: int) -> Dict[str, Any]:
        """Infer missing profile fields based on available data."""
        profile = self.get_user_food_profile(user_id)
        if not profile:
            return {}

        inferred = {}

        if profile.get("height_cm") and profile.get("weight_kg"):
            height_m = profile["height_cm"] / 100
            bmi = profile["weight_kg"] / (height_m * height_m)
            inferred["bmi"] = round(bmi, 1)

        if profile.get("weight_kg") and profile.get("body_fat_percent"):
            lbm = profile["weight_kg"] * (1 - profile["body_fat_percent"] / 100)
            inferred["lean_body_mass_kg"] = round(lbm, 1)

        if profile.get("primary_goal") and profile.get("weight_kg") and profile.get("target_weight_kg"):
            weight_diff = profile["target_weight_kg"] - profile["weight_kg"]
            inferred["weight_change_needed"] = round(weight_diff, 1)

        return inferred