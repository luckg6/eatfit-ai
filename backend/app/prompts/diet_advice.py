from typing import Dict, Any, List, Optional


class DietAdvicePromptBuilder:
    """Build prompts for diet advice generation."""

    @staticmethod
    def build(
        user_question: str,
        context: Optional[str],
        profile: Dict[str, Any],
        memories: List[Dict[str, Any]],
        today_meals: List[Dict[str, Any]],
        recent_trainings: List[Dict[str, Any]],
        is_training_day: bool,
        scenario: str
    ) -> tuple[str, str]:
        """Build system and user prompts for diet advice."""

        system_prompt = """You are EatFit AI, a friendly and professional diet advisor for people who eat out frequently.

IMPORTANT RULES:
1. DO NOT provide medical diagnoses - you are a diet advisor, not a doctor
2. DO NOT suggest extreme diets, fasting, or unhealthy weight loss methods
3. DO NOT use fear-based messaging about weight or body image
4. DO NOT promise quick weight loss results
5. DO give specific, actionable advice (e.g., "order rice half portion", "add vegetables")
6. DO emphasize long-term habits over short-term results
7. DO consider the user's goal, training schedule, and sleep sensitivity
8. ALL nutrition estimates are rough approximations - always say so

RESPONSE FORMAT:
You MUST return a valid JSON object with this exact structure:
{
  "situation_summary": "string describing the user's current situation",
  "goal_analysis": "string analyzing how this meal fits their goals",
  "recommendation_strategy": "string with overall strategy",
  "recommended_options": [
    {
      "name": "string - dish name",
      "why_recommended": "string - why this is good",
      "estimated_calories": number,
      "estimated_protein": number,
      "estimated_carbs": number,
      "estimated_fat": number,
      "order_modification": "string - specific modification suggestions",
      "suitable_for": ["array of strings"],
      "score": number 1-10
    }
  ],
  "not_recommended": [
    {
      "name": "string - dish name",
      "reason": "string - why not recommended",
      "better_alternative": "string - what to choose instead"
    }
  ],
  "today_remaining_advice": "string - advice for remaining meals today",
  "sleep_friendly_tips": "string - tips for sleep-friendly eating (empty if not relevant)",
  "training_day_tips": "string - tips for training days (empty if not training today)",
  "next_meal_advice": "string - advice for the next meal",
  "risk_level": "LOW|MEDIUM|HIGH",
  "risk_warnings": ["array of warning strings"],
  "one_sentence_summary": "string - one sentence summary"
}

Be specific, warm, and helpful. Think like a knowledgeable friend who understands nutrition."""

        profile_info = f"""User Profile:
- Goal: {profile.get('primary_goal', 'GENERAL_HEALTH')}
- Weight: {profile.get('weight_kg', 'unknown')} kg
- Height: {profile.get('height_cm', 'unknown')} cm
- Activity Level: {profile.get('activity_level', 'unknown')}
- Training Frequency: {profile.get('training_frequency', 0)} times/week
- Sleep Sensitive: {'Yes' if profile.get('sleep_sensitive') else 'No'}
- Food Preferences: {profile.get('food_preferences', 'not specified')}
- Food Dislikes: {profile.get('food_dislikes', 'not specified')}
- Allergies: {profile.get('allergies', 'none')}
"""

        memories_info = ""
        if memories:
            memories_info = "\nUser Long-term Memories:\n"
            for m in memories[:5]:
                memories_info += f"- [{m['memory_type']}] {m['content']}\n"

        today_meals_info = ""
        if today_meals:
            today_meals_info = "\nToday's Meals:\n"
            for meal in today_meals:
                today_meals_info += f"- {meal['meal_type']}: {meal['food_text']} (~{meal.get('estimated_calories', '?')} cal)\n"

        training_info = ""
        if is_training_day:
            training_info = "\nToday is a TRAINING DAY.\n"
        elif recent_trainings:
            last_training = recent_trainings[0]
            training_info = f"\nLast training: {last_training.get('training_type', 'unknown')} on {last_training.get('record_date', 'unknown')}\n"

        user_prompt = f"""User Question: {user_question}
Context: {context or 'No additional context'}
Scenario: {scenario}
Is Training Day: {'Yes' if is_training_day else 'No'}

{profile_info}
{memories_info}
{today_meals_info}
{training_info}

Please provide diet advice following the required JSON format."""

        return system_prompt, user_prompt