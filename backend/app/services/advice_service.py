"""
Diet advice generation service.
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.meal_log import MealLog
from app.models.memory import MemoryItem
from app.models.records import TrainingRecord
from app.prompts.diet_advice import DietAdvicePromptBuilder
from app.services.llm_service import get_llm_service

logger = logging.getLogger("eatfit.advice")


class AdviceService:
    """Service for generating diet advice."""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    def _get_profile(self) -> Dict[str, Any]:
        """Get user food profile."""
        from app.models.food_profile import UserFoodProfile
        profile = self.db.query(UserFoodProfile).filter(
            UserFoodProfile.user_id == self.user.id
        ).first()
        if not profile:
            return {}
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
            "notes": profile.notes
        }

    def _get_memories(self, memory_types: Optional[list] = None) -> list:
        """Get user memories."""
        query = self.db.query(MemoryItem).filter(MemoryItem.user_id == self.user.id)
        if memory_types:
            query = query.filter(MemoryItem.memory_type.in_(memory_types))
        return [
            {
                "id": m.id,
                "memory_type": m.memory_type,
                "content": m.content,
                "importance_score": m.importance_score,
                "source": m.source,
                "created_at": m.created_at.isoformat()
            }
            for m in query.order_by(MemoryItem.importance_score.desc()).limit(10).all()
        ]

    def _get_today_meals(self) -> list:
        """Get today's meals."""
        from datetime import datetime
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        meals = self.db.query(MealLog).filter(
            MealLog.user_id == self.user.id,
            MealLog.meal_time >= today_start
        ).all()
        return [
            {
                "id": m.id,
                "meal_type": m.meal_type,
                "meal_time": m.meal_time.isoformat(),
                "food_text": m.food_text,
                "scenario": m.scenario,
                "estimated_calories": float(m.estimated_calories) if m.estimated_calories else 0,
                "estimated_protein": float(m.estimated_protein) if m.estimated_protein else 0,
                "estimated_carbs": float(m.estimated_carbs) if m.estimated_carbs else 0,
                "estimated_fat": float(m.estimated_fat) if m.estimated_fat else 0,
                "health_score": m.health_score,
                "sleep_impact": m.sleep_impact,
                "ai_comment": m.ai_comment
            }
            for m in meals
        ]

    def _get_recent_trainings(self, limit: int = 5) -> list:
        """Get recent training records."""
        trainings = self.db.query(TrainingRecord).filter(
            TrainingRecord.user_id == self.user.id
        ).order_by(TrainingRecord.record_date.desc()).limit(limit).all()
        return [
            {
                "id": t.id,
                "training_type": t.training_type,
                "duration_minutes": t.duration_minutes,
                "intensity": t.intensity,
                "record_date": t.record_date.isoformat() if t.record_date else None
            }
            for t in trainings
        ]

    async def generate_diet_advice(self, question: str, context: Optional[str],
                                    is_training_day: bool, scenario: str) -> Dict[str, Any]:
        """Generate diet advice for a user question."""
        profile = self._get_profile()
        memories = self._get_memories()
        today_meals = self._get_today_meals()
        recent_trainings = self._get_recent_trainings()

        system_prompt, user_prompt = DietAdvicePromptBuilder.build(
            user_question=question,
            context=context,
            profile=profile,
            memories=memories,
            today_meals=today_meals,
            recent_trainings=recent_trainings,
            is_training_day=is_training_day,
            scenario=scenario
        )

        llm = get_llm_service()
        response_text = await llm.generate(system_prompt, user_prompt)

        try:
            if isinstance(response_text, str):
                response_data = json.loads(response_text)
            else:
                response_data = response_text
        except json.JSONDecodeError:
            response_data = {
                "situation_summary": "无法解析AI回复",
                "goal_analysis": "",
                "recommendation_strategy": "请稍后重试",
                "recommended_options": [],
                "not_recommended": [],
                "today_remaining_advice": "",
                "sleep_friendly_tips": "",
                "training_day_tips": "",
                "next_meal_advice": "",
                "risk_level": "MEDIUM",
                "risk_warnings": ["AI回复解析失败，建议稍后重试"],
                "one_sentence_summary": "请稍后重试"
            }

        return response_data