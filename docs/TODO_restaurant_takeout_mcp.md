# Phase 2 TODO: Restaurant & Takeout MCP Integration

> This document outlines the planned features for Phase 2 of the EatFit AI Agent project.
> These features are NOT to be implemented in Phase 1.

---

## Overview

Phase 2 will add the ability for the agent to search for restaurants and takeout options based on user location and preferences. This requires integration with map/takeout MCP (Model Context Protocol) tools.

---

## Goals

1. **Location-based restaurant search** - Users can ask "附近有什么适合减脂的餐馆？" and get recommendations
2. **Takeout/delivery merchant search** - Users can search for delivery options that match their diet goals
3. **Intelligent restaurant filtering** - Agent filters restaurants based on user memories (allergies, budget, goals, etc.)

---

## Implementation Details

### Location Memory Integration

1. Users can save their common locations as `memory_type = "location"`
   - Example: "西南交大犀浦校区附近"
   - Example: "公司楼下"
   - Example: "宿舍附近"

2. High-importance locations should require user confirmation (like other high-importance memory types)

3. Location can be extracted from:
   - Direct user input: "我在西南交大犀浦校区附近"
   - Contextual inference from eating patterns

4. Query pattern:
   ```
   用户: 我在西南交大犀浦校区附近，晚上吃什么好？
   Agent: 根据你的记忆，你常在西南交大犀浦校区附近吃饭。
         正在搜索附近适合减脂的餐馆...
   ```

### MCP Integration

#### Baidu Maps MCP (Primary for Restaurant Search)

1. Use Baidu Maps Web服务 API or SDK
2. Required capabilities:
   - Place search by keyword (餐厅、快餐、小吃)
   - Around-place search by coordinate
   - Place detail search (rating, menu, hours)
   - Navigation/route to place

3. Integration pattern:
   ```python
   # Pseudocode for MCP tool
   def search_restaurants(location: str, keywords: list, budget: float, dietary_restrictions: list):
       # 1. Geocode location string to coordinates
       # 2. Search nearby places with keywords
       # 3. Filter by budget, dietary needs
       # 4. Return top N recommendations
   ```

#### Meituan/Takeout MCP (Future consideration)

1. If available, use Meituan Open Platform API
2. Search merchants by category, rating, delivery time
3. Filter by dietary preferences (low-calorie, high-protein, etc.)

### Agent Loop Changes

1. Add new intent: `restaurant_search`
2. Add new agent step: `searching_nearby_restaurants`
3. Add new action: `restaurant_recommendation_card`

### Restaurant Recommendation Card

Frontend should display restaurant candidates in a card format:

```json
{
  "action_type": "restaurant_recommendation",
  "action_status": "pending",
  "action_data": {
    "restaurants": [
      {
        "name": "轻食沙拉店",
        "address": "距离你300米",
        "rating": 4.5,
        "avg_price": 35,
        "recommended_dishes": ["鸡胸肉沙拉", "藜麦碗"],
        "match_reason": "高蛋白、低油脂、符合你的减脂目标"
      }
    ]
  }
}
```

### Data Storage

1. Restaurant search results do NOT need a separate table
2. Store search context in `chat_messages.action_data` temporarily
3. If user confirms a restaurant, optionally save to `memory_items` with `memory_type = "location"`

### Prompt Changes

System prompt should include:
```
你是一个外食健康饮食助手，也了解用户附近的餐馆选项。
如果用户问附近有什么吃的，可以先问用户位置，或者根据已有记忆推断位置。
对于餐馆推荐，你需要考虑：
- 用户的减脂/增肌目标
- 用户预算（一顿多少钱）
- 用户过敏/不耐受食物
- 用户的饮食偏好（清淡、少油等）
- 距离和方便程度
```

---

## User Flow Examples

### Example 1: Location known from memory
```
用户: 今晚吃什么好？
Agent: 看到你常在西南交大犀浦校区附近吃饭。让我搜一下附近适合减脂的选项。
[MCP调用: 搜索附近餐厅，关键词：轻食、沙拉、健康餐]
Agent: 找到几个选择：
1. 轻食主义 (300m, ¥35/人) - 鸡胸肉沙拉推荐
2. 日式定食(500m, ¥45/人) - 牛肉定食少酱
你想选择哪个？或者告诉我你的具体位置，我可以重新搜索。
```

### Example 2: User provides location
```
用户: 我在公司楼下，有什么好吃的？
Agent: 好的，在公司楼下搜索...
[MCP调用: 搜索公司楼下附近餐厅]
Agent: 公司楼下有这些选择：
...
```

### Example 3: Takeout search
```
用户: 点外卖有什么推荐？
Agent: 你想吃什么类型的？或者告诉我你在哪里，我帮你搜一下附近的外卖选项。
```

---

## Technical Notes

### Map API Selection

Priority order:
1. Baidu Maps (国内覆盖最广)
2. Tencent Maps (微信生态)
3. Google Maps (海外场景)

### Rate Limiting

- Map API calls should be cached where possible
- Limit search frequency to avoid API quota issues
- Store recent search results in session

### Fallback Strategy

If MCP is unavailable or rate-limited:
```
Agent: 地图服务暂时不可用。你可以告诉我你看到了哪些餐馆，
我可以帮你分析哪个更适合你的目标。
```

---

## Not in Scope for Phase 2

- Actual ordering/payment integration
- Real-time delivery tracking
- Restaurant reservation systems
- Reviews/sentiment analysis
- Advanced dietary analysis from restaurant menus

---

## Acceptance Criteria for Phase 2

1. User can say "我在XX附近，想找适合减脂的餐馆" and get restaurant list
2. Agent correctly uses user's location memories
3. Restaurant cards display name, distance, price, recommendation reason
4. Agent considers user's allergies, budget, goals when filtering
5. Graceful fallback when MCP unavailable
6. No physical deletion of memories - use soft delete with status
7. SSE streaming works for restaurant search flow