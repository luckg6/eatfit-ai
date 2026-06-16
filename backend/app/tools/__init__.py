"""
Tools module for EatFit.

Each tool bundles DB access for a domain. They expose plain Python methods that
the agent loop calls — no MCP wiring here, that lives in mcp_client.py.

Removed (previously orphan, never imported outside tools/__init__.py):
  - MemoryTool, NutritionTool, MealLogTool, ProfileTool, RecommendationTool
"""
from app.tools.chat_tools import ChatTools
from app.tools.meal_tools import MealTools
from app.tools.memory_tools import MemoryTools
from app.tools.profile_tools import ProfileTools
from app.tools.restaurant_tools import RestaurantTools

__all__ = [
    "ProfileTools",
    "MemoryTools",
    "MealTools",
    "ChatTools",
    "RestaurantTools",
]
