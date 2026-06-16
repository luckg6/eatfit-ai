"""
Profile-update sub-agent.

Owns the profile_update intent: extract field updates → return pending action
for user confirmation. Falls back to LLM-based parsing when regex extraction
finds nothing.

Imports from:
  - app.prompts.agent_prompts: PROFILE_UPDATE_PARSE_SYSTEM, build_profile_update_parse_prompt, PROFILE_FIELD_NAMES
  - app.services.llm_service: get_llm_service
  - app.agent.intent_classifier: Intent, extract_entities
  - app.agent.subagents._shared: add_step
  - app.agent.agent_types: AgentContext, AgentResponse, AgentStep
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.agent.agent_types import AgentContext, AgentResponse, AgentStep
from app.agent.intent_classifier import Intent, extract_entities
from app.agent.subagents._shared import add_step

logger = logging.getLogger("eatfit.agent.subagents.profile")


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

async def parse_profile_update_with_llm(message: str, profile_tools, user_id: int) -> Dict[str, Any]:
    """Use LLM to parse profile updates from message."""
    from app.services.llm_service import get_llm_service
    llm = get_llm_service()
    current_weight = None
    if user_id:
        profile = profile_tools.get_user_profile(user_id)
        if profile:
            current_weight = profile.get("weight_kg")
    from app.prompts.agent_prompts import PROFILE_UPDATE_PARSE_SYSTEM
    try:
        result = await llm.generate(
            PROFILE_UPDATE_PARSE_SYSTEM,
            build_profile_update_parse_prompt(message, current_weight),
        )
        return json.loads(result)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Response formatter
# ---------------------------------------------------------------------------

def generate_profile_update_display(
    updates: Dict[str, Any],
    old_values: Dict[str, Any],
    profile_tools,
    user_id: int,
) -> str:
    from app.prompts.agent_prompts import PROFILE_FIELD_NAMES
    parts = []
    for field, new_value in updates.items():
        if field.startswith("_"):
            continue
        old_value = old_values.get(field)
        display_name = PROFILE_FIELD_NAMES.get(field, field)
        if old_value is not None:
            parts.append(f"{display_name}: {old_value} → {new_value}")
        else:
            parts.append(f"{display_name}: {new_value}")

    if not parts and "_weight_delta_text" in updates:
        delta_text = updates["_weight_delta_text"]
        current_profile = profile_tools.get_user_profile(user_id) if user_id else None
        current_weight = current_profile.get("weight_kg") if current_profile else None
        if current_weight:
            delta = updates.get("_weight_delta", 0)
            new_weight = round(current_weight + delta, 1)
            parts.append(f"体重: {current_weight}kg → {new_weight}kg ({delta_text})")
        else:
            parts.append(f"体重变化: {delta_text}")

    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Sub-agent entry
# ---------------------------------------------------------------------------

async def run(context: AgentContext, agent) -> AgentResponse:
    """Sub-agent entry: extract entities → build pending action."""
    add_step(context, AgentStep.PARSING_PROFILE_UPDATE, {"message": context.message})

    entities = extract_entities(context.message, context.intent)
    if not entities:
        entities = await parse_profile_update_with_llm(
            context.message,
            agent.profile_tools,
            agent.user.id if agent.user else None,
        )
    if not entities:
        return AgentResponse(
            text="抱歉，我没有理解你想更新的资料。能再说明一下吗？",
            steps=context.steps,
        )

    current_profile = agent.profile_tools.get_user_profile(context.user_id)
    old_values = {k: current_profile[k] for k in entities if current_profile and k in current_profile}

    if "_weight_delta" in entities and "weight_kg" not in entities:
        current_weight = current_profile.get("weight_kg") if current_profile else None
        if current_weight is not None:
            entities["weight_kg"] = round(current_weight + entities["_weight_delta"], 1)
        entities.pop("_weight_delta", None)
        entities.pop("_weight_delta_text", None)

    action_data = {
        "action_type": "profile_update",
        "action_status": "pending",
        "action_data": {
            "updates": entities,
            "old_values": old_values,
            "display_text": generate_profile_update_display(
                entities, old_values, agent.profile_tools, agent.user.id if agent.user else None,
            ),
        },
    }
    add_step(context, AgentStep.CREATING_PENDING_ACTION, {
        "action_type": "profile_update",
        "updates": entities,
    })

    return AgentResponse(
        text=f"检测到你想更新: {generate_profile_update_display(entities, old_values, agent.profile_tools, agent.user.id if agent.user else None)}",
        action=action_data,
        steps=context.steps,
    )
