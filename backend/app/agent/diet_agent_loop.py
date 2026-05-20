"""
Diet Agent Loop - ReAct style main loop for the EatFit agent.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("eatfit.agent")

from app.agent.intent_classifier import Intent, IntentResult, classify, classify_multi, extract_entities
from app.tools.profile_tools import ProfileTools
from app.tools.memory_tools import MemoryTools
from app.tools.meal_tools import MealTools
from app.tools.chat_tools import ChatTools
from app.tools.restaurant_tools import RestaurantTools
from app.services.llm_service import get_llm_service


class AgentStep(Enum):
    """Agent execution steps for tracing."""
    INTENT_DETECTED = "intent_detected"
    LOADING_PROFILE = "loading_profile"
    LOADING_MEMORIES = "loading_memories"
    LOADING_TODAY_MEALS = "loading_today_meals"
    LOADING_RECENT_CHAT = "loading_recent_chat"
    PARSING_MEAL = "parsing_meal"
    PARSING_PROFILE_UPDATE = "parsing_profile_update"
    CREATING_PENDING_ACTION = "creating_pending_action"
    GENERATING_ADVICE = "generating_advice"
    EXTRACTING_MEMORIES = "extracting_memories"
    MEMORY_SAVED = "memory_saved"
    FINAL_RESPONSE = "final_response"


@dataclass
class AgentContext:
    """Context passed through the agent loop."""
    user_id: int
    session_id: int
    message: str
    intent: Intent = Intent.GENERAL_CHAT
    intent_confidence: float = 0.5
    intents: List[Tuple[Intent, float, str]] = field(default_factory=list)  # All matched intents
    profile: Optional[Dict[str, Any]] = None
    memories: List[Dict[str, Any]] = field(default_factory=list)
    today_meals: List[Dict[str, Any]] = field(default_factory=list)
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)
    pending_actions: List[Dict[str, Any]] = field(default_factory=list)
    extracted_memories: List[Dict[str, Any]] = field(default_factory=list)
    llm_response: Optional[Dict[str, Any]] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Response from the agent loop."""
    text: str
    action: Optional[Dict[str, Any]] = None  # pending action to confirm
    memory_action: Optional[Dict[str, Any]] = None  # memory confirm action
    steps: List[Dict[str, Any]] = field(default_factory=list)
    context_snapshot: Dict[str, Any] = field(default_factory=dict)


class DietAgentLoop:
    """Main agent loop for diet advice using ReAct pattern."""

    def __init__(self, db, user, latitude=None, longitude=None, restaurant_context=None):
        self.db = db
        self.user = user
        self.latitude = latitude
        self.longitude = longitude
        self._restaurant_context = restaurant_context or {}
        self.profile_tools = ProfileTools(db)
        self.memory_tools = MemoryTools(db)
        self.meal_tools = MealTools(db)
        self.chat_tools = ChatTools(db)
        self.restaurant_tools = RestaurantTools(db)

    async def run(self, message: str, session_id: int) -> AgentResponse:
        """
        Run the agent loop on a user message.
        Returns the agent response with potential pending actions.
        """
        context = AgentContext(
            user_id=self.user.id,
            session_id=session_id,
            message=message
        )

        # Step 1: Multi-intent detection
        multi_results = classify_multi(message)
        context.intents = multi_results  # Store all matched intents

        # Use top intent as primary
        if multi_results:
            primary_intent, primary_confidence, reasoning = multi_results[0]
            context.intent = primary_intent
            context.intent_confidence = primary_confidence
            logger.info(f"[agent] Multi-intent detected: {[(i[0].value, i[1]) for i in multi_results]}")
            logger.info(f"[agent] Primary intent: {primary_intent.value} (confidence={primary_confidence}), reasoning: {reasoning}")
            self._add_step(context, AgentStep.INTENT_DETECTED, {
                "intents": [(i[0].value, i[1], i[2]) for i in multi_results],
                "primary_intent": primary_intent.value,
                "confidence": primary_confidence,
                "reasoning": reasoning
            })
        else:
            # No rule matches → GENERAL_CHAT
            context.intent = Intent.GENERAL_CHAT
            context.intent_confidence = 0.3
            logger.info(f"[agent] No rule match, defaulting to general_chat")
            self._add_step(context, AgentStep.INTENT_DETECTED, {
                "intents": [],
                "primary_intent": Intent.GENERAL_CHAT.value,
                "confidence": 0.3,
                "reasoning": "No rule pattern matched"
            })

        # Step 2: Load context (always needed for any intent, even general_chat)
        # Load profile
        context.profile = self.profile_tools.get_user_profile(self.user.id)
        self._add_step(context, AgentStep.LOADING_PROFILE, {
            "loaded": context.profile is not None
        })

        # Load relevant memories
        context.memories = self.memory_tools.get_relevant_memories(
            self.user.id, context.intent.value, limit=10
        )
        self._add_step(context, AgentStep.LOADING_MEMORIES, {
            "count": len(context.memories),
            "types": [m["memory_type"] for m in context.memories]
        })

        # Load today's meals (needed for most intents)
        context.today_meals = self.meal_tools.get_today_meals(self.user.id)
        self._add_step(context, AgentStep.LOADING_TODAY_MEALS, {
            "meal_count": len(context.today_meals),
            "total_calories": sum(m.get("estimated_calories", 0) for m in context.today_meals)
        })

        # Load recent chat messages from this session for context continuity
        context.recent_messages = self.chat_tools.get_recent_messages(
            context.session_id, self.user.id, limit=10
        )
        self._add_step(context, AgentStep.LOADING_RECENT_CHAT, {
            "count": len(context.recent_messages)
        })

        # Step 3: Handle intents (multi-intent: run all primary intents in priority order)
        # Filter out low-confidence intents (< 0.6) as noise
        primary_intents = [(i, c, r) for i, c, r in multi_results if c >= 0.6] if multi_results else []

        # Build list of handlers to execute
        handlers_to_run = []
        for intent, confidence, reasoning in primary_intents:
            if intent == Intent.MEAL_LOG:
                handlers_to_run.append(("meal_log", self._handle_meal_log(context)))
            elif intent == Intent.PROFILE_UPDATE:
                handlers_to_run.append(("profile_update", self._handle_profile_update(context)))
            elif intent == Intent.MEMORY_CANDIDATE:
                handlers_to_run.append(("memory_candidate", self._handle_memory_candidate(context)))
            elif intent == Intent.DASHBOARD_QUERY:
                handlers_to_run.append(("dashboard_query", self._handle_dashboard_query(context)))
            elif intent == Intent.RESTAURANT_SEARCH_PLANNED:
                handlers_to_run.append(("restaurant", self._handle_restaurant_search_planned(context)))

        # Also run general_chat for DIET_ADVICE intent
        for intent, confidence, reasoning in primary_intents:
            if intent == Intent.DIET_ADVICE and not any(h[0] == "diet_advice" for h in handlers_to_run):
                handlers_to_run.append(("diet_advice", self._handle_diet_advice(context)))

        # If no primary intents, fall back to general chat
        if not handlers_to_run:
            return await self._handle_general_chat(context)

        # Execute handlers and collect results
        responses = []
        for name, coro in handlers_to_run:
            try:
                resp = await coro
                responses.append((name, resp)) 
            except Exception as e:
                logger.error(f"[agent] Handler {name} failed: {e}", exc_info=True)

        # Merge responses
        return self._merge_responses(responses, context)

    def _add_step(self, context: AgentContext, step: AgentStep, data: Dict[str, Any]) -> None:
        """Add an agent step for tracing."""
        context.steps.append({
            "step": step.value,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

    async def _handle_meal_log(self, context: AgentContext) -> AgentResponse:
        """Handle meal logging intent."""
        self._add_step(context, AgentStep.PARSING_MEAL, {"message": context.message})

        # Parse meal from text
        parsed = self.meal_tools.parse_meal_from_text(context.message)

        # Use LLM to estimate nutrition
        nutrition_data = await self._estimate_nutrition(context.message, context.profile)

        # Create pending action
        pending_action = self.meal_tools.create_pending_meal_action(
            user_id=context.user_id,
            parsed_meal=parsed,
            estimated_calories=nutrition_data.get("estimated_calories", 0),
            estimated_protein=nutrition_data.get("estimated_protein", 0),
            estimated_carbs=nutrition_data.get("estimated_carbs", 0),
            estimated_fat=nutrition_data.get("estimated_fat", 0),
            calorie_confidence=nutrition_data.get("confidence", 0.65)
        )

        self._add_step(context, AgentStep.CREATING_PENDING_ACTION, {
            "action_type": "meal_log",
            "food_text": parsed.get("food_text")
        })

        # Generate acknowledgment text
        response_text = self._generate_meal_log_response(parsed, nutrition_data)

        return AgentResponse(
            text=response_text,
            action=pending_action,
            steps=context.steps
        )

    async def _handle_profile_update(self, context: AgentContext) -> AgentResponse:
        """Handle profile update intent."""
        self._add_step(context, AgentStep.PARSING_PROFILE_UPDATE, {"message": context.message})

        # Extract profile updates from message
        entities = extract_entities(context.message, context.intent)

        if not entities:
            # Fallback to LLM parsing
            entities = await self._parse_profile_update_with_llm(context.message)

        if not entities:
            return AgentResponse(
                text="抱歉，我没有理解你想更新的资料。能再说明一下吗？",
                steps=context.steps
            )

        # Get current profile to show old value
        current_profile = self.profile_tools.get_user_profile(context.user_id)
        old_values = {}
        for key, new_value in entities.items():
            if current_profile and key in current_profile:
                old_values[key] = current_profile[key]

        # If _weight_delta is present, compute the new absolute weight
        if "_weight_delta" in entities and "weight_kg" not in entities:
            current_weight = current_profile.get("weight_kg") if current_profile else None
            if current_weight is not None:
                new_weight = round(current_weight + entities["_weight_delta"], 1)
                entities["weight_kg"] = new_weight
            # Remove internal fields before sending to frontend
            entities.pop("_weight_delta", None)
            entities.pop("_weight_delta_text", None)

        # Create pending action for confirmation
        action_data = {
            "action_type": "profile_update",
            "action_status": "pending",
            "action_data": {
                "updates": entities,
                "old_values": old_values,
                "display_text": self._generate_profile_update_display(entities, old_values)
            }
        }

        self._add_step(context, AgentStep.CREATING_PENDING_ACTION, {
            "action_type": "profile_update",
            "updates": entities
        })

        response_text = f"检测到你想更新: {self._generate_profile_update_display(entities, old_values)}"

        return AgentResponse(
            text=response_text,
            action=action_data,
            steps=context.steps
        )

    async def _handle_memory_candidate(self, context: AgentContext) -> AgentResponse:
        """Handle memory candidate intent."""
        import logging
        logger = logging.getLogger("eatfit.advice")
        logger.info(f"[memory] ========== _handle_memory_candidate ENTERED ==========")
        logger.info(f"[memory] message={context.message}")
        logger.info(f"[memory] user_id={context.user_id}, intent={context.intent}")
        self._add_step(context, AgentStep.EXTRACTING_MEMORIES, {"message": context.message})

        # Extract memory candidates using LLM
        memory_candidates = await self._extract_memory_candidates(context)
        logger.info(f"[memory] _extract_memory_candidates returned: {type(memory_candidates)} len={len(memory_candidates) if memory_candidates else 0}, raw={memory_candidates}")

        if not memory_candidates:
            logger.warning(f"[memory] no candidates extracted, falling through to general_chat")
            return await self._handle_general_chat(context)

        # Validate first candidate structure
        top_candidate = memory_candidates[0]
        logger.info(f"[memory] top_candidate={top_candidate}, memory_type={top_candidate.get('memory_type') if isinstance(top_candidate, dict) else 'NOT_DICT'}, content={top_candidate.get('content') if isinstance(top_candidate, dict) else 'NOT_DICT'}")
        if not isinstance(top_candidate, dict) or "memory_type" not in top_candidate or "content" not in top_candidate:
            logger.warning(f"[memory] invalid candidate structure, falling through to general_chat")
            return await self._handle_general_chat(context)

        # Check if it's high importance
        is_high_importance = self.is_high_importance_memory(top_candidate["memory_type"])
        logger.info(f"[memory] memory_type={top_candidate['memory_type']}, is_high_importance={is_high_importance}")

        if is_high_importance:
            # Create pending memory confirm action
            memory_action = self.memory_tools.create_pending_memory(
                user_id=context.user_id,
                memory_type=top_candidate["memory_type"],
                content=top_candidate["content"],
                importance_score=top_candidate.get("importance_score", 5),
                confidence_score=top_candidate.get("confidence_score", 0.8)
            )

            response_text = memory_action["display_text"]

            return AgentResponse(
                text=response_text,
                memory_action=memory_action,
                steps=context.steps
            )
        else:
            # Auto-save low-risk preferences
            import logging
            logger = logging.getLogger("eatfit.advice")
            logger.info(f"[memory] entering auto-save: memory_type={top_candidate['memory_type']}, content={top_candidate['content']}")
            try:
                created = self.memory_tools.create_memory(
                    user_id=context.user_id,
                    memory_type=top_candidate["memory_type"],
                    content=top_candidate["content"],
                    importance_score=top_candidate.get("importance_score", 3),
                    source="auto_extracted"
                )
                self._add_step(context, AgentStep.MEMORY_SAVED, {
                    "memory_id": created.id if created else None,
                    "memory_type": top_candidate["memory_type"],
                    "content": top_candidate["content"],
                    "success": created is not None
                })
                logger.info(f"[memory] auto-saved: user_id={context.user_id}, type={top_candidate['memory_type']}, content={top_candidate['content']}, memory_id={created.id if created else 'NONE'}")
            except Exception as e:
                logger.error(f"[memory] auto-save failed: {e}", exc_info=True)
                self._add_step(context, AgentStep.MEMORY_SAVED, {
                    "error": str(e),
                    "memory_type": top_candidate["memory_type"],
                    "content": top_candidate["content"],
                    "success": False
                })

            return AgentResponse(
                text=f"已记住: {top_candidate['content']}",
                steps=context.steps
            )

    async def _handle_dashboard_query(self, context: AgentContext) -> AgentResponse:
        """Handle dashboard query intent."""
        summary = self.meal_tools.get_daily_summary(context.user_id)

        # Get profile for goal context
        profile = context.profile or self.profile_tools.get_user_profile(self.user.id)

        response_text = self._generate_dashboard_response(summary, profile, context.today_meals)

        return AgentResponse(
            text=response_text,
            steps=context.steps,
            context_snapshot={
                "today_summary": summary,
                "profile": profile,
                "memories": context.memories
            }
        )

    async def _handle_restaurant_search_planned(self, context: AgentContext) -> AgentResponse:
        """Handle restaurant search intent (Phase 2 planned)."""
        return AgentResponse(
            text="餐馆搜索能力会在下一阶段接入地图工具。目前你可以告诉我你附近的几个餐馆或外卖选项，我可以先帮你判断哪个更适合你的目标。",
            steps=context.steps
        )

    async def _handle_diet_advice(self, context: AgentContext) -> AgentResponse:
        """Handle diet advice intent (called as part of multi-intent)."""
        return await self._handle_general_chat(context)

    async def _handle_general_chat(self, context: AgentContext) -> AgentResponse:
        """Handle general chat with LLM, supporting ReAct tool-calling."""
        self._add_step(context, AgentStep.GENERATING_ADVICE, {})

        # Build context for LLM
        llm = get_llm_service()
        system_prompt = self._get_system_prompt()

        # Build initial conversation history for ReAct loop
        conversation_history = [{"role": "system", "content": system_prompt}]

        # Add recent messages from session for context continuity
        if context.recent_messages:
            for msg in context.recent_messages[-6:]:
                role = "user" if msg.get("role") == "user" else "assistant"
                content = msg.get("content", "")
                if content:
                    conversation_history.append({"role": role, "content": content})

        # Build user prompt with context
        prompt_context = self._build_advice_context(context)
        user_prompt = self._build_user_prompt(prompt_context, context.message)
        conversation_history.append({"role": "user", "content": user_prompt})

        # ReAct loop: call LLM, execute tools, continue until direct response
        max_iterations = 5
        iteration = 0
        response_text = ""
        response_data = {"one_sentence_summary": ""}

        while iteration < max_iterations:
            iteration += 1
            try:
                response_text = await llm.generate_from_history(conversation_history)

                # Try to parse as JSON
                try:
                    response_data = json.loads(response_text)
                    context.llm_response = response_data
                except json.JSONDecodeError:
                    response_data = {"one_sentence_summary": response_text}
                    context.llm_response = response_data

                # Check if LLM wants to call a tool
                is_tool_call = response_data.get("response_type") == "tool_call" or (
                    "tool_name" in response_data and "tool_args" in response_data
                )

                if is_tool_call:
                    tool_name = response_data.get("tool_name")
                    tool_args = response_data.get("tool_args", {})

                    # Execute the tool
                    tool_result = await self._execute_tool(tool_name, tool_args, context)

                    # Add tool call and result to conversation
                    conversation_history.append({"role": "assistant", "content": json.dumps(response_data, ensure_ascii=False)})
                    conversation_history.append({"role": "system", "content": f"[Tool Result for {tool_name}]: {json.dumps(tool_result, ensure_ascii=False)}"})

                    # Continue to next iteration
                    continue

                # Direct response - we're done
                break

            except Exception as e:
                logger.error(f"[ReAct loop] iteration {iteration} error: {e}", exc_info=True)
                # Don't use generic fallback - let HTTP errors propagate with their real error
                import httpx
                if isinstance(e, httpx.HTTPStatusError):
                    # Return a tool_call retry signal to the LLM with the error context
                    response_data = {
                        "response_type": "error",
                        "error": f"API错误: {str(e)}",
                        "one_sentence_summary": f"API请求失败，请重试或调整参数"
                    }
                else:
                    response_data = {"one_sentence_summary": f"处理出错: {str(e)}"}
                break

        self._add_step(context, AgentStep.FINAL_RESPONSE, {
            "preview": response_text[:100] if response_text else "no response"
        })

        return AgentResponse(
            text=self._format_advice_response(response_data, context),
            steps=context.steps
        )

    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        try:
            if tool_name == "map_geocode":
                from app.tools.mcp_client import get_baidu_map_client
                client = get_baidu_map_client()
                address = tool_args.get("address", "")
                is_china = tool_args.get("is_chinese_mainland", True)
                result = await client.geocode(address, is_china=is_china)
                logger.info(f"[ReAct] map_geocode: address={address}, result={str(result)[:200] if result else 'None'}")
                if result and result.get("result"):
                    geo = result["result"]
                    location = geo.get("location", {})
                    lat = location.get("lat")
                    lng = location.get("lng")
                    if lat is not None and lng is not None:
                        return {"success": True, "lat": lat, "lng": lng, "formatted_address": geo.get("formatted_address", "")}
                return {"success": False, "error": f"无法解析地址: {address}"}

            elif tool_name == "map_search_places":
                from app.tools.mcp_client import get_baidu_map_client
                client = get_baidu_map_client()
                query = tool_args.get("query", "美食")
                region = tool_args.get("region", "成都")
                location = tool_args.get("location")
                radius = tool_args.get("radius", 2000)
                is_china = tool_args.get("is_chinese_mainland", True)

                logger.info(f"[ReAct] map_search_places: query={query}, region={region}, location={location}")
                places = await client.search_places(query=query, region=region, location=location, radius=radius, is_china=is_china)
                logger.info(f"[ReAct] map_search_places returned {len(places) if places else 0} places")
                if not places:
                    return {"success": True, "restaurants": [], "message": "未找到结果"}

                restaurants = []
                for p in places[:tool_args.get("limit", 5)]:
                    restaurants.append({
                        "name": p.get("name", ""),
                        "address": p.get("address", ""),
                        "tag": p.get("tag", ""),
                        "overall_rating": p.get("overall_rating"),
                        "uid": p.get("uid", ""),
                    })
                logger.info(f"[ReAct] returning {len(restaurants)} restaurants: {[r['name'] for r in restaurants]}")
                return {"success": True, "restaurants": restaurants, "count": len(restaurants)}

            elif tool_name == "map_place_details":
                from app.tools.mcp_client import get_baidu_map_client
                client = get_baidu_map_client()
                uid = tool_args.get("uid")
                is_china = tool_args.get("is_chinese_mainland", True)
                if not uid:
                    return {"success": False, "error": "缺少UID"}
                details = await client.get_place_details(uid, is_china=is_china)
                if not details:
                    return {"success": False, "error": "无法获取详情"}
                return {"success": True, "details": details}

            elif tool_name == "search_restaurants":
                from app.tools.restaurant_tools import RestaurantTools
                restaurant_tools = RestaurantTools(self.db)
                query = tool_args.get("query", "美食")
                location = tool_args.get("location")
                region = tool_args.get("region", "成都")
                radius = tool_args.get("radius", 2000)
                limit = tool_args.get("limit", 5)

                if not location and self.latitude and self.longitude:
                    location = f"{self.latitude},{self.longitude}"

                restaurants = await restaurant_tools.search_nearby_restaurants(
                    user_id=context.user_id,
                    query=query,
                    region=region,
                    location=location,
                    radius=radius,
                    limit=limit
                )
                return {"success": True, "restaurants": restaurants, "count": len(restaurants)}

            elif tool_name == "get_restaurant_details":
                from app.tools.restaurant_tools import RestaurantTools
                restaurant_tools = RestaurantTools(self.db)
                uid = tool_args.get("uid")
                name = tool_args.get("name", "")
                if not uid:
                    return {"success": False, "error": "缺少UID"}
                details = await restaurant_tools.get_restaurant_details(uid)
                if not details:
                    return {"success": False, "error": "无法获取详情"}
                return {"success": True, "details": details, "name": name}

            elif tool_name == "get_user_profile":
                profile = self.profile_tools.get_user_profile(context.user_id)
                return {"success": True, "profile": profile}

            elif tool_name == "get_today_meals":
                meals = self.meal_tools.get_today_meals(context.user_id)
                return {"success": True, "meals": meals}

            elif tool_name == "get_user_memories":
                memories = self.memory_tools.get_relevant_memories(context.user_id, limit=10)
                return {"success": True, "memories": memories}

            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"[DietAgentLoop] tool execution error: {tool_name}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _estimate_nutrition(self, food_text: str, profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to estimate nutrition for a meal."""
        llm = get_llm_service()

        prompt = f"""根据以下食物描述，估算营养成分。只返回JSON格式：
{{
  "estimated_calories": 数字(千卡),
  "estimated_protein": 数字(克),
  "estimated_carbs": 数字(克),
  "estimated_fat": 数字(克),
  "confidence": 0到1之间的置信度
}}

食物: {food_text}
"""

        try:
            result = await llm.generate(
                "你是一个营养估算助手，根据食物描述估算热量和宏量营养素。返回JSON格式。",
                prompt
            )
            data = json.loads(result)
            return {
                "estimated_calories": data.get("estimated_calories", 0),
                "estimated_protein": data.get("estimated_protein", 0),
                "estimated_carbs": data.get("estimated_carbs", 0),
                "estimated_fat": data.get("estimated_fat", 0),
                "confidence": data.get("confidence", 0.65)
            }
        except Exception:
            return {
                "estimated_calories": 0,
                "estimated_protein": 0,
                "estimated_carbs": 0,
                "estimated_fat": 0,
                "confidence": 0.5
            }

    async def _parse_profile_update_with_llm(self, message: str) -> Dict[str, Any]:
        """Use LLM to parse profile updates from message."""
        llm = get_llm_service()
        current_weight = None
        if self.user:
            profile = self.profile_tools.get_user_profile(self.user.id)
            if profile:
                current_weight = profile.get("weight_kg")

        prompt = f"""从用户消息中提取要更新的profile字段。

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

        try:
            result = await llm.generate(
                "你是一个profile更新解析助手，从用户消息中提取要更新的字段。返回JSON格式。",
                prompt
            )
            return json.loads(result)
        except Exception:
            return {}

    async def _extract_memory_candidates(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Extract memory candidates from the conversation."""
        llm = get_llm_service()

        # Build context
        context_text = f"用户消息: {context.message}\n"
        if context.profile:
            context_text += f"用户目标: {context.profile.get('primary_goal')}\n"
        if context.memories:
            context_text += f"已有记忆: {[m['content'] for m in context.memories[:5]]}\n"

        prompt = f"""分析用户消息，提取需要长期记忆的信息。返回JSON数组格式：
[{{
  "memory_type": "diet_preference|food_dislike|allergy_intolerance|goal|budget|location|scenario|sleep|body_response|restriction|habit",
  "content": "记忆内容",
  "importance_score": 1-10,
  "confidence_score": 0到1之间
}}]

只提取重要且稳定的信息，不要提取临时状态。
只返回JSON数组，不要其他内容。

上下文:
{context_text}
"""

        try:
            result = await llm.generate(
                "你是一个记忆抽取助手，分析用户消息中需要长期记忆的信息。返回JSON数组格式。",
                prompt
            )
            logger.info(f"[memory] LLM raw result (len={len(result)}): {result[:300]}")

            # Try to find JSON array in response (handles LLM returning text before JSON)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
            else:
                # Fallback: try parsing the whole thing as JSON
                parsed = json.loads(result)

            # Handle both direct array and single-object format
            if isinstance(parsed, list):
                candidates = parsed
            elif isinstance(parsed, dict):
                # Check both snake_case (real API) and camelCase (mock)
                if ("memory_type" in parsed and "content" in parsed) or \
                   ("memoryType" in parsed and "content" in parsed):
                    return [parsed]
                data = parsed.get("data") or parsed.get("memories") or []
                candidates = data if isinstance(data, list) else []
            else:
                candidates = []

            # Normalize camelCase to snake_case for compatibility
            def normalize(item):
                if not isinstance(item, dict):
                    return None
                result = {}
                for k, v in item.items():
                    if k == "memoryType":
                        result["memory_type"] = v
                    elif k == "importanceScore":
                        result["importance_score"] = v
                    elif k == "confidenceScore":
                        result["confidence_score"] = v
                    else:
                        result[k] = v
                return result

            normalized = [normalize(c) for c in candidates]
            logger.info(f"[memory] extracted {len(normalized)} candidates: {normalized}")
            return [c for c in normalized if c is not None]
        except json.JSONDecodeError as e:
            logger.error(f"[memory] JSON parse failed: {e}, result={result[:200]}")
            return []
        except Exception as e:
            logger.error(f"[memory] unexpected error in extraction: {e}", exc_info=True)
            return []

    def _build_advice_context(self, context: AgentContext) -> Dict[str, Any]:
        """Build context dictionary for advice generation."""
        return {
            "profile": context.profile,
            "memories": context.memories,
            "today_meals": context.today_meals,
            "recent_messages": context.recent_messages,
            "message": context.message,
            "intent": context.intent.value
        }

    def _get_system_prompt(self) -> str:
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

    def _build_user_prompt(self, context: Dict[str, Any], message: str) -> str:
        """Build user prompt for LLM."""
        prompt_parts = [f"用户消息: {message}\n"]

        if context.get("profile"):
            p = context["profile"]
            prompt_parts.append(f"\n用户画像:")
            if p.get("primary_goal"):
                prompt_parts.append(f"- 目标: {p['primary_goal']}")
            if p.get("budget_per_meal"):
                prompt_parts.append(f"- 预算: {p['budget_per_meal']}元/餐")
            if p.get("weight_kg"):
                prompt_parts.append(f"- 体重: {p['weight_kg']}kg")
            if p.get("sleep_sensitive"):
                prompt_parts.append(f"- 睡眠敏感")

        if context.get("memories"):
            prompt_parts.append(f"\n用户记忆:")
            for m in context["memories"][:5]:
                prompt_parts.append(f"- [{m['memory_type']}] {m['content']}")

        if context.get("today_meals"):
            total_cal = sum(m.get("estimated_calories", 0) for m in context["today_meals"])
            prompt_parts.append(f"\n今日已记录: {len(context['today_meals'])}餐, 共{total_cal:.0f}千卡")
            for m in context["today_meals"]:
                prompt_parts.append(f"- {m['meal_type']}: {m['food_text']} (~{m.get('estimated_calories', 0):.0f}千卡)")

        if context.get("recent_messages"):
            prompt_parts.append(f"\n当前会话历史:")
            for m in context["recent_messages"]:
                role_display = "用户" if m.get("role") == "user" else "助手"
                content = m.get("content", "")
                # Truncate long messages
                if len(content) > 200:
                    content = content[:200] + "..."
                prompt_parts.append(f"- [{role_display}] {content}")

        return "\n".join(prompt_parts)

    def _format_advice_response(self, response_data: Dict[str, Any], context: AgentContext) -> str:
        """Format LLM response for display."""
        parts = []

        if response_data.get("situation_summary"):
            parts.append(response_data["situation_summary"])

        if response_data.get("one_sentence_summary"):
            parts.append(f"\n💡 {response_data['one_sentence_summary']}")

        if response_data.get("recommended_options"):
            parts.append("\n推荐选项:")
            for i, opt in enumerate(response_data["recommended_options"][:3], 1):
                parts.append(f"{i}. {opt.get('name', 'Unknown')}")
                if opt.get("estimated_calories"):
                    parts.append(f"   约{opt['estimated_calories']}千卡")
                if opt.get("why_recommended"):
                    parts.append(f"   {opt['why_recommended']}")
                if opt.get("order_modification"):
                    parts.append(f"   点餐建议: {opt['order_modification']}")

        if response_data.get("not_recommended"):
            parts.append("\n❌ 建议避免:")
            for opt in response_data["not_recommended"][:2]:
                if isinstance(opt, str):
                    parts.append(f"- {opt}")
                else:
                    parts.append(f"- {opt.get('name', 'Unknown')}: {opt.get('reason', '')}")

        if response_data.get("sleep_friendly_tips"):
            parts.append(f"\n😴 睡眠友好: {response_data['sleep_friendly_tips']}")

        return "\n".join(parts)

    def _generate_meal_log_response(self, parsed: Dict[str, Any], nutrition: Dict[str, Any]) -> str:
        """Generate response for meal logging."""
        food = parsed.get("food_text", "")
        meal_type = parsed.get("meal_type", "SNACK")
        calories = nutrition.get("estimated_calories", 0)

        meal_type_names = {
            "BREAKFAST": "早餐",
            "LUNCH": "午餐",
            "DINNER": "晚餐",
            "SNACK": "零食"
        }

        return f"记录: {food}\n类型: {meal_type_names.get(meal_type, meal_type)}\n估算热量: ~{calories:.0f}千卡 (估算值)"

    def _generate_profile_update_display(self, updates: Dict[str, Any], old_values: Dict[str, Any]) -> str:
        """Generate display text for profile update."""
        field_names = {
            "weight_kg": "体重",
            "budget_per_meal": "预算",
            "gender": "性别",
            "age": "年龄",
            "primary_goal": "目标",
            "height_cm": "身高"
        }

        parts = []
        for field, new_value in updates.items():
            # Skip internal fields
            if field.startswith("_"):
                continue
            old_value = old_values.get(field)
            display_name = field_names.get(field, field)
            if old_value is not None:
                parts.append(f"{display_name}: {old_value} → {new_value}")
            else:
                parts.append(f"{display_name}: {new_value}")

        # If only _weight_delta_text exists (no absolute weight extracted), show delta text
        if not parts and "_weight_delta_text" in updates:
            delta_text = updates["_weight_delta_text"]
            # Get current weight for display
            current_profile = self.profile_tools.get_user_profile(self.user.id)
            current_weight = current_profile.get("weight_kg") if current_profile else None
            if current_weight:
                delta = updates.get("_weight_delta", 0)
                new_weight = round(current_weight + delta, 1)
                parts.append(f"体重: {current_weight}kg → {new_weight}kg ({delta_text})")
            else:
                parts.append(f"体重变化: {delta_text}")

        return ", ".join(parts)

    def _generate_dashboard_response(self, summary: Dict[str, Any], profile: Optional[Dict], meals: List) -> str:
        """Generate response for dashboard query."""
        parts = []

        parts.append(f"今日摄入: {summary['total_calories']:.0f}千卡")
        parts.append(f"蛋白质: {summary['total_protein']:.0f}g, 碳水: {summary['total_carbs']:.0f}g, 脂肪: {summary['total_fat']:.0f}g")
        parts.append(f"共 {summary['meal_count']} 餐")

        if summary.get("meals"):
            parts.append("\n已记录:")
            for m in summary["meals"]:
                parts.append(f"- {m['meal_type']}: {m['food_text']} (~{m.get('estimated_calories', 0):.0f}千卡)")

        if profile and profile.get("primary_goal"):
            goal_map = {"FAT_LOSS": "减脂", "MUSCLE_GAIN": "增肌", "MAINTAIN": "维持"}
            parts.append(f"\n当前目标: {goal_map.get(profile['primary_goal'], profile['primary_goal'])}")

        return "\n".join(parts)

    def is_high_importance_memory(self, memory_type: str) -> bool:
        """Check if a memory type is high importance."""
        return memory_type in MemoryTools.HIGH_IMPORTANCE_TYPES

    def _merge_responses(self, responses: List[Tuple[str, AgentResponse]], context: AgentContext) -> AgentResponse:
        """
        Merge responses from multiple intent handlers.
        Prioritize: memory_action > pending_action > text.
        Text from different handlers is concatenated.
        """
        if not responses:
            return AgentResponse(text="抱歉，处理过程中出现问题。", steps=context.steps)

        # If only one response, return as-is
        if len(responses) == 1:
            return responses[0][1]

        # Collect texts
        texts = []
        pending_action = None
        memory_action = None
        all_steps = []

        for name, resp in responses:
            all_steps.extend(resp.steps)
            if resp.text:
                texts.append(resp.text)
            if resp.action and not pending_action:
                pending_action = resp.action
            if resp.memory_action and not memory_action:
                memory_action = resp.memory_action

        # Merge texts based on handler types
        merged_text = self._merge_texts(texts, responses)

        return AgentResponse(
            text=merged_text,
            action=pending_action,
            memory_action=memory_action,
            steps=all_steps
        )

    def _merge_texts(self, texts: List[str], responses: List[Tuple[str, AgentResponse]]) -> str:
        """Merge texts from multiple handlers with proper formatting."""
        if not texts:
            return ""

        # Remove empty texts
        texts = [t for t in texts if t.strip()]
        if not texts:
            return ""

        if len(texts) == 1:
            return texts[0]

        # For multiple texts, add visual separator for different intent handlers
        merged = []
        for (name, _), text in zip(responses, texts):
            if name == "memory_candidate":
                # Memory confirmation - add emoji prefix
                merged.append(f"📝 {text}")
            elif name == "diet_advice":
                # Diet advice - add section indicator
                if not text.startswith("💡"):
                    merged.append(f"\n💡 {text}")
                else:
                    merged.append(text)
            elif name == "meal_log":
                merged.append(f"🍽️ {text}")
            elif name == "profile_update":
                merged.append(f"👤 {text}")
            else:
                merged.append(text)

        return "\n".join(merged)