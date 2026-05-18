import httpx
import asyncio
import json
import re

async def test():
    headers = {
        'Authorization': 'Bearer sk-cp-aGpjqeb_fgtDD5DegWv3nncuV1I00CAACqBKJATZUM6_EekoLtLywt0O5qLIbpu_kA8FJtXlCU3otMmwzygCGAd6WyAF7tv6aE61Wz6A2ITfOw0Vo6AkYd0',
        'Content-Type': 'application/json'
    }

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

    user_prompt = """User Question: 我想吃牛肉饭
Context: No additional context
Scenario: OTHER
Is Training Day: No

User Profile:
- Goal: GENERAL_HEALTH
- Weight: unknown kg
- Height: unknown cm
- Activity Level: unknown
- Training Frequency: 0 times/week
- Sleep Sensitive: No
- Food Preferences: not specified
- Food Dislikes: not specified
- Allergies: none

Please provide diet advice following the required JSON format."""

    payload = {
        'model': 'MiniMax-M2.7',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'temperature': 0.7
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            'https://api.minimaxi.com/v1/chat/completions',
            headers=headers,
            json=payload
        )
        data = response.json()
        content = data['choices'][0]['message']['content']

        # Clean like the service does
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)

        print('Cleaned content:')
        print(repr(content[:800]))

        try:
            parsed = json.loads(content)
            print('\nJSON parsing succeeded!')
            print('Keys:', list(parsed.keys()))
        except json.JSONDecodeError as e:
            print(f'\nJSON parsing failed: {e}')

asyncio.run(test())