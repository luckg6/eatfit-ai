import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.advice import AdviceSession, DietAdviceRecord
from app.models.memory import MemoryItem
from app.models.meal_log import MealLog
from app.models.records import TrainingRecord, WeightRecord, BodyFatRecord
from app.services.llm_service import get_llm_service
from app.prompts.diet_advice import DietAdvicePromptBuilder
from app.prompts.memory_extractor import MemoryExtractorPromptBuilder
from app.prompts.daily_plan import DailyPlanPromptBuilder
from app.prompts.weekly_review import WeeklyReviewPromptBuilder


class AdviceService:
    """Service for generating diet advice and managing advice sessions."""

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

    def _get_recent_weights(self, limit: int = 5) -> list:
        """Get recent weight records."""
        weights = self.db.query(WeightRecord).filter(
            WeightRecord.user_id == self.user.id
        ).order_by(WeightRecord.record_date.desc()).limit(limit).all()
        return [
            {
                "id": w.id,
                "weight_kg": float(w.weight_kg),
                "record_date": w.record_date.isoformat() if w.record_date else None,
                "note": w.note
            }
            for w in weights
        ]

    def _get_recent_body_fat(self, limit: int = 5) -> list:
        """Get recent body fat records."""
        records = self.db.query(BodyFatRecord).filter(
            BodyFatRecord.user_id == self.user.id
        ).order_by(BodyFatRecord.record_date.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "body_fat_percent": float(r.body_fat_percent),
                "record_date": r.record_date.isoformat() if r.record_date else None,
                "note": r.note
            }
            for r in records
        ]

    async def generate_advice(
        self,
        question: str,
        context: Optional[str],
        is_training_day: bool,
        scenario: str
    ) -> Dict[str, Any]:
        """Generate diet advice."""
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

        session = AdviceSession(
            user_id=self.user.id,
            title=question[:50],
            user_question=question,
            context_text=context,
            ai_response_json=response_data
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        advice_record = DietAdviceRecord(
            user_id=self.user.id,
            session_id=session.id,
            situation_summary=response_data.get("situation_summary"),
            recommendation_strategy=response_data.get("recommendation_strategy"),
            recommended_options_json=response_data.get("recommended_options"),
            not_recommended_json=response_data.get("not_recommended"),
            estimated_summary_json={
                "calories": sum(opt.get("estimated_calories", 0) for opt in response_data.get("recommended_options", [])),
                "protein": sum(opt.get("estimated_protein", 0) for opt in response_data.get("recommended_options", []))
            },
            next_meal_advice=response_data.get("next_meal_advice"),
            sleep_friendly_tips=response_data.get("sleep_friendly_tips"),
            risk_level=response_data.get("risk_level", "LOW")
        )
        self.db.add(advice_record)
        self.db.commit()

        if self.user.auto_memory_enabled:
            await self._extract_and_save_memories(profile, question, response_data)

        return response_data

    async def _extract_and_save_memories(
        self,
        profile: Dict[str, Any],
        user_question: str,
        ai_response: Dict[str, Any]
    ):
        """Extract and save memories from conversation."""
        system_prompt, user_prompt = MemoryExtractorPromptBuilder.build(
            profile=profile,
            user_question=user_question,
            ai_response=ai_response
        )

        llm = get_llm_service()
        response_text = await llm.generate(system_prompt, user_prompt)

        try:
            memory_data = json.loads(response_text) if isinstance(response_text, str) else response_text
            memories = memory_data.get("memories", [])

            for mem in memories[:3]:
                existing = self.db.query(MemoryItem).filter(
                    MemoryItem.user_id == self.user.id,
                    MemoryItem.memory_type == mem.get("memoryType"),
                    MemoryItem.content == mem.get("content")
                ).first()

                if not existing:
                    memory = MemoryItem(
                        user_id=self.user.id,
                        memory_type=mem.get("memoryType"),
                        content=mem.get("content"),
                        importance_score=mem.get("importanceScore", 5),
                        source=mem.get("source", "auto_extracted")
                    )
                    self.db.add(memory)

            self.db.commit()
        except Exception:
            pass

    async def generate_daily_plan(self, is_training_day: bool) -> Dict[str, Any]:
        """Generate daily meal plan."""
        profile = self._get_profile()
        memories = self._get_memories(memory_types=["DIET_PREFERENCE", "FOOD_DISLIKE", "STRATEGY"])
        today_meals = self._get_today_meals()

        system_prompt, user_prompt = DailyPlanPromptBuilder.build(
            profile=profile,
            memories=memories,
            today_meals=today_meals,
            is_training_day=is_training_day
        )

        llm = get_llm_service()
        response_text = await llm.generate(system_prompt, user_prompt)

        try:
            return json.loads(response_text) if isinstance(response_text, str) else response_text
        except json.JSONDecodeError:
            return {
                "breakfast_suggestion": "请稍后重试",
                "lunch_suggestion": "",
                "dinner_suggestion": "",
                "snack_suggestion": "",
                "protein_focus": "",
                "avoid_today": [],
                "sleep_reminder": "",
                "one_day_strategy": "请稍后重试"
            }

    async def generate_weekly_review(self) -> Dict[str, Any]:
        """Generate weekly diet review."""
        from app.tools.meal_log_tool import MealLogTool

        profile = self._get_profile()
        memories = self._get_memories()
        recent_trainings = self._get_recent_trainings()
        recent_weights = self._get_recent_weights()
        recent_body_fat = self._get_recent_body_fat()

        meal_log_tool = MealLogTool(self.db)
        weekly_meals = meal_log_tool.summarize_weekly_intake(self.user.id)

        system_prompt, user_prompt = WeeklyReviewPromptBuilder.build(
            profile=profile,
            memories=memories,
            weekly_meals=weekly_meals,
            recent_trainings=recent_trainings,
            recent_weights=recent_weights,
            recent_body_fat=recent_body_fat
        )

        llm = get_llm_service()
        response_text = await llm.generate(system_prompt, user_prompt)

        try:
            return json.loads(response_text) if isinstance(response_text, str) else response_text
        except json.JSONDecodeError:
            return {
                "week_summary": "请稍后重试",
                "what_went_well": [],
                "main_problems": [],
                "protein_consistency": "",
                "sleep_impact_analysis": "",
                "eating_out_pattern": "",
                "weight_and_body_fat_trend": "",
                "next_week_strategy": "",
                "next_week_actions": [],
                "warnings": ["AI回复解析失败，建议稍后重试"]
            }