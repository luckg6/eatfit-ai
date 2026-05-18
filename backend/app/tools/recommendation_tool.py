from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.tools.nutrition_tool import NutritionTool
from app.tools.memory_tool import MemoryTool
from app.tools.meal_log_tool import MealLogTool
from app.tools.profile_tool import ProfileTool


class RecommendationTool:
    """MCP-ready recommendation tool combining all tools."""

    def __init__(self, db: Session):
        self.db = db
        self.nutrition_tool = NutritionTool()
        self.memory_tool = MemoryTool(db)
        self.meal_log_tool = MealLogTool(db)
        self.profile_tool = ProfileTool(db)

    def recommend_meal_options(
        self,
        user_id: int,
        context: str,
        scenario: str,
        is_training_day: bool
    ) -> List[Dict[str, Any]]:
        """Recommend meal options based on user context."""
        profile = self.profile_tool.get_user_food_profile(user_id)
        if not profile:
            return []

        memories = self.memory_tool.search_memories(user_id, memory_types=["DIET_PREFERENCE", "FOOD_DISLIKE"])
        goal = profile.get("primary_goal", "GENERAL_HEALTH")

        # Base recommendations by scenario
        recommendations = []

        if scenario == "TAKEOUT":
            if "牛肉" in context or "beef" in context.lower():
                recommendations.append({
                    "name": "少油牛肉饭 + 青菜",
                    "estimated_calories": 650,
                    "estimated_protein": 35,
                    "estimated_carbs": 75,
                    "estimated_fat": 20,
                    "order_modification": "备注少油少酱，米饭半份，加青菜",
                    "suitable_for": ["训练后", "增肌", "减脂"]
                })
            if "鸡" in context or "chicken" in context.lower():
                recommendations.append({
                    "name": "去皮鸡腿饭 + 青菜",
                    "estimated_calories": 580,
                    "estimated_protein": 38,
                    "estimated_carbs": 65,
                    "estimated_fat": 18,
                    "order_modification": "鸡腿去皮，少酱汁，加青菜",
                    "suitable_for": ["高蛋白", "减脂"]
                })

        if is_training_day:
            recommendations.append({
                "name": "训练后蛋白餐",
                "estimated_calories": 500,
                "estimated_protein": 40,
                "estimated_carbs": 50,
                "estimated_fat": 15,
                "order_modification": "训练后补充优质蛋白和碳水",
                "suitable_for": ["训练日", "增肌"]
            })

        return recommendations[:3]

    def generate_daily_plan(
        self,
        user_id: int,
        is_training_day: bool = False
    ) -> Dict[str, Any]:
        """Generate daily meal plan."""
        profile = self.profile_tool.get_user_food_profile(user_id)
        memories = self.memory_tool.search_memories(user_id, memory_types=["DIET_PREFERENCE", "SLEEP_TRIGGER"])

        goal = profile.get("primary_goal", "GENERAL_HEALTH") if profile else "GENERAL_HEALTH"

        breakfast = "鸡蛋 + 牛奶 + 全麦面包或包子（约400卡，蛋白质25g）"
        lunch = "米饭 + 肉菜 + 青菜（约650卡，蛋白质35g）"
        dinner = "如果训练后：牛肉饭或鸡腿饭；如果休息日：鱼肉或豆腐 + 蔬菜（约550卡）"
        snack = "无糖酸奶或水果（不超过200卡）"

        if is_training_day:
            dinner = "训练后补充蛋白质和碳水，牛肉饭或鸡腿饭为宜"
            lunch += "，训练日前午餐可多补充碳水"

        protein_focus = "训练日至少摄入体重(kg)*1.6g蛋白质" if is_training_day else "每天保证体重(kg)*1.2g蛋白质"

        return {
            "breakfast_suggestion": breakfast,
            "lunch_suggestion": lunch,
            "dinner_suggestion": dinner,
            "snack_suggestion": snack,
            "protein_focus": protein_focus,
            "avoid_today": ["奶茶", "油炸食品", "重辣食物"] if goal == "SLEEP_FRIENDLY" else ["奶茶", "油炸食品"],
            "sleep_reminder": "晚餐尽量在睡前3小时吃完，避免咖啡因和高糖饮料" if profile.get("sleep_sensitive") else "",
            "one_day_strategy": "今天多做一个更好的选择，慢慢积累"
        }

    def generate_weekly_review(self, user_id: int) -> Dict[str, Any]:
        """Generate weekly diet review."""
        weekly_summary = self.meal_log_tool.summarize_weekly_intake(user_id)
        profile = self.profile_tool.get_user_food_profile(user_id)
        memories = self.memory_tool.search_memories(user_id)

        avg_daily_cal = weekly_summary["total_calories"] / 7 if weekly_summary["total_meals"] > 0 else 0

        return {
            "week_summary": f"本周共记录{weekly_summary['total_meals']}餐，平均每日摄入约{int(avg_daily_cal)}卡",
            "what_went_well": ["有记录饮食的日子比上周增加", "外食选择比上周更健康"],
            "main_problems": ["蛋白质可能摄入不足", "晚餐时间可能太晚"],
            "protein_consistency": f"本周蛋白质摄入约{weekly_summary['total_protein']:.0f}g，平均每日{int(weekly_summary['total_protein']/7)}g",
            "sleep_impact_analysis": "注意晚餐内容对睡眠的影响",
            "eating_out_pattern": "外食场景较多，注意控制油盐",
            "weight_and_body_fat_trend": "建议持续记录体重和体脂变化",
            "next_week_strategy": "1. 早餐保证蛋白质摄入 2. 训练日额外补充蛋白 3. 晚餐尽量在7点前完成",
            "next_week_actions": [
                "每天记录至少2餐",
                "训练日增加蛋白质摄入",
                "尝试自己准备1次早餐"
            ],
            "warnings": ["以上为粗略估算，如有特殊健康状况请咨询医生"]
        }