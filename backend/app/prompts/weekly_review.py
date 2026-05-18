from typing import Dict, Any, List


class WeeklyReviewPromptBuilder:
    """Build prompts for weekly diet review generation."""

    @staticmethod
    def build(
        profile: Dict[str, Any],
        memories: List[Dict[str, Any]],
        weekly_meals: Dict[str, Any],
        recent_trainings: List[Dict[str, Any]],
        recent_weights: List[Dict[str, Any]],
        recent_body_fat: List[Dict[str, Any]]
    ) -> tuple[str, str]:
        """Build system and user prompts for weekly review generation."""

        system_prompt = """You are EatFit AI, a friendly diet advisor. Generate a weekly diet review for the user.

Return JSON with this exact structure:
{
  "week_summary": "string - overall summary of the week",
  "what_went_well": ["array of positive things"],
  "main_problems": ["array of areas to improve"],
  "protein_consistency": "string - protein intake analysis",
  "sleep_impact_analysis": "string - how diet affected sleep this week",
  "eating_out_pattern": "string - analysis of eating out patterns",
  "weight_and_body_fat_trend": "string - weight/body fat trend if data available",
  "next_week_strategy": "string - strategy for next week",
  "next_week_actions": ["array of 3 actionable items for next week"],
  "warnings": ["array of warnings or cautions"]
}

Be encouraging, specific, and focus on progress over perfection."""

        profile_info = f"""User Profile:
- Goal: {profile.get('primary_goal', 'GENERAL_HEALTH')}
- Target Weight: {profile.get('target_weight_kg', 'unknown')} kg
- Current Weight: {profile.get('weight_kg', 'unknown')} kg
- Training Frequency: {profile.get('training_frequency', 0)} times/week
- Sleep Sensitive: {'Yes' if profile.get('sleep_sensitive') else 'No'}
"""

        weekly_info = f"""Weekly Summary:
- Total Meals: {weekly_meals.get('total_meals', 0)}
- Total Calories: {weekly_meals.get('total_calories', 0):.0f} kcal
- Total Protein: {weekly_meals.get('total_protein', 0):.0f}g
- Total Carbs: {weekly_meals.get('total_carbs', 0):.0f}g
- Total Fat: {weekly_meals.get('total_fat', 0):.0f}g
"""

        training_info = ""
        if recent_trainings:
            training_info = "\nRecent Trainings:\n"
            for t in recent_trainings[:5]:
                training_info += f"- {t.get('training_type', 'unknown')} on {t.get('record_date', 'unknown')}\n"

        weight_info = ""
        if recent_weights:
            weight_info = "\nRecent Weights:\n"
            for w in recent_weights[:3]:
                weight_info += f"- {w.get('weight_kg', 'unknown')} kg on {w.get('record_date', 'unknown')}\n"

        body_fat_info = ""
        if recent_body_fat:
            body_fat_info = "\nRecent Body Fat:\n"
            for bf in recent_body_fat[:3]:
                body_fat_info += f"- {bf.get('body_fat_percent', 'unknown')}% on {bf.get('record_date', 'unknown')}\n"

        memories_info = ""
        if memories:
            memories_info = "\nKey Memories:\n"
            for m in memories[:3]:
                memories_info += f"- [{m['memory_type']}] {m['content']}\n"

        user_prompt = f"""{profile_info}
{weekly_info}
{training_info}
{weight_info}
{body_fat_info}
{memories_info}

Generate weekly review."""

        return system_prompt, user_prompt