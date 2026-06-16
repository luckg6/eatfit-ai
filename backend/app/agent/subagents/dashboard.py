"""
Dashboard-query sub-agent.

Owns the dashboard_query intent: summarize today's meals vs profile goal.
Pure data aggregation — no LLM call. The snapshot is returned for the
frontend trace panel.

Imports from:
  - app.prompts.agent_prompts: DASHBOARD_GOAL_MAP
  - app.agent.subagents._shared: add_step
  - app.agent.agent_types: AgentContext, AgentResponse
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.agent.agent_types import AgentContext, AgentResponse
from app.agent.subagents._shared import add_step

logger = logging.getLogger("eatfit.agent.subagents.dashboard")


# ---------------------------------------------------------------------------
# Response formatter
# ---------------------------------------------------------------------------

def generate_dashboard_response(summary: Dict[str, Any], profile: Dict, meals: list) -> str:
    from app.prompts.agent_prompts import DASHBOARD_GOAL_MAP
    parts = [
        f"今日摄入: {summary['total_calories']:.0f}千卡",
        f"蛋白质: {summary['total_protein']:.0f}g, 碳水: {summary['total_carbs']:.0f}g, 脂肪: {summary['total_fat']:.0f}g",
        f"共 {summary['meal_count']} 餐",
    ]
    if summary.get("meals"):
        parts.append("\n已记录:")
        for m in summary["meals"]:
            parts.append(f"- {m['meal_type']}: {m['food_text']} (~{m.get('estimated_calories', 0):.0f}千卡)")
    if profile and profile.get("primary_goal"):
        goal_name = DASHBOARD_GOAL_MAP.get(profile["primary_goal"], profile["primary_goal"])
        parts.append(f"\n当前目标: {goal_name}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Sub-agent entry
# ---------------------------------------------------------------------------

async def run(context: AgentContext, agent) -> AgentResponse:
    """Sub-agent entry: aggregate today's meals → return summary snapshot."""
    summary = agent.meal_tools.get_daily_summary(context.user_id)
    profile = context.profile or agent.profile_tools.get_user_profile(
        agent.user.id if agent.user else context.user_id
    )
    return AgentResponse(
        text=generate_dashboard_response(summary, profile, context.today_meals),
        steps=context.steps,
        context_snapshot={
            "today_summary": summary,
            "profile": profile,
            "memories": context.memories,
        },
    )
