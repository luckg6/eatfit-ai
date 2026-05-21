"""
Baidu Map MCP Client for restaurant search integration.
使用百度地图官方 MCP HTTP 端点。
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

import httpx

logger = logging.getLogger("eatfit.mcp")

BAIDU_MAP_API_KEY = os.getenv("BAIDU_MAP_API_KEY", "")
MCP_ENDPOINT = f"https://mcp.map.baidu.com/mcp?ak={BAIDU_MAP_API_KEY}"


class BaiduMapMCPClient:
    """Client for Baidu Map MCP HTTP endpoint."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or BAIDU_MAP_API_KEY
        self.endpoint = f"https://mcp.map.baidu.com/mcp?ak={self.api_key}"


    async def _call_mcp(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool via JSON-RPC over HTTP."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.endpoint, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"[BaiduMapMCP] raw response: {response.text[:500]}")
                content_type = response.headers.get("Content-Type", "")

                if "application/json" in content_type:
                    return response.json()
                elif "text/event-stream" in content_type:
                    # SSE 响应，解析 data: 行
                    lines = response.text.strip().split("\n")
                    for line in lines:
                        if line.startswith("data:"):
                            data = line[5:].strip()
                            if data and data != "[DONE]":
                                return json.loads(data)
                    return {}
                else:
                    return response.json()
        except Exception as e:
            logger.error(f"[BaiduMapMCP] _call_mcp failed: {e}")
            import traceback
            traceback.print_exc()
            return {}

    async def search_places(
        self,
        query: str = "美食",
        region: str = "北京",
        location: str = None,
        radius: int = 1000,
        tag: str = None,
        is_china: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for places using Baidu Map MCP.
        """
        args = {
            "query": query,
            "region": region,
            "is_chinese_mainland": str(is_china).lower(),
        }
        if location:
            args["location"] = location
            args["radius"] = radius
        if tag:
            args["tag"] = tag

        result = await self._call_mcp("map_search_places", args)

        if result.get("error"):
            logger.error(f"[BaiduMapMCP] map_search_places error: {result.get('error')}")
            return []

        # 解析 MCP 响应内容
        content = result.get("result", {}).get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text", "")
            try:
                data = json.loads(text)
                return data.get("results", [])
            except json.JSONDecodeError:
                logger.error(f"[BaiduMapMCP] failed to parse response: {text[:200]}")
                return []
        return []

    async def get_place_details(self, uid: str, is_china: bool = True) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific POI."""
        result = await self._call_mcp("map_place_details", {"uid": uid, "is_chinese_mainland": str(is_china).lower()})

        if result.get("error"):
            logger.error(f"[BaiduMapMCP] map_place_details error: {result.get('error')}")
            return None

        content = result.get("result", {}).get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text", "")
            try:
                data = json.loads(text)
                return data.get("result")
            except json.JSONDecodeError:
                logger.error(f"[BaiduMapMCP] failed to parse detail response: {text[:200]}")
                return None
        return None

    async def ip_location(self) -> Optional[Dict[str, Any]]:
        """Get user's current location by IP."""
        result = await self._call_mcp("map_ip_location", {})

        if result.get("error"):
            logger.error(f"[BaiduMapMCP] map_ip_location error: {result.get('error')}")
            return None

        content = result.get("result", {}).get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text", "")
            try:
                data = json.loads(text)
                content_data = data.get("content", {})
                address_detail = content_data.get("address_detail", {})
                point = content_data.get("point", {})

                mc_x = float(point.get("x", 0))
                mc_y = float(point.get("y", 0))
                lat, lng = self._mc_to_geocode(mc_x, mc_y)

                return {
                    "location": f"{lat},{lng}",
                    "city": address_detail.get("city", ""),
                    "province": address_detail.get("province", ""),
                    "district": address_detail.get("district", ""),
                }
            except json.JSONDecodeError:
                logger.error(f"[BaiduMapMCP] failed to parse ip_location response: {text[:200]}")
                return None
        return None

    def _mc_to_geocode(self, mc_x: float, mc_y: float) -> tuple:
        """Convert Baidu Mercator BD-09MC to BD-09LL (百度墨卡托转百度经纬度)."""
        MCBAND = [12890594.86, 8362377.87, 5591021, 3481989.83, 1678043.12, 0]
        MC2LL = [
            [1.410526172116255e-8, 0.00000898305509648872, -1.9939833816331, 200.9824383106796, -187.2403703815547, 91.6087516669843, -23.38765649603339, 2.57121317296198, -0.03801003308653, 17337981.2],
            [-7.435856389565537e-9, 0.000008983055097726239, -0.78625201886289, 96.32687599759846, -1.85204757529826, -59.36935905485877, 47.40033549296737, -16.50741931063887, 2.28786674699375, 10260144.86],
            [-3.030883460898826e-8, 0.00000898305509983578, 0.30071316287616, 59.74293618442277, 7.357984074871, -25.38371002664745, 13.45380521110908, -3.29883767235584, 0.32710905363475, 6856817.37],
            [-1.981981304930552e-8, 0.000008983055099779535, 0.03278182852591, 40.31678527705744, 0.65659298677277, -4.44255534477492, 0.85341911805263, 0.12923347998204, -0.04625736007561, 4482777.06],
            [3.09191371068437e-9, 0.000008983055096812155, 0.00006995724062, 23.10934304144901, -0.00023663490511, -0.6321817810242, -0.00663494467273, 0.03430082397953, -0.00466043876332, 2555164.4],
            [2.890871144776878e-9, 0.000008983055095805407, -3.068298e-8, 7.47137025468032, -0.00000353937994, -0.02145144861037, -0.00001234426596, 0.00010322952773, -0.00000323890364, 826088.5],
        ]

        abs_y = abs(mc_y)
        for i, band in enumerate(MCBAND):
            if abs_y >= band:
                coef = MC2LL[i]
                break
        else:
            coef = MC2LL[-1]

        x_temp = coef[0] + coef[1] * abs(mc_x)
        c = abs_y / coef[9]
        y_temp = coef[2] + coef[3] * c + coef[4] * c ** 2 + coef[5] * c ** 3 + coef[6] * c ** 4 + coef[7] * c ** 5 + coef[8] * c ** 6
        x_temp *= -1 if mc_x < 0 else 1
        y_temp *= -1 if mc_y < 0 else 1

        return (y_temp, x_temp)

    async def geocode(self, address: str, is_china: bool = True) -> Optional[Dict[str, Any]]:
        """Convert address to coordinates."""
        result = await self._call_mcp("map_geocode", {"address": address, "is_chinese_mainland": str(is_china).lower()})

        if result.get("error"):
            logger.error(f"[BaiduMapMCP] map_geocode error: {result.get('error')}")
            return None

        content = result.get("result", {}).get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text", "")
            try:
                data = json.loads(text)
                return data  # data itself contains result
            except json.JSONDecodeError:
                logger.error(f"[BaiduMapMCP] failed to parse geocode response: {text[:200]}")
                return None
        return None


# Global client instance
_baidu_map_client: Optional[BaiduMapMCPClient] = None


def get_baidu_map_client() -> BaiduMapMCPClient:
    """Get or create the global Baidu Map MCP client instance."""
    global _baidu_map_client
    if _baidu_map_client is None:
        _baidu_map_client = BaiduMapMCPClient()
    return _baidu_map_client