"""
ReAct tool dispatch registry — maps tool_name -> async callable.

Originally split out of DietAgentLoop._execute_tool (a 100+ line if/elif
chain inlined in the loop). Splitting it out:

  1) Makes the tool surface explicit and grep-able.
  2) Lets new tools be added without touching the loop body.
  3) Each handler is a small async function, easy to unit-test in isolation.

Tools that need one-off setup (like `from app.tools.mcp_client import ...`) defer
their import to the call site so importing this module doesn't pull in baidu-map
SDK at app start-up.
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from app.agent.agent_types import AgentContext

logger = logging.getLogger("eatfit.agent.tools")


# A tool takes (args, context, agent) and returns a dict.
# `agent` exposes db / latitude / longitude / tool bundles (profile_tools etc.).
ToolHandler = Callable[[Dict[str, Any], "AgentContext", Any], Awaitable[Dict[str, Any]]]


# --- Tool implementations ---------------------------------------------------

async def tool_map_geocode(args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    from app.tools.mcp_client import get_baidu_map_client
    client = get_baidu_map_client()
    address = args.get("address", "")
    is_china = args.get("is_chinese_mainland", True)
    result = await client.geocode(address, is_china=is_china)
    logger.info(f"[ReAct] map_geocode: address={address}, result={str(result)[:200] if result else 'None'}")
    if result and result.get("result"):
        geo = result["result"]
        location = geo.get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")
        if lat is not None and lng is not None:
            return {
                "success": True,
                "lat": lat,
                "lng": lng,
                "formatted_address": geo.get("formatted_address", ""),
            }
    return {"success": False, "error": f"无法解析地址: {address}"}


async def tool_map_search_places(args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    from app.tools.mcp_client import get_baidu_map_client
    client = get_baidu_map_client()
    query = args.get("query", "美食")
    region = args.get("region", "成都")
    location = args.get("location")
    radius = args.get("radius", 2000)
    is_china = args.get("is_chinese_mainland", True)

    logger.info(f"[ReAct] map_search_places: query={query}, region={region}, location={location}")
    places = await client.search_places(
        query=query, region=region, location=location, radius=radius, is_china=is_china,
    )
    logger.info(f"[ReAct] map_search_places returned {len(places) if places else 0} places")
    if not places:
        return {"success": True, "restaurants": [], "message": "未找到结果"}

    restaurants = []
    for p in places[:args.get("limit", 5)]:
        restaurants.append({
            "name": p.get("name", ""),
            "address": p.get("address", ""),
            "tag": p.get("tag", ""),
            "overall_rating": p.get("overall_rating"),
            "uid": p.get("uid", ""),
        })
    logger.info(f"[ReAct] returning {len(restaurants)} restaurants: {[r['name'] for r in restaurants]}")
    return {"success": True, "restaurants": restaurants, "count": len(restaurants)}


async def tool_map_place_details(args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    from app.tools.mcp_client import get_baidu_map_client
    client = get_baidu_map_client()
    uid = args.get("uid")
    is_china = args.get("is_chinese_mainland", True)
    if not uid:
        return {"success": False, "error": "缺少UID"}
    details = await client.get_place_details(uid, is_china=is_china)
    if not details:
        return {"success": False, "error": "无法获取详情"}
    return {"success": True, "details": details}


async def tool_search_restaurants(args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    from app.tools.restaurant_tools import RestaurantTools
    restaurant_tools = RestaurantTools(agent.db)
    query = args.get("query", "美食")
    location = args.get("location")
    region = args.get("region", "成都")
    radius = args.get("radius", 2000)
    limit = args.get("limit", 5)

    if not location and agent.latitude and agent.longitude:
        location = f"{agent.latitude},{agent.longitude}"

    restaurants = await restaurant_tools.search_nearby_restaurants(
        user_id=context.user_id, query=query, region=region, location=location, radius=radius, limit=limit,
    )
    return {"success": True, "restaurants": restaurants, "count": len(restaurants)}


async def tool_get_restaurant_details(args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    from app.tools.restaurant_tools import RestaurantTools
    restaurant_tools = RestaurantTools(agent.db)
    uid = args.get("uid")
    name = args.get("name", "")
    if not uid:
        return {"success": False, "error": "缺少UID"}
    details = await restaurant_tools.get_restaurant_details(uid)
    if not details:
        return {"success": False, "error": "无法获取详情"}
    return {"success": True, "details": details, "name": name}


async def tool_get_user_profile(args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    profile = agent.profile_tools.get_user_profile(context.user_id)
    return {"success": True, "profile": profile}


async def tool_get_today_meals(args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    meals = agent.meal_tools.get_today_meals(context.user_id)
    return {"success": True, "meals": meals}


async def tool_get_user_memories(args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    """
    ReAct 工具只在 subagents/chat.py 的 ReAct 循环里被调用，因此用 'diet_advice' 作为
    intent key 复用 memory_tools.intent_memory_map 中那 8 类相关记忆的过滤
    配置（与 general_chat 的"全类型"fallback 不同）。原代码漏传 intent，
    导致 kwarg `limit=10` 被绑到 intent 槽位，整条向量查询退化成纯数字匹配。
    """
    memories = agent.memory_tools.get_relevant_memories(
        user_id=context.user_id, intent="diet_advice", limit=10,
        query_text=context.message,
    )
    return {"success": True, "memories": memories}


# --- Registry ---------------------------------------------------------------

TOOL_REGISTRY: Dict[str, ToolHandler] = {
    "map_geocode": tool_map_geocode,
    "map_search_places": tool_map_search_places,
    "map_place_details": tool_map_place_details,
    "search_restaurants": tool_search_restaurants,
    "get_restaurant_details": tool_get_restaurant_details,
    "get_user_profile": tool_get_user_profile,
    "get_today_meals": tool_get_today_meals,
    "get_user_memories": tool_get_user_memories,
}


async def execute_tool(tool_name: str, tool_args: Dict[str, Any], context: "AgentContext", agent: Any) -> Dict[str, Any]:
    """Dispatch a tool call by name; return a uniform {success, ...} dict."""
    handler = TOOL_REGISTRY.get(tool_name)
    if handler is None:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    try:
        return await handler(tool_args, context, agent)
    except Exception as e:
        logger.error(f"[Orchestrator] tool execution error: {tool_name}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
