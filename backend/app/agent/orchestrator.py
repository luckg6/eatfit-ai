"""
Orchestrator — the ReAct coordinator.

Owns one chat turn end-to-end:

  1) Intent detection (multi-intent, rule + optional LLM fallback)
  2) Context load (profile / memories / today's meals / recent chat)
  3) Sub-agent dispatch by Intent (in priority order)
  4) Response merge across sub-agents (when multiple intents match)

Each concrete step lives in its own module:
  - intent_classifier.py : rule-based + LLM intent detection
  - agent_types.py       : AgentContext / AgentResponse / AgentStep / ReActLoopState
  - subagents/           : one module per Intent (chat, meal_log, profile,
                           memory, dashboard, restaurant)
  - tools/registry.py    : ReAct tool dispatch table

To add a new intent: add an enum value, write a subagent in subagents/, register
it in DISPATCH below. Nothing else needs to change in this file.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.agent.agent_types import AgentContext, AgentResponse, AgentStep
from app.agent.intent_classifier import Intent, classify_multi
from app.agent.subagents._shared import add_step
from app.agent.subagents import chat as chat_subagent
from app.agent.subagents import (
    dashboard as dashboard_subagent,
    meal_log as meal_log_subagent,
    memory as memory_subagent,
    profile as profile_subagent,
    restaurant as restaurant_subagent,
)
from app.tools.chat_tools import ChatTools
from app.tools.meal_tools import MealTools
from app.tools.memory_tools import MemoryTools
from app.tools.profile_tools import ProfileTools
from app.tools.restaurant_tools import RestaurantTools

logger = logging.getLogger("eatfit.agent")

# Intent -> (trace name, sub-agent module)
DISPATCH: Dict[Intent, Tuple[str, Any]] = {
    Intent.MEAL_LOG: ("meal_log", meal_log_subagent),
    Intent.PROFILE_UPDATE: ("profile_update", profile_subagent),
    Intent.MEMORY_CANDIDATE: ("memory_candidate", memory_subagent),
    Intent.DASHBOARD_QUERY: ("dashboard_query", dashboard_subagent),
    Intent.RESTAURANT_SEARCH_PLANNED: ("restaurant", restaurant_subagent),
}

# Minimum confidence to count a multi-intent match as actionable.
PRIMARY_INTENT_THRESHOLD = 0.6


# ---------------------------------------------------------------------------
# Response merge (only used by the orchestrator)
# ---------------------------------------------------------------------------

def merge_responses(responses: List[Tuple[str, AgentResponse]], context: AgentContext) -> AgentResponse:
    if not responses:
        return AgentResponse(text="抱歉，处理过程中出现问题。", steps=context.steps)
    if len(responses) == 1:
        return responses[0][1]

    texts: List[str] = []
    pending_action = None
    memory_action = None
    all_steps: List[Dict[str, Any]] = []
    for name, resp in responses:
        all_steps.extend(resp.steps)
        if resp.text:
            texts.append(resp.text)
        if resp.action and not pending_action:
            pending_action = resp.action
        if resp.memory_action and not memory_action:
            memory_action = resp.memory_action

    merged_text = _merge_texts(texts, responses)
    return AgentResponse(
        text=merged_text,
        action=pending_action,
        memory_action=memory_action,
        steps=all_steps,
    )


def _merge_texts(texts: List[str], responses: List[Tuple[str, AgentResponse]]) -> str:
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        return ""
    if len(texts) == 1:
        return texts[0]

    merged = []
    for (name, _), text in zip(responses, texts):
        if name == "memory_candidate":
            merged.append(f"📝 {text}")
        elif name == "meal_log":
            merged.append(f"🍽️ {text}")
        elif name == "profile_update":
            merged.append(f"👤 {text}")
        else:
            merged.append(text)
    return "\n".join(merged)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """Main agent loop coordinator.

    Composes the tool bundles (profile/memory/meal/chat/restaurant) with
    per-intent sub-agents from subagents/.
    """

    def __init__(
        self,
        db: Session,
        user: Any,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ):
        self.db = db
        self.user = user
        self.latitude = latitude
        self.longitude = longitude
        self.profile_tools = ProfileTools(db)
        self.memory_tools = MemoryTools(db)
        self.meal_tools = MealTools(db)
        self.chat_tools = ChatTools(db)
        self.restaurant_tools = RestaurantTools(db)

    # ---- Public entry point ------------------------------------------------

    async def run(self, message: str, session_id: int) -> AgentResponse:
        """Run the orchestrator on a user message.

        Returns the agent response with potential pending actions.
        """
        context = AgentContext(
            user_id=self.user.id, session_id=session_id, message=message,
        )

        # 1) Multi-intent detection
        multi_results = classify_multi(message)
        context.intents = multi_results

        if multi_results:
            primary_intent, primary_confidence, reasoning = multi_results[0]
            context.intent = primary_intent
            context.intent_confidence = primary_confidence
            logger.info(
                f"[agent] Multi-intent detected: {[(i[0].value, i[1]) for i in multi_results]}"
            )
            logger.info(
                f"[agent] Primary intent: {primary_intent.value} "
                f"(confidence={primary_confidence}), reasoning: {reasoning}"
            )
            add_step(context, AgentStep.INTENT_DETECTED, {
                "intents": [(i[0].value, i[1], i[2]) for i in multi_results],
                "primary_intent": primary_intent.value,
                "confidence": primary_confidence,
                "reasoning": reasoning,
            })
        else:
            context.intent = Intent.GENERAL_CHAT
            context.intent_confidence = 0.3
            logger.info("[agent] No rule match, defaulting to general_chat")
            add_step(context, AgentStep.INTENT_DETECTED, {
                "intents": [],
                "primary_intent": Intent.GENERAL_CHAT.value,
                "confidence": 0.3,
                "reasoning": "No rule pattern matched",
            })

        # 2) Load context (always — even general_chat uses profile/memories/meals)
        self._load_context(context)

        # 3) Dispatch intent handlers (in priority order, all with conf >= threshold)
        primary_intents = [
            (i, c, r) for i, c, r in multi_results
            if c >= PRIMARY_INTENT_THRESHOLD
        ] if multi_results else []

        subagents_to_run: List[Tuple[str, Any]] = []
        for intent, _confidence, _reasoning in primary_intents:
            entry = DISPATCH.get(intent)
            if entry is None:
                continue
            handler_name, subagent_module = entry
            subagents_to_run.append((handler_name, subagent_module.run(context, self)))

        if not subagents_to_run:
            return await chat_subagent.run(context, self)

        # 4) Execute + merge
        responses: List[Tuple[str, AgentResponse]] = []
        for name, coro in subagents_to_run:
            try:
                resp = await coro
                responses.append((name, resp))
            except Exception as e:
                logger.error(f"[agent] Sub-agent {name} failed: {e}", exc_info=True)

        return merge_responses(responses, context)

    # ---- Internals ---------------------------------------------------------

    def _load_context(self, context: AgentContext) -> None:
        context.profile = self.profile_tools.get_user_profile(self.user.id)
        add_step(context, AgentStep.LOADING_PROFILE, {"loaded": context.profile is not None})

        context.memories = self.memory_tools.get_relevant_memories(
            self.user.id, context.intent.value, limit=10,
            query_text=context.message,
        )
        add_step(context, AgentStep.LOADING_MEMORIES, {
            "count": len(context.memories),
            "types": [m["memory_type"] for m in context.memories],
        })

        context.today_meals = self.meal_tools.get_today_meals(self.user.id)
        add_step(context, AgentStep.LOADING_TODAY_MEALS, {
            "meal_count": len(context.today_meals),
            "total_calories": sum(m.get("estimated_calories", 0) for m in context.today_meals),
        })

        context.recent_messages = self.chat_tools.get_recent_messages(
            context.session_id, self.user.id, limit=10,
        )
        add_step(context, AgentStep.LOADING_RECENT_CHAT, {"count": len(context.recent_messages)})
