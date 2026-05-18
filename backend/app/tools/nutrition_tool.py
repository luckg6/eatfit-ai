from typing import List, Dict, Any, Optional


class NutritionTool:
    """MCP-ready nutrition estimation tool using rule-based approach."""

    # Food nutrition database (rough estimates per 100g or per unit)
    FOOD_DATA = {
        "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
        "noodles": {"calories": 140, "protein": 4.5, "carbs": 25, "fat": 1.5},
        "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2},
        "chicken_breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
        "chicken_leg": {"calories": 209, "protein": 26, "carbs": 0, "fat": 11},
        "beef": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15},
        "pork": {"calories": 242, "protein": 27, "carbs": 0, "fat": 14},
        "fish": {"calories": 130, "protein": 28, "carbs": 0, "fat": 3},
        "shrimp": {"calories": 99, "protein": 24, "carbs": 0.2, "fat": 0.3},
        "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11},
        "milk": {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1},
        "tofu": {"calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8},
        "vegetables": {"calories": 20, "protein": 1.5, "carbs": 3.5, "fat": 0.2},
        "potato": {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1},
        "rice_noodles": {"calories": 109, "protein": 2.7, "carbs": 24, "fat": 0.6},
        "fried_rice": {"calories": 190, "protein": 5, "carbs": 30, "fat": 6},
        "braised_pork": {"calories": 250, "protein": 15, "carbs": 8, "fat": 18},
        "tomato_egg": {"calories": 120, "protein": 8, "carbs": 5, "fat": 8},
        "mapo_tofu": {"calories": 180, "protein": 10, "carbs": 8, "fat": 12},
        "green_beans": {"calories": 30, "protein": 2, "carbs": 5, "fat": 0.2},
    }

    # High-protein foods (grams per 100g)
    HIGH_PROTEIN = ["chicken_breast", "beef", "fish", "shrimp", "egg", "tofu", "pork"]

    # High-fat / high-sugar foods to avoid
    HIGH_FAT_SUGAR = ["fried", "oil", "sauce", "cream", "butter", "sugar", "candy", "cake"]

    def estimate_meal_nutrition(self, food_text: str) -> Dict[str, Any]:
        """Estimate nutrition for a food description."""
        food_lower = food_text.lower()
        total_cal = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0

        for food_key, nutrition in self.FOOD_DATA.items():
            if food_key in food_lower:
                multiplier = self._estimate_quantity(food_text, food_key)
                total_cal += nutrition["calories"] * multiplier
                total_protein += nutrition["protein"] * multiplier
                total_carbs += nutrition["carbs"] * multiplier
                total_fat += nutrition["fat"] * multiplier

        if total_cal == 0:
            return {
                "estimated_calories": 400,
                "estimated_protein": 15,
                "estimated_carbs": 50,
                "estimated_fat": 12,
                "note": "Rough estimate based on typical meal"
            }

        return {
            "estimated_calories": round(total_cal, 1),
            "estimated_protein": round(total_protein, 1),
            "estimated_carbs": round(total_carbs, 1),
            "estimated_fat": round(total_fat, 1)
        }

    def _estimate_quantity(self, food_text: str, food_key: str) -> float:
        """Estimate portion multiplier based on keywords."""
        text = food_text.lower()
        if "big" in text or "large" in text or "extra" in text:
            return 1.5
        if "small" in text or "little" in text or "half" in text:
            return 0.7
        if "double" in text or "两份" in text or "two" in text:
            return 2.0
        return 1.0

    def compare_food_options(
        self,
        options: List[str],
        user_goal: str
    ) -> List[Dict[str, Any]]:
        """Compare multiple food options for a user goal."""
        results = []
        for option in options:
            nutrition = self.estimate_meal_nutrition(option)
            score = self.score_meal_for_goal(option, user_goal)
            results.append({
                "food": option,
                "nutrition": nutrition,
                "score": score
            })
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def score_meal_for_goal(self, food_text: str, goal: str) -> int:
        """Score a meal 1-10 based on goal alignment."""
        score = 5
        food_lower = food_text.lower()

        if goal == "FAT_LOSS":
            if any(f in food_lower for f in self.HIGH_FAT_SUGAR):
                score -= 3
            if any(f in food_lower for f in self.HIGH_PROTEIN):
                score += 2
            if "vegetable" in food_lower or "greens" in food_lower:
                score += 1

        elif goal == "MUSCLE_GAIN":
            if any(f in food_lower for f in self.HIGH_PROTEIN):
                score += 3
            if "rice" in food_lower or "noodle" in food_lower:
                score += 1

        elif goal == "SLEEP_FRIENDLY":
            if any(x in food_lower for x in ["coffee", "caffeine", "tea", "coke", "cola", " spicy", "麻辣"]):
                score -= 4
            if any(f in food_lower for f in self.HIGH_PROTEIN):
                score += 1

        return max(1, min(10, score))

    def suggest_healthier_modification(self, food_text: str) -> str:
        """Suggest healthier modifications for a meal."""
        suggestions = []
        food_lower = food_text.lower()

        if "fried" in food_lower or "油炸" in food_lower:
            suggestions.append("可以尝试少油烹饪或选择清蒸")
        if "white rice" in food_lower or "白米饭" in food_lower:
            suggestions.append("可以替换成杂粮饭或减少米饭份量")
        if "noodles" in food_lower or "面" in food_lower:
            suggestions.append("可以加一份青菜，增加纤维摄入")
        if "sauce" in food_lower or "酱汁" in food_lower:
            suggestions.append("备注少酱或不要额外酱汁")
        if "drink" not in food_lower and "drinks" not in food_lower:
            suggestions.append("建议搭配白水或无糖茶，避免含糖饮料")

        if not suggestions:
            return "整体搭配不错，注意控制油盐即可"

        return "; ".join(suggestions)