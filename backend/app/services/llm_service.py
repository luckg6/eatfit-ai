import logging
from typing import Optional, Dict, Any
import json

from app.core.config import settings

logger = logging.getLogger("eatfit.llm")


class BaseLLMService:
    """Base class for LLM services."""

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.model = settings.LLM_MODEL

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text from LLM."""
        raise NotImplementedError

    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response from LLM output."""
        import re
        response = response.strip()
        # Remove <think> ...  thinking tags first (handles MiniMax-style output)
        response = re.sub(r'<think>.*?', '', response, flags=re.DOTALL)
        # Remove ```json ... ``` or ``` ... ``` code blocks
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        # Find the first JSON object/array start AFTER all think tags (skip any { inside think blocks)
        # Look for the last ]] or the actual JSON start after the think block
        json_start = response.find('[{')
        if json_start < 0:
            json_start = response.find('{"')
        if json_start < 0:
            # Fallback: find first { after last newline or at start
            json_start = max(0, response.find('['))
        response = response[json_start:]
        return response.strip()


class MockLLMService(BaseLLMService):
    """Mock LLM service for development without API key."""

    def __init__(self):
        super().__init__()

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return mock response based on user prompt content."""
        user_lower = user_prompt.lower()

        if "diet advice" in system_prompt.lower() or "recommend" in system_prompt.lower():
            return self._get_mock_diet_advice(user_prompt)
        elif "memory" in system_prompt.lower() or "extract" in system_prompt.lower():
            return self._get_mock_memory_extraction(user_prompt)
        elif "daily plan" in system_prompt.lower():
            return self._get_mock_daily_plan()
        elif "weekly review" in system_prompt.lower():
            return self._get_mock_weekly_review()
        else:
            return self._get_default_mock_response(user_prompt)

    def _get_mock_diet_advice(self, user_prompt: str) -> str:
        """Return mock diet advice response."""
        if "牛肉饭" in user_prompt or "beef rice" in user_prompt.lower():
            return json.dumps({
                "situation_summary": "用户是训练后晚餐场景，希望补充蛋白质，同时担心晚餐影响睡眠。",
                "goal_analysis": "训练后需要补充蛋白质和适量碳水，但晚餐应避免过油、过辣和大量含糖饮料。",
                "recommendation_strategy": "可以吃牛肉饭，但要调整点餐方式：米饭半份或正常份根据饥饿程度选择，少酱汁，加青菜，避免辣油和含糖饮料。",
                "recommended_options": [
                    {
                        "name": "少油牛肉饭 + 青菜 + 无糖饮料",
                        "why_recommended": "牛肉能提供蛋白质，米饭补充训练后糖原，青菜增加饱腹感和纤维。",
                        "estimated_calories": 650,
                        "estimated_protein": 35,
                        "estimated_carbs": 75,
                        "estimated_fat": 20,
                        "order_modification": "备注少油少酱，米饭半份或七分，额外加青菜，不要辣油。",
                        "suitable_for": ["训练后", "增肌减脂", "外食场景"],
                        "score": 8
                    },
                    {
                        "name": "鸡腿饭去皮 + 青菜 + 鸡蛋",
                        "why_recommended": "蛋白质更稳定，脂肪可通过去皮和少酱降低。",
                        "estimated_calories": 600,
                        "estimated_protein": 38,
                        "estimated_carbs": 65,
                        "estimated_fat": 18,
                        "order_modification": "鸡腿尽量去皮，少酱汁，加一份青菜。",
                        "suitable_for": ["训练后", "高蛋白"],
                        "score": 8
                    },
                    {
                        "name": "牛肉粉少汤 + 加蛋",
                        "why_recommended": "比重油盖饭更清爽，加蛋可以提高蛋白质。",
                        "estimated_calories": 550,
                        "estimated_protein": 30,
                        "estimated_carbs": 70,
                        "estimated_fat": 12,
                        "order_modification": "少喝汤，少辣，加一个鸡蛋。",
                        "suitable_for": ["晚餐", "睡眠友好"],
                        "score": 7
                    }
                ],
                "not_recommended": [
                    {
                        "name": "重辣肥牛饭 + 可乐",
                        "reason": "油脂、辣度和含糖饮料都可能影响睡眠，也容易让总热量偏高。",
                        "better_alternative": "选择少油牛肉饭，饮料换成水或无糖茶。"
                    }
                ],
                "today_remaining_advice": "如果这顿吃了牛肉饭，夜里不要再加高糖零食；如果仍然饿，可以选择牛奶或无糖酸奶。",
                "sleep_friendly_tips": "晚餐尽量避免可乐、奶茶、浓茶、咖啡和特别辣的食物。",
                "training_day_tips": "训练后这顿可以保留适量主食，不建议完全不吃碳水。",
                "next_meal_advice": "明天早餐可以选择鸡蛋、牛奶、全麦面包或包子搭配无糖豆浆，继续保证蛋白质。",
                "risk_level": "LOW",
                "risk_warnings": [
                    "以上热量和营养为粗略估算，不等同于精确营养计算。",
                    "如果有特殊疾病或长期睡眠障碍，请咨询医生或营养师。"
                ],
                "one_sentence_summary": "可以吃牛肉饭，但关键是少油少酱、加青菜、避开含糖饮料。"
            })
        else:
            return json.dumps({
                "situation_summary": "用户在外食场景中需要选择更健康的饮食选项。",
                "goal_analysis": "根据用户情况，建议选择高蛋白、低油脂的食物组合。",
                "recommendation_strategy": "优选蛋白质来源食物，增加蔬菜摄入，控制高油高糖食物。",
                "recommended_options": [
                    {
                        "name": "鸡胸肉沙拉 + 糙米饭",
                        "why_recommended": "高蛋白低脂，增加蔬菜纤维，适合减脂人群。",
                        "estimated_calories": 480,
                        "estimated_protein": 35,
                        "estimated_carbs": 45,
                        "estimated_fat": 12,
                        "order_modification": "要求少沙拉酱，可以换成油醋汁",
                        "suitable_for": ["减脂", "增肌", "健康饮食"],
                        "score": 8
                    },
                    {
                        "name": "清汤牛肉面 + 青菜",
                        "why_recommended": "相对清淡，牛肉提供蛋白，面条补充碳水。",
                        "estimated_calories": 520,
                        "estimated_protein": 28,
                        "estimated_carbs": 60,
                        "estimated_fat": 14,
                        "order_modification": "少放牛肉汤，尽量不喝汤",
                        "suitable_for": ["增肌", "外食场景"],
                        "score": 7
                    }
                ],
                "not_recommended": [
                    {
                        "name": "炸鸡套餐 + 可乐",
                        "reason": "油炸食物脂肪含量高，可乐增加糖分摄入，不利于健康目标。",
                        "better_alternative": "选择烤鸡或清炒菜品，饮料换成无糖茶"
                    }
                ],
                "today_remaining_advice": "注意控制总热量摄入，优先保证蛋白质，多选择蒸煮类食物。",
                "sleep_friendly_tips": "晚餐不宜过晚，避免咖啡因和高糖食品。",
                "training_day_tips": "训练后及时补充蛋白质和碳水，帮助恢复。",
                "next_meal_advice": "注意均衡营养，不要连续两餐都是高碳水。",
                "risk_level": "LOW",
                "risk_warnings": [
                    "以上热量和营养为粗略估算，不等同于精确营养计算。",
                    "建议根据个人情况调整份量。"
                ],
                "one_sentence_summary": "选择高蛋白、低油脂的食物，多吃蔬菜，控制零食。"
            })

    def _get_mock_memory_extraction(self, user_prompt: str) -> str:
        """Return mock memory extraction response."""
        return json.dumps({
            "memories": [
                {
                    "memoryType": "DIET_PREFERENCE",
                    "content": "用户喜欢牛肉饭、鸡腿饭等有饱腹感的外食，不喜欢太清淡的轻食。",
                    "importanceScore": 8,
                    "source": "auto_extracted"
                }
            ]
        })

    def _get_mock_daily_plan(self) -> str:
        """Return mock daily plan response."""
        return json.dumps({
            "breakfast_suggestion": "鸡蛋2个 + 牛奶1盒 + 全麦面包2片（约400卡，蛋白质25g）",
            "lunch_suggestion": "米饭1碗 + 鸡腿1个 + 青菜1份 + 番茄炒蛋（约650卡，蛋白质40g）",
            "dinner_suggestion": "牛肉饭或鱼肉豆腐餐，避免油炸和重辣（约550卡，蛋白质35g）",
            "snack_suggestion": "无糖酸奶1盒或水果1个（不超过150卡）",
            "protein_focus": "今日蛋白质目标约100g，训练日更要保证蛋白质摄入",
            "avoid_today": ["奶茶", "油炸食品", "蛋糕甜点"],
            "sleep_reminder": "睡前3小时尽量不要吃东西，晚餐别太晚",
            "one_day_strategy": "今天比昨天多做一个健康选择就好"
        })

    def _get_mock_weekly_review(self) -> str:
        """Return mock weekly review response."""
        return json.dumps({
            "week_summary": "本周共记录14餐，平均每日摄入约1800卡，蛋白质摄入基本达标",
            "what_went_well": [
                "蛋白质摄入比上周稳定",
                "外食选择更健康了",
                "开始注意蔬菜摄入"
            ],
            "main_problems": [
                "晚餐时间偏晚",
                "偶尔吃高油高盐食物",
                "饮水可能不够"
            ],
            "protein_consistency": "蛋白质摄入约70g/天，有3天达标，4天不足",
            "sleep_impact_analysis": "注意晚餐不要太晚和太油，可能影响睡眠质量",
            "eating_out_pattern": "外食场景占80%，油盐控制需要加强",
            "weight_and_body_fat_trend": "体重基本稳定，体脂需要持续观察",
            "next_week_strategy": "1. 提前吃晚餐 2. 记录每天蛋白质 3. 增加绿叶蔬菜",
            "next_week_actions": [
                "晚餐尽量在7-8点前吃完",
                "每天至少记录2餐",
                "选择1-2次轻食替代外卖"
            ],
            "warnings": ["如有特殊健康状况，请咨询医生或营养师"]
        })

    def _get_default_mock_response(self, user_prompt: str) -> str:
        """Return default mock response."""
        return json.dumps({
            "response": "这是Mock模式的回复。配置真实的LLM_API_KEY后可以获取真实AI建议。",
            "tip": "在backend/.env中设置LLM_API_KEY即可启用真实AI服务"
        })


class RealLLMService(BaseLLMService):
    """Real LLM service using OpenAI-compatible API."""

    def __init__(self):
        super().__init__()

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using OpenAI-compatible API."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }

        raw_content = None
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]
                logger.info(f"[RealLLMService] Raw model response:\n{raw_content}\n---")
                cleaned = self._clean_json_response(raw_content)
                logger.info(f"[RealLLMService] Response cleaned, length={len(cleaned)}, preview='{cleaned[:150]}...'")
                return cleaned
        except Exception as e:
            logger.error(f"[RealLLMService] LLM API error: {e}")
            if raw_content:
                logger.error(f"[RealLLMService] Raw content was: {raw_content[:500]}")
            return json.dumps({
                "situation_summary": "用户在寻求饮食建议，当前场景是外食。",
                "goal_analysis": "根据用户情况，建议选择高蛋白、低油脂的食物组合。",
                "recommendation_strategy": "优选蛋白质来源食物，增加蔬菜摄入，控制高油高糖食物。",
                "recommended_options": [
                    {
                        "name": "鸡胸肉沙拉 + 糙米饭",
                        "why_recommended": "高蛋白低脂，增加蔬菜纤维，适合减脂人群。",
                        "estimated_calories": 480,
                        "estimated_protein": 35,
                        "estimated_carbs": 45,
                        "estimated_fat": 12,
                        "order_modification": "要求少沙拉酱，可以换成油醋汁",
                        "suitable_for": ["减脂", "增肌", "健康饮食"],
                        "score": 8
                    }
                ],
                "not_recommended": [
                    {
                        "name": "炸鸡套餐 + 可乐",
                        "reason": "油炸食物脂肪含量高，可乐增加糖分摄入，不利于健康目标。",
                        "better_alternative": "选择烤鸡或清炒菜品，饮料换成无糖茶"
                    }
                ],
                "today_remaining_advice": "注意控制总热量摄入，优先保证蛋白质，多选择蒸煮类食物。",
                "sleep_friendly_tips": "晚餐不宜过晚，避免咖啡因和高糖食品。",
                "training_day_tips": "训练后及时补充蛋白质和碳水，帮助恢复。",
                "next_meal_advice": "注意均衡营养，不要连续两餐都是高碳水。",
                "risk_level": "LOW",
                "risk_warnings": [
                    "以上热量和营养为粗略估算，不等同于精确营养计算。",
                    "建议根据个人情况调整份量。"
                ],
                "one_sentence_summary": "选择高蛋白、低油脂的食物，多吃蔬菜，控制零食。"
            })


_llm_service: Optional[BaseLLMService] = None


def get_llm_service() -> BaseLLMService:
    """Get the appropriate LLM service based on configuration."""
    global _llm_service
    if _llm_service is None:
        if settings.LLM_API_KEY:
            _llm_service = RealLLMService()
        else:
            _llm_service = MockLLMService()
    return _llm_service