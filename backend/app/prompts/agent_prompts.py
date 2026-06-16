"""
Prompts used by the ReAct agent loop.

All hardcoded prompt strings previously inlined inside DietAgentLoop live here so
that:
  1) Prompt edits don't require touching the loop control flow.
  2) Prompt builders can be unit-tested in isolation.
  3) Lookups (goal name, meal type, etc.) are centralized.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ----------------------------------------------------------------------
# Lookups
# ----------------------------------------------------------------------

GOAL_NAMES: Dict[str, str] = {
    "FAT_LOSS": "减脂",
    "MUSCLE_GAIN": "增肌",
    "MAINTAIN": "维持",
    "SUGAR_CONTROL": "控糖",
    "SLEEP_IMPROVEMENT": "改善睡眠",
}

MEAL_TYPE_NAMES: Dict[str, str] = {
    "BREAKFAST": "早餐",
    "LUNCH": "午餐",
    "DINNER": "晚餐",
    "SNACK": "零食",
}

PROFILE_FIELD_NAMES: Dict[str, str] = {
    "weight_kg": "体重",
    "budget_per_meal": "预算",
    "gender": "性别",
    "age": "年龄",
    "primary_goal": "目标",
    "height_cm": "身高",
}

DASHBOARD_GOAL_MAP: Dict[str, str] = {
    "FAT_LOSS": "减脂",
    "MUSCLE_GAIN": "增肌",
    "MAINTAIN": "维持",
}


# ----------------------------------------------------------------------
# ReAct loop system prompt & progressive hints
# ----------------------------------------------------------------------

def get_agent_system_prompt() -> str:
    return """你是一个外食健康饮食助手。
你的目标不是给出医学诊断，而是帮助用户在外食、食堂、快餐、餐馆、外卖场景中做更健康、更可执行的选择。
如果涉及热量、蛋白质等数值，请说明是估算。
如果用户有过敏、不耐受、睡眠敏感等记忆，必须优先考虑。
回答要具体，不要空泛。
尽量给出 2~3 个可执行选项。

【重要：当你需要查询餐厅或地点时，必须严格按照以下顺序执行】：
1. 首先调用 map_geocode 将地址转换为经纬度坐标
   - 例如用户说"成都中和有什么餐厅"，必须先调用 map_geocode({"address": "成都市双流区中和街道", "is_chinese_mainland": true})
   - 例如用户说"附近有什么餐厅"，如果知道城市就调用 map_geocode({"address": "成都市武侯区", "is_chinese_mainland": true})
   - 不要猜测坐标，必须先地理编码！
2. 获得坐标后，再调用 map_search_places 搜索餐厅
3. 最后生成带餐厅卡片的回复

可用工具：
- map_geocode: 将中文地址转换为经纬度坐标，输入 {"address": "详细地址", "is_chinese_mainland": true}
  返回: {"success": true, "lat": 30.61, "lng": 104.04, "formatted_address": "..."}
- map_search_places: 搜索地点，输入 {"query": "关键词", "region": "城市", "location": "lat,lng", "radius": 3000, "limit": 5}
  返回: {"success": true, "restaurants": [{"name": "...", "address": "...", "uid": "...", "overall_rating": ...}]}
- map_place_details: 获取地点详情，输入 {"uid": "地点UID"}
- get_user_profile: 获取用户信息
- get_today_meals: 获取今日饮食记录

调用工具的格式（必须严格遵循）：
{"response_type": "tool_call", "tool_name": "工具名", "tool_args": {...}}

如果你不需要调用工具，直接返回普通文本回答即可。

返回JSON格式，包含以下字段（当你不调用工具时）：
- situation_summary: 当前情况分析
- goal_analysis: 目标分析
- recommendation_strategy: 推荐策略
- recommended_options: 推荐选项数组，每项包含name, why_recommended, estimated_calories, order_modification
- not_recommended: 不推荐选项数组
- today_remaining_advice: 今日剩余建议
- sleep_friendly_tips: 睡眠友好建议
- one_sentence_summary: 一句话总结"""


TOOL_REMINDER_HINT = """可用工具提醒：
- map_geocode: 将地址转换为经纬度
- map_search_places: 搜索餐厅/地点
- map_place_details: 获取地点详情
- get_user_profile: 获取用户信息
- get_today_meals: 获取今日饮食记录

如需查询餐厅，先用 map_geocode 获取坐标，再用 map_search_places 搜索。"""

NEAR_LIMIT_HINT = "⚠️ 你即将达到最大对话轮次（{remaining}轮）。如果还有信息需要查询，请尽快完成，或直接给出建议。"

STUCK_HINT = "你已经连续 {turns} 轮没有调用工具。如果当前信息足以回答用户，请直接给出建议。"

EMPTY_SEARCH_RETRY_HINT = (
    "地图搜索返回0结果。请用更宽泛的关键词重试，例如 query=\"餐厅\" 或 query=\"美食\"，"
    "不要放弃，继续调用 map_search_places 获取可供选择的餐厅列表。"
)


# ----------------------------------------------------------------------
# User prompt builder
# ----------------------------------------------------------------------

def build_advice_context(context: Any) -> Dict[str, Any]:
    """Project AgentContext into the dict shape the prompt builder expects."""
    return {
        "profile": context.profile,
        "memories": context.memories,
        "today_meals": context.today_meals,
        "recent_messages": context.recent_messages,
        "message": context.message,
        "intent": context.intent.value,
    }


def build_advice_user_prompt(prompt_context: Dict[str, Any], message: str) -> str:
    """Build the user-side prompt containing profile / memories / today's meals / history."""
    parts = [f"用户消息: {message}\n"]

    if prompt_context.get("profile"):
        p = prompt_context["profile"]
        parts.append(f"\n用户画像:")
        if p.get("primary_goal"):
            parts.append(f"- 目标: {p['primary_goal']}")
        if p.get("budget_per_meal"):
            parts.append(f"- 预算: {p['budget_per_meal']}元/餐")
        if p.get("weight_kg"):
            parts.append(f"- 体重: {p['weight_kg']}kg")
        if p.get("sleep_sensitive"):
            parts.append(f"- 睡眠敏感")

    if prompt_context.get("memories"):
        parts.append(f"\n用户记忆:")
        for m in prompt_context["memories"][:5]:
            parts.append(f"- [{m['memory_type']}] {m['content']}")

    if prompt_context.get("today_meals"):
        total_cal = sum(m.get("estimated_calories", 0) for m in prompt_context["today_meals"])
        parts.append(f"\n今日已记录: {len(prompt_context['today_meals'])}餐, 共{total_cal:.0f}千卡")
        for m in prompt_context["today_meals"]:
            parts.append(f"- {m['meal_type']}: {m['food_text']} (~{m.get('estimated_calories', 0):.0f}千卡)")

    if prompt_context.get("recent_messages"):
        parts.append(f"\n当前会话历史:")
        for m in prompt_context["recent_messages"]:
            role_display = "用户" if m.get("role") == "user" else "助手"
            content = m.get("content", "")
            if len(content) > 200:
                content = content[:200] + "..."
            parts.append(f"- [{role_display}] {content}")

    return "\n".join(parts)


# ----------------------------------------------------------------------
# Restaurant analysis prompt
# ----------------------------------------------------------------------

def build_restaurant_analysis_prompt(
    restaurant_name: str,
    address: str,
    tag: str,
    rating: float,
    price_level: int,
    telephone: str,
    details: Dict[str, Any],
    user_goal: str,
    goal_name: str,
    profile: Optional[Dict],
    today_meals: List[Dict],
) -> str:
    """Build prompt for LLM to analyze a restaurant against user's diet goals."""
    info_parts = [f"餐厅名称: {restaurant_name}"]
    if address:
        info_parts.append(f"地址: {address}")
    if tag:
        info_parts.append(f"标签: {tag}")
    if rating:
        info_parts.append(f"评分: {rating}分")
    if price_level:
        info_parts.append(f"价位: {price_level}（数字越大越贵）")
    if telephone:
        info_parts.append(f"电话: {telephone}")
    if details.get("business_time"):
        info_parts.append(f"营业时间: {details['business_time']}")
    if details.get("type"):
        info_parts.append(f"餐厅类型: {details['type']}")
    basic_info = "\n".join(info_parts)

    if today_meals:
        total_cal = sum(m.get("estimated_calories", 0) for m in today_meals)
        total_protein = sum(m.get("estimated_protein", 0) for m in today_meals)
        today_summary = f"今日已记录 {len(today_meals)} 餐，共 {total_cal:.0f} 千卡，蛋白质 {total_protein:.0f}g"
    else:
        today_summary = "今日尚未记录任何饮食"

    return f"""分析以下餐厅是否符合用户的饮食目标：

【餐厅信息】
{basic_info}

【用户饮食目标】
{goal_name} ({user_goal})

【用户今日饮食情况】
{today_summary}

【用户profile信息】
{profile if profile else "未获取到"}

请分析：
1. 这个餐厅是否适合用户的饮食目标？
2. 如果目标 是增肌，推荐哪些高蛋白菜品？
3. 如果目标是减脂，建议避免哪些高热量菜品？
4. 给出具体的点餐建议（2-3个推荐，1-2个避免）

回答要具体、实用，基于餐厅的标签和类型给出建议。"""


# ----------------------------------------------------------------------
# LLM helper prompts (nutrition estimation, profile parse, memory extract)
# ----------------------------------------------------------------------

def build_nutrition_estimation_prompt(food_text: str) -> str:
    return f"""根据以下食物描述，估算营养成分。只返回JSON格式：
{{
  "estimated_calories": 数字(千卡),
  "estimated_protein": 数字(克),
  "estimated_carbs": 数字(克),
  "estimated_fat": 数字(克),
  "confidence": 0到1之间的置信度
}}

食物: {food_text}
"""


NUTRITION_ESTIMATION_SYSTEM = (
    "你是一个营养估算助手，根据食物描述估算热量和宏量营养素。返回JSON格式。"
)


def build_profile_update_parse_prompt(message: str, current_weight: Optional[float]) -> str:
    return f"""从用户消息中提取要更新的profile字段。

可能的字段和单位：
- weight_kg: 体重，单位是kg，数字。如"体重60kg"、"60kg"、"长了5斤"(需要用当前体重{current_weight}kg加上变化量计算)
- height_cm: 身高，单位是cm，数字
- budget_per_meal: 预算，单位是元，数字
- gender: 性别，值是"male"或"female"
- primary_goal: 目标，值是"FAT_LOSS"/"MUSCLE_GAIN"/"MAINTAIN"/"SUGAR_CONTROL"/"SLEEP_IMPROVEMENT"

重要：食物偏好/不喜欢/过敏信息（如"我不吃香菜"、"我对花生过敏"）不是profile字段，不要返回这些，返回空JSON {{}}。
只有明确说要更新上面的列表里的字段时才返回对应的键值对。

返回JSON格式，键是字段名，值是新值：
{{"field_name": value, ...}}

只返回需要更新的字段。用户消息: {message}"""


PROFILE_UPDATE_PARSE_SYSTEM = (
    "你是一个profile更新解析助手，从用户消息中提取要更新的字段。返回JSON格式。"
)


def build_memory_extraction_prompt(context: Any) -> str:
    context_text = f"用户消息: {context.message}\n"
    if context.profile:
        context_text += f"用户目标: {context.profile.get('primary_goal')}\n"
    if context.memories:
        context_text += f"已有记忆: {[m['content'] for m in context.memories[:5]]}\n"

    return f"""分析用户消息，提取需要长期记忆的信息。返回JSON数组格式：
[{{
  "memory_type": "preference|allergy_intolerance",
  "content": "记忆内容",
  "importance_score": 1-10,
  "confidence_score": 0到1之间
}}]

只提取重要且稳定的信息，不要提取临时状态。
只返回JSON数组，不要其他内容。

上下文:
{context_text}
"""


MEMORY_EXTRACTION_SYSTEM = (
    "你是一个记忆抽取助手，分析用户消息中需要长期记忆的信息。返回JSON数组格式。"
)
