"""
Intent classification for user messages.

Two-stage:
  1) Rule-based pattern matching (fast path, zero LLM cost)
  2) LLM-based classifier (fallback for ambiguous cases or context-dependent
     utterances like ellipsis / anaphora)

The LLM path accepts `recent_messages` so it can disambiguate references like
"那个多少卡？" (refers to a meal from the previous turn). It is not currently
wired into the orchestrator — see `classify_with_llm` for the entry point.
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Intent(Enum):
    MEAL_LOG = "meal_log"
    PROFILE_UPDATE = "profile_update"
    MEMORY_CANDIDATE = "memory_candidate"
    DASHBOARD_QUERY = "dashboard_query"
    GENERAL_CHAT = "general_chat"
    RESTAURANT_SEARCH_PLANNED = "restaurant_search_planned"  # Phase 2


@dataclass
class IntentResult:
    intent: Intent
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = None


# ----------------------------------------------------------------------
# Rule-based patterns (fast path)
# ----------------------------------------------------------------------

MEAL_LOG_PATTERNS = [
    (r"刚吃|吃了|吃过|吃完|就吃|吃了点|叫了|点了|外卖到了", 0.9),
    (r"(早|午|晚)饭.*吃", 0.85),
    (r"吃了.*饭|吃了.*面|吃了.*包|吃了.*粉|吃了.*菜", 0.85),
    (r"摄入了|摄取了|摄取了.*热量", 0.8),
    (r"记录.*餐?|记.*吃了", 0.8),
]

PROFILE_UPDATE_PATTERNS = [
    (r"体重.*(|是|到|为)(\d+)", 0.95),
    (r"(身高|体脂|目标体重)", 0.9),
    (r"我现在.*(|是|在)(\d+)", 0.9),
    (r"预算.*(|是|在|控制|在|约)(\d+)", 0.95),
    (r"(男|女|其他|保密)", 0.85),  # gender
    (r"年龄|我今年", 0.85),
    (r"(增肌|减脂|维持|控糖|改善睡眠).*目标", 0.9),
    (r"主要.*(目标|想)", 0.8),
    (r"我.*过敏|我不.*吃|我不能.*吃", 0.85),
    (r"(帮我?)?(更新|改一下).*(体重|身高|目标|资料)", 0.9),
    (r"(长了|重了|胖了|减了|掉了|瘦了)(\d+(?:\.\d+)?)\s*(?:斤|公斤|kg)", 0.85),
    (r"(\d+(?:\.\d+)?)\s*(?:斤|公斤|kg)", 0.8),
]

MEMORY_CANDIDATE_PATTERNS = [
    (r"不喜欢|不喜欢.*食物", 0.85),
    (r"(我不吃|我不能吃|我.*过敏)(.*)", 0.9),  # 食物偏好/过敏 → memory
    (r"我对.*过敏", 0.95),
    (r"(?:乳糖|麸质|海鲜|坚果).*?不耐", 0.95),
    (r"(喝了|吃了|喝了).*(不舒服|拉肚子|过敏)", 0.9),
    (r"睡眠.*(不好|浅|差|失眠)", 0.85),
    (r"(咖啡|茶|奶茶|可乐).*睡不着", 0.85),
    (r"晚饭.*(影响睡眠|睡不着)", 0.85),
    (r"经常.*(食堂|外食|外卖|餐厅)", 0.8),
    (r"(学校|公司|西南交大|犀浦)", 0.75),
    (r"偏好.*(清淡|重口|高蛋白|少油)", 0.8),
    (r"一般.*吃|通常.*吃|经常.*吃", 0.7),
]

DASHBOARD_QUERY_PATTERNS = [
    (r"今天.*(吃了多少|热量|蛋白质|摄入)", 0.9),
    (r"今日.*(总结|摄入|记录)", 0.9),
    (r"今天.*(怎么样|如何)", 0.7),
    (r"我的.*(目标|进度)", 0.75),
]

RESTAURANT_SEARCH_PATTERNS = [
    (r"附近.*(有什么|哪个|哪家)", 0.85),
    (r"附近.*(餐馆|餐厅|饭店|外卖)", 0.85),
    (r"搜索.*附近|找.*附近", 0.8),
    (r"地图.*搜索|百度地图", 0.7),
    # Restaurant detail lookup (higher priority than dashboard_query)
    (r"(帮我)?查看.*餐厅.*详细信息", 0.88),
    (r"餐厅.*(UID|uid).*详细", 0.9),
    (r"(分析|查看).*是否符合.*(目标|饮食)", 0.85),
]


def classify_intent_rule_based(text: str) -> Optional[IntentResult]:
    """Classify intent using pattern matching. Returns None if no clear match."""
    text_lower = text.lower()

    # Check meal_log first
    for pattern, base_confidence in MEAL_LOG_PATTERNS:
        if re.search(pattern, text):
            return IntentResult(
                intent=Intent.MEAL_LOG,
                confidence=base_confidence,
                reasoning=f"Matched meal pattern: {pattern}"
            )

    # Check memory_candidate first to prioritize health constraints (allergy, intolerance)
    # e.g. "我有乳糖不耐能吃什么" should first extract the allergy as memory, then give advice
    for pattern, base_confidence in MEMORY_CANDIDATE_PATTERNS:
        if re.search(pattern, text):
            return IntentResult(
                intent=Intent.MEMORY_CANDIDATE,
                confidence=base_confidence,
                reasoning=f"Matched memory pattern: {pattern}"
            )

    # Check profile_update
    for pattern, base_confidence in PROFILE_UPDATE_PATTERNS:
        if re.search(pattern, text):
            return IntentResult(
                intent=Intent.PROFILE_UPDATE,
                confidence=base_confidence,
                reasoning=f"Matched profile pattern: {pattern}"
            )

    # Check dashboard_query
    for pattern, base_confidence in DASHBOARD_QUERY_PATTERNS:
        if re.search(pattern, text):
            return IntentResult(
                intent=Intent.DASHBOARD_QUERY,
                confidence=base_confidence,
                reasoning=f"Matched dashboard pattern: {pattern}"
            )

    # Check restaurant_search (Phase 2 planned)
    for pattern, base_confidence in RESTAURANT_SEARCH_PATTERNS:
        if re.search(pattern, text):
            return IntentResult(
                intent=Intent.RESTAURANT_SEARCH_PLANNED,
                confidence=base_confidence,
                reasoning=f"Matched restaurant pattern (Phase 2): {pattern}"
            )

    return None


def classify(text: str) -> IntentResult:
    """
    Main intent classification function (rule-based only).
    LLM fallback happens in the agent loop when confidence < 0.5.
    """
    rule_result = classify_intent_rule_based(text)
    if rule_result is not None:
        return rule_result
    # No rule match - agent loop will call LLM if needed
    return IntentResult(
        intent=Intent.GENERAL_CHAT,
        confidence=0.3,
        reasoning="No rule pattern matched. LLM classification will be attempted."
    )


def classify_multi(text: str) -> List[Tuple[Intent, float, str]]:
    """
    Multi-intent classification: returns ALL matched intents with confidence.
    Used when a message has multiple purposes (e.g., "我有乳糖不耐能吃什么"
    should BOTH save memory AND give food recommendations).
    Returns list of (intent, confidence, reasoning) tuples sorted by confidence descending.
    """
    results = []

    # Check meal_log
    for pattern, base_confidence in MEAL_LOG_PATTERNS:
        if re.search(pattern, text):
            results.append((Intent.MEAL_LOG, base_confidence, f"Matched meal pattern: {pattern}"))
            break

    # Check memory_candidate first to prioritize health constraints
    for pattern, base_confidence in MEMORY_CANDIDATE_PATTERNS:
        if re.search(pattern, text):
            results.append((Intent.MEMORY_CANDIDATE, base_confidence, f"Matched memory pattern: {pattern}"))
            break

    # Check profile_update
    for pattern, base_confidence in PROFILE_UPDATE_PATTERNS:
        if re.search(pattern, text):
            results.append((Intent.PROFILE_UPDATE, base_confidence, f"Matched profile pattern: {pattern}"))
            break

    # Check restaurant_search (higher priority for restaurant-specific messages)
    for pattern, base_confidence in RESTAURANT_SEARCH_PATTERNS:
        if re.search(pattern, text):
            results.append((Intent.RESTAURANT_SEARCH_PLANNED, base_confidence, f"Matched restaurant pattern (Phase 2): {pattern}"))
            break

    # Check dashboard_query
    for pattern, base_confidence in DASHBOARD_QUERY_PATTERNS:
        if re.search(pattern, text):
            results.append((Intent.DASHBOARD_QUERY, base_confidence, f"Matched dashboard pattern: {pattern}"))
            break

    # Sort by confidence descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def extract_entities(text: str, intent: Intent) -> Dict[str, Any]:
    """Extract entities based on intent."""
    entities = {}

    if intent == Intent.MEAL_LOG:
        # Try to extract meal type
        meal_type_match = re.search(r"(早|午|晚|夜宵|宵夜|早餐|午餐|晚餐|午饭|早饭)?餐", text)
        if meal_type_match:
            meal_map = {"早": "BREAKFAST", "午": "LUNCH", "晚": "DINNER", "夜宵": "SNACK", "宵夜": "SNACK", "早餐": "BREAKFAST", "午餐": "LUNCH", "晚餐": "DINNER", "午饭": "LUNCH", "早饭": "BREAKFAST"}
            entities["meal_type"] = meal_map.get(meal_type_match.group(1), "SNACK")

        # Try to extract food description
        food_match = re.search(r"(吃了|点了|叫了)?(.+)", text)
        if food_match:
            entities["food_text"] = food_match.group(2).strip()

    elif intent == Intent.PROFILE_UPDATE:
        # Extract weight delta: 长了/重了/胖了/减了X斤 → relative change (stored in kg)
        # Matches: 长了5斤, 重了3公斤, 瘦了7.5kg, 胖了2斤
        weight_delta_match = re.search(r"(长|重|胖|减|掉|瘦)(了)?(\d+(?:\.\d+)?)\s*(斤|公斤|kg)", text, re.IGNORECASE)
        if weight_delta_match:
            delta = float(weight_delta_match.group(3))
            unit = weight_delta_match.group(4).lower()
            if unit in ("斤",):
                delta = delta * 0.5  # 斤 → kg
            # else: kg or 公斤 already in kg
            direction = weight_delta_match.group(1)
            if direction in ("长", "重", "胖"):
                entities["_weight_delta"] = delta  # positive = gained
            else:
                entities["_weight_delta"] = -delta  # negative = lost
            entities["_weight_delta_text"] = f"{direction}了{weight_delta_match.group(3)}{weight_delta_match.group(4)}"

        # Extract absolute weight (with "体重" keyword OR just "X斤" / "Xkg" standalone)
        weight_match = re.search(r"体重[是为]?(\d+(?:\.\d+)?)(?:kg)?", text)
        if not weight_match:
            # Try plain "X斤" without 体重 keyword
            weight_match = re.search(r"^(\d+(?:\.\d+)?)斤", text)
        if not weight_match:
            # Try "Xkg" without 体重 keyword
            weight_match = re.search(r"(\d+(?:\.\d+)?)\s*kg", text, re.IGNORECASE)
        if weight_match:
            weight_val = float(weight_match.group(1))
            # If unit is 斤 (no kg suffix), convert to kg
            if "斤" in weight_match.group(0):
                weight_val = weight_val * 0.5
            entities["weight_kg"] = weight_val

        # Extract budget
        budget_match = re.search(r"预算[是为]?(\d+(?:\.\d+)?)", text)
        if budget_match:
            entities["budget_per_meal"] = float(budget_match.group(1))

        # Extract gender
        if "男" in text:
            entities["gender"] = "male"
        elif "女" in text:
            entities["gender"] = "female"

        # Extract height
        height_match = re.search(r"身高(?:是|到|为)?(\d+(?:\.\d+)?)", text)
        if height_match:
            entities["height_cm"] = float(height_match.group(1))

        # Extract goal
        if "减脂" in text:
            entities["primary_goal"] = "FAT_LOSS"
        elif "增肌" in text:
            entities["primary_goal"] = "MUSCLE_GAIN"
        elif "维持" in text:
            entities["primary_goal"] = "MAINTAIN"
        elif "控糖" in text:
            entities["primary_goal"] = "SUGAR_CONTROL"
        elif "改善睡眠" in text:
            entities["primary_goal"] = "SLEEP_IMPROVEMENT"

    return entities


# ----------------------------------------------------------------------
# LLM-based classifier (fallback / context-aware)
# ----------------------------------------------------------------------

LLM_INTENT_SYSTEM_PROMPT = """你是一个意图分类助手。根据用户消息判断真实意图。

可能的意图：
- meal_log: 用户在记录吃了什么（如"刚吃了牛肉饭"、"记录午餐"）
- profile_update: 用户明确想更新资料（如"体重是70kg"、"我目标增肌"、"更新身高175"、"长了5斤帮我更新"）
- memory_candidate: 用户提到值得记住的信息，但不一定是要更新资料（如"我不喜欢吃香菜"、"长了5斤"、"最近睡眠不好"）
- dashboard_query: 用户在查今日摄入或进度（如"今天吃了多少热量"）
- general_chat: 闲聊、问建议、推荐、或者无法归类（"吃什么好"、"推荐什么"都归这里，走 LLM ReAct 给出建议）

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
    recent_messages: Optional[List[Dict[str, Any]]] = None,
) -> IntentResult:
    """
    Async LLM-based intent classification for ambiguous cases or
    context-dependent utterances (ellipsis, anaphora).

    Pass `recent_messages` so the LLM can resolve references like
    "那个多少卡？" (refers to a meal from the previous turn).
    """
    from app.services.llm_service import get_llm_service
    import json

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
                "source": "llm",
            },
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return IntentResult(
            intent=Intent.GENERAL_CHAT,
            confidence=0.3,
            reasoning=f"LLM classification failed: {e}. Defaulting to general_chat.",
        )


def _build_user_prompt(
    text: str,
    profile_context: Optional[Dict[str, Any]],
    recent_messages: Optional[List[Dict[str, Any]]],
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
        "profile_update": Intent.PROFILE_UPDATE,
        "memory_candidate": Intent.MEMORY_CANDIDATE,
        "dashboard_query": Intent.DASHBOARD_QUERY,
        "general_chat": Intent.GENERAL_CHAT,
        "restaurant_search_planned": Intent.RESTAURANT_SEARCH_PLANNED,
    }
    return mapping.get(intent_str.lower(), Intent.GENERAL_CHAT)
