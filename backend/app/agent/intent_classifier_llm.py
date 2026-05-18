"""
Async LLM-based intent classification for ambiguous cases.
Called by the agent loop when rule-based confidence < 0.5.
"""

import json
from typing import Optional, Dict, Any, List

from app.agent.intent_classifier import Intent, IntentResult
from app.services.llm_service import get_llm_service

LLM_INTENT_SYSTEM_PROMPT = """你是一个意图分类助手。根据用户消息判断真实意图。

可能的意图：
- meal_log: 用户在记录吃了什么（如"刚吃了牛肉饭"、"记录午餐"）
- diet_advice: 用户在问饮食建议（如"吃什么好"、"推荐什么"）
- profile_update: 用户明确想更新资料（如"体重是70kg"、"我目标增肌"、"更新身高175"、"长了5斤帮我更新"）
- memory_candidate: 用户提到值得记住的信息，但不一定是要更新资料（如"我不喜欢吃香菜"、"长了5斤"、"最近睡眠不好"）
- dashboard_query: 用户在查今日摄入或进度（如"今天吃了多少热量"）
- general_chat: 闲聊或无法归类

重要规则：
1. 明确说"更新"/"帮我改"/"改成"/"记录"体重/身高 → profile_update
2. "长了X斤"/"重了X斤"/"胖了X斤" 有明确更新意图 → profile_update（不是memory_candidate）
3. 只有随口说说、没有明确意图（如"我好像胖了"） → memory_candidate
4. 体重单位：如果用户说"斤"，需要转换为kg（1斤=0.5kg）

返回JSON格式：
{"intent": "意图名", "confidence": 0.0-1.0, "reasoning": "判断理由", "requires_confirmation": true/false}"""


async def classify_with_llm(
    text: str,
    profile_context: Optional[Dict[str, Any]] = None,
    recent_messages: Optional[List[Dict[str, Any]]] = None
) -> IntentResult:
    """
    Async LLM-based intent classification for ambiguous cases.
    Called by the agent loop when rule-based classify() returns low confidence.
    """
    llm = get_llm_service()
    user_prompt = _build_user_prompt(text, profile_context, recent_messages)

    try:
        result = await llm.generate(LLM_INTENT_SYSTEM_PROMPT, user_prompt)
        data = json.loads(result)

        intent = _map_string_to_intent(data.get("intent", "general_chat"))

        return IntentResult(
            intent=intent,
            confidence=float(data.get("confidence", 0.5)),
            reasoning=data.get("reasoning", ""),
            metadata={
                "requires_confirmation": data.get("requires_confirmation", False),
                "source": "llm"
            }
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return IntentResult(
            intent=Intent.GENERAL_CHAT,
            confidence=0.3,
            reasoning=f"LLM classification failed: {e}. Defaulting to general_chat."
        )


def _build_user_prompt(
    text: str,
    profile_context: Optional[Dict[str, Any]],
    recent_messages: Optional[List[Dict[str, Any]]]
) -> str:
    """Build the user prompt for LLM intent classification."""
    parts = [f"用户消息: {text}\n"]

    if profile_context:
        parts.append("\n用户上下文:")
        if profile_context.get("primary_goal"):
            parts.append(f"- 目标: {profile_context['primary_goal']}")
        if profile_context.get("weight_kg"):
            parts.append(f"- 当前体重: {profile_context['weight_kg']}kg")
        if profile_context.get("height_cm"):
            parts.append(f"- 身高: {profile_context['height_cm']}cm")
        if profile_context.get("food_preferences"):
            parts.append(f"- 饮食偏好: {profile_context['food_preferences']}")

    if recent_messages:
        parts.append("\n最近对话:")
        for msg in recent_messages[-3:]:
            role = "用户" if msg.get("role") == "user" else "助手"
            content = msg.get("content", "")[:100]
            parts.append(f"- [{role}] {content}")

    return "\n".join(parts)


def _map_string_to_intent(intent_str: str) -> Intent:
    """Map LLM response string to Intent enum."""
    mapping = {
        "meal_log": Intent.MEAL_LOG,
        "diet_advice": Intent.DIET_ADVICE,
        "profile_update": Intent.PROFILE_UPDATE,
        "memory_candidate": Intent.MEMORY_CANDIDATE,
        "dashboard_query": Intent.DASHBOARD_QUERY,
        "general_chat": Intent.GENERAL_CHAT,
        "restaurant_search_planned": Intent.RESTAURANT_SEARCH_PLANNED,
    }
    return mapping.get(intent_str.lower(), Intent.GENERAL_CHAT)