"""
Meal-log sub-agent.

Owns the meal-log intent: parse food text → estimate nutrition → return
pending action for user confirmation.

Imports from:
  - app.prompts.agent_prompts: NUTRITION_ESTIMATION_SYSTEM, build_nutrition_estimation_prompt, MEAL_TYPE_NAMES
  - app.services.llm_service: get_llm_service
  - app.agent.subagents._shared: add_step
  - app.agent.agent_types: AgentContext, AgentResponse, AgentStep
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.agent.agent_types import AgentContext, AgentResponse, AgentStep
from app.agent.subagents._shared import add_step
from app.prompts.agent_prompts import (
    MEAL_TYPE_NAMES,
    build_nutrition_estimation_prompt,
)

logger = logging.getLogger("eatfit.agent.subagents.meal_log")


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

async def estimate_nutrition(food_text: str, profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Use LLM to estimate nutrition for a meal text."""
    from app.services.llm_service import get_llm_service
    llm = get_llm_service()
    from app.prompts.agent_prompts import NUTRITION_ESTIMATION_SYSTEM
    try:
        result = await llm.generate(NUTRITION_ESTIMATION_SYSTEM, build_nutrition_estimation_prompt(food_text))
        data = json.loads(result)
        return {
            "estimated_calories": data.get("estimated_calories", 0),
            "estimated_protein": data.get("estimated_protein", 0),
            "estimated_carbs": data.get("estimated_carbs", 0),
            "estimated_fat": data.get("estimated_fat", 0),
            "confidence": data.get("confidence", 0.65),
        }
    except Exception:
        return {
            "estimated_calories": 0, "estimated_protein": 0, "estimated_carbs": 0, "estimated_fat": 0,
            "confidence": 0.5,
        }


# ---------------------------------------------------------------------------
# Response formatter
# ---------------------------------------------------------------------------

def generate_meal_log_response(parsed: Dict[str, Any], nutrition: Dict[str, Any]) -> str:
    food = parsed.get("food_text", "")
    meal_type = parsed.get("meal_type", "SNACK")
    calories = nutrition.get("estimated_calories", 0)
    return (
        f"记录: {food}\n"
        f"类型: {MEAL_TYPE_NAMES.get(meal_type, meal_type)}\n"
        f"估算热量: ~{calories:.0f}千卡 (估算值)"
    )


# ---------------------------------------------------------------------------
# Sub-agent entry
# ---------------------------------------------------------------------------

async def run(context: AgentContext, agent) -> AgentResponse:
    """Sub-agent entry: parse meal → estimate nutrition → return pending action."""
    add_step(context, AgentStep.PARSING_MEAL, {"message": context.message})

    parsed = agent.meal_tools.parse_meal_from_text(context.message)
    nutrition = await estimate_nutrition(context.message, context.profile)

    pending_action = agent.meal_tools.create_pending_meal_action(
        user_id=context.user_id,
        parsed_meal=parsed,
        estimated_calories=nutrition.get("estimated_calories", 0),
        estimated_protein=nutrition.get("estimated_protein", 0),
        estimated_carbs=nutrition.get("estimated_carbs", 0),
        estimated_fat=nutrition.get("estimated_fat", 0),
        calorie_confidence=nutrition.get("confidence", 0.65),
    )
    add_step(context, AgentStep.CREATING_PENDING_ACTION, {
        "action_type": "meal_log",
        "food_text": parsed.get("food_text"),
    })

    return AgentResponse(
        text=generate_meal_log_response(parsed, nutrition),
        action=pending_action,
        steps=context.steps,
    )
