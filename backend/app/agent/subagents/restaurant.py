"""
Restaurant-search sub-agent.

Owns the restaurant_search_planned intent:
  - "附近有什么餐厅" → search nearby → present selection list (pending action)
  - '餐厅"XXX"(UID:xxx)' → fetch details → LLM analysis vs user goal

Imports from:
  - app.prompts.agent_prompts: GOAL_NAMES, build_restaurant_analysis_prompt
  - app.services.llm_service: get_llm_service
  - app.agent.subagents._shared: add_step
  - app.agent.agent_types: AgentContext, AgentResponse, AgentStep
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict

from app.agent.agent_types import AgentContext, AgentResponse, AgentStep
from app.agent.subagents._shared import add_step

logger = logging.getLogger("eatfit.agent.subagents.restaurant")


# ---------------------------------------------------------------------------
# Detail lookup sub-flow
# ---------------------------------------------------------------------------

async def _run_detail_lookup(
    context: AgentContext,
    agent,
    restaurant_name: str,
    uid: str,
) -> AgentResponse:
    add_step(context, AgentStep.GENERATING_ADVICE, {
        "intent": "restaurant_detail_lookup", "name": restaurant_name, "uid": uid,
    })
    try:
        details = await agent.restaurant_tools.get_restaurant_details(uid)
    except Exception as e:
        logger.error(f"[restaurant] detail lookup failed: {e}", exc_info=True)
        return AgentResponse(text=f"获取餐厅 '{restaurant_name}' 详细信息时出错，请稍后再试。", steps=context.steps)

    if not details:
        return AgentResponse(text=f"未找到餐厅 '{restaurant_name}' 的详细信息。", steps=context.steps)

    profile = context.profile
    goal = profile.get("primary_goal", "UNKNOWN") if profile else "UNKNOWN"
    from app.prompts.agent_prompts import GOAL_NAMES, build_restaurant_analysis_prompt
    goal_name = GOAL_NAMES.get(goal, goal)
    analysis_prompt = build_restaurant_analysis_prompt(
        restaurant_name=details.get("name", restaurant_name),
        address=details.get("address", ""),
        tag=details.get("tag", ""),
        rating=details.get("overall_rating"),
        price_level=details.get("price_level"),
        telephone=details.get("telephone"),
        details=details,
        user_goal=goal,
        goal_name=goal_name,
        profile=profile,
        today_meals=context.today_meals,
    )
    from app.services.llm_service import get_llm_service
    llm = get_llm_service()
    try:
        advice_text = await llm.generate(
            "你是一个外食健康饮食助手，根据餐厅信息和用户目标，给出是否适合用户的分析和建议。",
            analysis_prompt,
        )
    except Exception as e:
        logger.error(f"[restaurant] LLM analysis failed: {e}", exc_info=True)
        return AgentResponse(text=f"分析餐厅 '{restaurant_name}' 时出错，请稍后再试。", steps=context.steps)

    add_step(context, AgentStep.FINAL_RESPONSE, {"restaurant": details.get("name", restaurant_name), "goal": goal})
    return AgentResponse(text=f"**{details.get('name', restaurant_name)}**\n\n{advice_text}", steps=context.steps)


# ---------------------------------------------------------------------------
# Sub-agent entry
# ---------------------------------------------------------------------------

async def run(context: AgentContext, agent) -> AgentResponse:
    """Sub-agent entry: parse detail-lookup regex OR run nearby search."""
    message = context.message

    # Detail lookup: '餐厅"XXX"(UID:xxx)'
    detail_match = re.search(r'餐厅["""](.+?)["""][\s（(]*UID:([a-zA-Z0-9]+)', message)
    if detail_match:
        return await _run_detail_lookup(context, agent, detail_match.group(1), detail_match.group(2))

    add_step(context, AgentStep.GENERATING_ADVICE, {"intent": "restaurant_search_planned"})

    if not agent.latitude or not agent.longitude:
        return AgentResponse(
            text="无法获取你的位置信息，请在手机设置中开启定位权限后再试。",
            steps=context.steps,
        )

    location = f"{agent.latitude},{agent.longitude}"
    region = "成都"
    try:
        restaurants = await agent.restaurant_tools.search_nearby_restaurants(
            user_id=context.user_id, query="美食", location=location, region=region, radius=3000, limit=5,
        )
    except Exception as e:
        logger.error(f"[restaurant] search failed: {e}", exc_info=True)
        return AgentResponse(text="搜索附近餐厅时出错，请稍后再试。", steps=context.steps)

    if not restaurants:
        return AgentResponse(text="附近没有找到餐厅，可能当前位置比较偏或者网络问题。", steps=context.steps)

    restaurant_names = [r.get("name", "未知") for r in restaurants]
    action_data = {
        "action_type": "restaurant_select",
        "action_status": "pending",
        "action_data": {
            "restaurants": restaurants,
            "search_params": {"location": location, "region": region, "radius": 3000},
        },
    }
    add_step(context, AgentStep.CREATING_PENDING_ACTION, {
        "action_type": "restaurant_search",
        "restaurant_count": len(restaurants),
        "restaurants": restaurant_names,
    })
    response_text = (
        f"找到 {len(restaurants)} 家附近餐厅，请选择你想了解的餐厅，我帮你分析适合你的菜品：\n"
        + "\n".join([f"{i+1}. {name}" for i, name in enumerate(restaurant_names)])
    )
    return AgentResponse(text=response_text, action=action_data, steps=context.steps)
