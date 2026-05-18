from typing import Dict, Any, List, Optional


class DailyPlanPromptBuilder:
    """Build prompts for daily meal plan generation."""

    @staticmethod
    def build(
        profile: Dict[str, Any],
        memories: List[Dict[str, Any]],
        today_meals: List[Dict[str, Any]],
        is_training_day: bool
    ) -> tuple[str, str]:
        """Build system and user prompts for daily plan generation."""

        system_prompt = """You are EatFit AI, a friendly diet advisor. Generate a daily meal plan for the user.

Return JSON with this exact structure:
{
  "breakfast_suggestion": "string - specific breakfast recommendation with approximate nutrition",
  "lunch_suggestion": "string - specific lunch recommendation with approximate nutrition",
  "dinner_suggestion": "string - specific dinner recommendation with approximate nutrition",
  "snack_suggestion": "string - snack recommendation if needed",
  "protein_focus": "string - protein intake focus for the day",
  "avoid_today": ["array of foods to avoid today"],
  "sleep_reminder": "string - sleep-friendly reminder if user is sleep sensitive, empty string otherwise",
  "one_day_strategy": "string - one sentence strategy for the day"
}

Be specific, practical, and aligned with the user's goal.
Consider if it's a training day and adjust recommendations accordingly."""

        profile_info = f"""User Profile:
- Goal: {profile.get('primary_goal', 'GENERAL_HEALTH')}
- Weight: {profile.get('weight_kg', 'unknown')} kg
- Activity Level: {profile.get('activity_level', 'unknown')}
- Training Frequency: {profile.get('training_frequency', 0)} times/week
- Sleep Sensitive: {'Yes' if profile.get('sleep_sensitive') else 'No'}
- Food Preferences: {profile.get('food_preferences', 'not specified')}
- Food Dislikes: {profile.get('food_dislikes', 'not specified')}
- Budget: {profile.get('budget_per_meal', 'not specified')} per meal
- Common Scenarios: {profile.get('common_eating_scenarios', 'not specified')}
"""

        memories_info = ""
        if memories:
            memories_info = "\nUser Memories (try to incorporate):\n"
            for m in memories[:3]:
                memories_info += f"- [{m['memory_type']}] {m['content']}\n"

        today_meals_info = ""
        if today_meals:
            today_meals_info = "\nToday's Already Eaten:\n"
            for meal in today_meals:
                today_meals_info += f"- {meal['meal_type']}: {meal['food_text']} (~{meal.get('estimated_calories', '?')} cal)\n"

        user_prompt = f"""{profile_info}
{memories_info}
{today_meals_info}
Is Training Day: {'Yes' if is_training_day else 'No'}

Generate today's meal plan."""

        return system_prompt, user_prompt