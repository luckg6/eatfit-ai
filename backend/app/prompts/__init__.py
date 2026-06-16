"""
Prompts module for EatFit.

Each submodule owns one prompt family:

  - memory_extractor.py: extract memory candidates from a message
  - daily_plan.py      : build a one-day eating plan
  - weekly_review.py   : build a weekly review
  - agent_prompts.py   : prompts + lookup tables used by the ReAct agent loop
                         (system prompt, user-prompt builder, hint templates,
                         restaurant analysis prompt, LLM helper prompts).
"""
from app.prompts.agent_prompts import (
    DASHBOARD_GOAL_MAP,
    GOAL_NAMES,
    MEAL_TYPE_NAMES,
    PROFILE_FIELD_NAMES,
    build_advice_context,
    build_advice_user_prompt,
    build_memory_extraction_prompt,
    build_nutrition_estimation_prompt,
    build_profile_update_parse_prompt,
    build_restaurant_analysis_prompt,
    get_agent_system_prompt,
)
from app.prompts.daily_plan import DailyPlanPromptBuilder
from app.prompts.memory_extractor import MemoryExtractorPromptBuilder
from app.prompts.weekly_review import WeeklyReviewPromptBuilder

__all__ = [
    # Builder classes
    "MemoryExtractorPromptBuilder",
    "DailyPlanPromptBuilder",
    "WeeklyReviewPromptBuilder",
    # ReAct agent prompt helpers
    "GOAL_NAMES",
    "MEAL_TYPE_NAMES",
    "PROFILE_FIELD_NAMES",
    "DASHBOARD_GOAL_MAP",
    "get_agent_system_prompt",
    "build_advice_context",
    "build_advice_user_prompt",
    "build_memory_extraction_prompt",
    "build_nutrition_estimation_prompt",
    "build_profile_update_parse_prompt",
    "build_restaurant_analysis_prompt",
]
