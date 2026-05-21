"""
Restaurant search tools for the EatFit Agent using Baidu Map API.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.tools.mcp_client import get_baidu_map_client

logger = logging.getLogger("eatfit.restaurant")


class RestaurantTools:
    """Tools for searching restaurants via Baidu Map API."""

    def __init__(self, db: Session):
        self.db = db

    async def search_nearby_restaurants(
        self,
        user_id: int,
        query: str = "美食",
        location: str = None,
        region: str = None,
        radius: int = 2000,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for restaurants near a location.

        Args:
            user_id: User ID for context
            query: Search keyword (e.g., "美食", "火锅", "轻食", "快餐")
            location: "lat,lng" center point (if None, use IP location)
            region: City name (if None, inferred from IP)
            radius: Search radius in meters
            limit: Max results to return
        """
        client = get_baidu_map_client()

        # 如果传入的是文字地址（不是 lat,lng 坐标），需要先地理编码
        if location and not re.match(r"^-?\d+\.?\d*,-?\d+\.?\d*$", location):
            # 这是一个文字地址，需要地理编码
            logger.info(f"[RestaurantTools] location is text address, geocoding: {location}")
            geocode_result = await client.geocode(location)
            if geocode_result and geocode_result.get("location", {}).get("lat", 0) != 0:
                lat = geocode_result["location"]["lat"]
                lng = geocode_result["location"]["lng"]
                location = f"{lat},{lng}"
                logger.info(f"[RestaurantTools] geocoded to: {location}")
            else:
                logger.warning(f"[RestaurantTools] geocode failed for '{location}', falling back to IP location")
                location = None

        # 优先使用用户传入的位置，否则用 IP 定位
        if not location:
            ip_result = await client.ip_location()
            logger.info(f"[RestaurantTools] ip_result: {ip_result}")
            if ip_result:
                district = ip_result.get("district", "")
                city = ip_result.get("city", "")
                if district:
                    # 用区名政府地址地理编码
                    geocode_result = await client.geocode(f"成都市郫都区人民政府")
                    logger.info(f"[RestaurantTools] geocode raw result: {geocode_result}")
                    if geocode_result and geocode_result.get("location", {}).get("lat", 0) != 0:
                        lat = geocode_result["location"]["lat"]
                        lng = geocode_result["location"]["lng"]
                        location = f"{lat},{lng}"
                        logger.info(f"[RestaurantTools] geocoded location: {location}")
                    else:
                        location = ip_result.get("location")
                        logger.info(f"[RestaurantTools] geocode failed, using ip location: {location}")
                region = city

        logger.info(f"[RestaurantTools] search param: location={location}, region={region}, radius={radius}")

        if not region:
            region = "北京"  # Default fallback

        # Search via Baidu Map MCP
        results = await client.search_places(
            query=query,
            region=region,
            location=location,
            radius=5000,
        )

        # Format results for the agent
        restaurants = []
        for item in results[:limit]:
            restaurants.append({
                "name": item.get("name", ""),
                "address": item.get("address", ""),
                "location": item.get("location", {}),
                "uid": item.get("uid", ""),
                "telephone": item.get("telephone"),
                "tag": item.get("tag"),
                "price_level": item.get("price_level"),
                "overall_rating": item.get("overall_rating"),
                "detail_url": item.get("detail_url"),
            })

        logger.info(f"[RestaurantTools] Found {len(restaurants)} restaurants for query='{query}'")
        return restaurants

    async def get_restaurant_details(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get detailed restaurant info by UID."""
        client = get_baidu_map_client()
        return await client.get_place_details(uid)

    async def format_restaurant_for_display(self, restaurant: Dict[str, Any]) -> str:
        """Format a restaurant for display in chat."""
        name = restaurant.get("name", "未知")
        address = restaurant.get("address", "")
        rating = restaurant.get("overall_rating")
        tag = restaurant.get("tag", "")
        price = restaurant.get("price_level")

        parts = [f"**{name}**"]
        if tag:
            parts.append(f"标签: {tag}")
        if rating:
            parts.append(f"评分: {rating}分")
        if price:
            parts.append(f"价位: {price}")
        if address:
            parts.append(f"地址: {address}")

        return " | ".join(parts)