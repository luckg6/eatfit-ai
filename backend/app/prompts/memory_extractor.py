from typing import Dict, Any, List


class MemoryExtractorPromptBuilder:
    """Build prompts for extracting memories from conversations."""

    @staticmethod
    def build(
        profile: Dict[str, Any],
        user_question: str,
        ai_response: Dict[str, Any]
    ) -> tuple[str, str]:
        """Build system and user prompts for memory extraction."""

        system_prompt = """You are a memory extractor for a diet advisor app called EatFit AI.

Your job is to extract 0-3 important long-term memories from conversations.
Only extract memories that are:
1. Useful for long-term diet advice
2. Specific and actionable
3. Not sensitive or private medical details
4. Not general conversational filler

MEMORY TYPES:
- USER_PROFILE: Basic user characteristics
- DIET_PREFERENCE: Food preferences and likes
- FOOD_DISLIKE: Foods they don't like or can't eat
- ROUTINE: Daily habits and training patterns
- SLEEP_TRIGGER: Foods that affect their sleep
- BEHAVIOR_PATTERN: Common eating patterns or behaviors
- PROGRESS: Goals and progress updates
- WARNING: Important health warnings or restrictions
- STRATEGY: Diet strategies that work for them

IMPORTANT:
- Extract AT MOST 3 memories per conversation
- Only extract if information is genuinely useful
- Return empty array if nothing worth remembering
- Do NOT extract: medical diagnoses, body shame content, secrets, or sensitive personal info
- Importance score: 1-10, higher means more important to remember

Return JSON:
{
  "memories": [
    {
      "memoryType": "string - one of the memory types above",
      "content": "string - what to remember, be specific and concise",
      "importanceScore": number 1-10,
      "source": "auto_extracted"
    }
  ]
}"""

        user_prompt = f"""Extract memories from this conversation:

User Profile:
- Goal: {profile.get('primary_goal', 'GENERAL_HEALTH')}
- Food Preferences: {profile.get('food_preferences', 'not specified')}
- Food Dislikes: {profile.get('food_dislikes', 'not specified')}
- Sleep Sensitive: {'Yes' if profile.get('sleep_sensitive') else 'No'}

User Question: {user_question}

AI Response Summary: {ai_response.get('one_sentence_summary', 'N/A')}

Recommendation Strategy: {ai_response.get('recommendation_strategy', 'N/A')}

Extract any useful long-term memories (0-3). Return empty array if nothing worth remembering."""

        return system_prompt, user_prompt