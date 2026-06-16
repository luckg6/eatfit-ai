"""
Memory-candidate sub-agent.

Owns the memory_candidate intent: extract memory candidates from the message →
either auto-save (low importance) or surface as confirm action (high importance).

If extraction fails or returns an invalid candidate, falls through to the
chat sub-agent (which has full ReAct + history context to produce advice).

Imports from:
  - app.prompts.agent_prompts: MEMORY_EXTRACTION_SYSTEM, build_memory_extraction_prompt
  - app.services.llm_service: get_llm_service
  - app.agent.subagents._shared: add_step
  - app.agent.subagents.chat: run as chat (fallback)
  - app.agent.agent_types: AgentContext, AgentResponse, AgentStep
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from app.agent.agent_types import AgentContext, AgentResponse, AgentStep
from app.agent.subagents._shared import add_step

logger = logging.getLogger("eatfit.agent.subagents.memory")


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

async def extract_memory_candidates(context: AgentContext) -> List[Dict[str, Any]]:
    """Extract memory candidates from the conversation."""
    from app.services.llm_service import get_llm_service
    llm = get_llm_service()
    from app.prompts.agent_prompts import MEMORY_EXTRACTION_SYSTEM
    try:
        result = await llm.generate(MEMORY_EXTRACTION_SYSTEM, build_memory_extraction_prompt(context))
        logger.info(f"[memory] LLM raw result (len={len(result)}): {result[:300]}")

        # Tolerate LLM wrapping the JSON array in prose
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        parsed = json.loads(json_match.group() if json_match else result)

        if isinstance(parsed, list):
            candidates = parsed
        elif isinstance(parsed, dict):
            if ("memory_type" in parsed and "content" in parsed) or \
               ("memoryType" in parsed and "content" in parsed):
                candidates = [parsed]
            else:
                data = parsed.get("data") or parsed.get("memories") or []
                candidates = data if isinstance(data, list) else []
        else:
            candidates = []

        def normalize(item):
            if not isinstance(item, dict):
                return None
            out = {}
            for k, v in item.items():
                if k == "memoryType":
                    out["memory_type"] = v
                elif k == "importanceScore":
                    out["importance_score"] = v
                elif k == "confidenceScore":
                    out["confidence_score"] = v
                else:
                    out[k] = v
            return out

        normalized = [normalize(c) for c in candidates]
        logger.info(f"[memory] extracted {len(normalized)} candidates: {normalized}")
        return [c for c in normalized if c is not None]
    except json.JSONDecodeError as e:
        logger.error(f"[memory] JSON parse failed: {e}, result={result[:200]}")
        return []
    except Exception as e:
        logger.error(f"[memory] unexpected error in extraction: {e}", exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Sub-agent entry
# ---------------------------------------------------------------------------

async def run(context: AgentContext, agent) -> AgentResponse:
    """Sub-agent entry: extract memory candidates → save or surface confirm action."""
    # Local import to break circular: subagents/chat.py may also import nothing
    # from here, but if future refactor adds shared deps this avoids cycles.
    from app.agent.subagents import chat as chat_subagent

    logger.info(f"[memory] ========== handle_memory_candidate ENTERED ==========")
    logger.info(f"[memory] message={context.message}")
    add_step(context, AgentStep.EXTRACTING_MEMORIES, {"message": context.message})

    memory_candidates = await extract_memory_candidates(context)
    logger.info(f"[memory] extract_memory_candidates returned: {type(memory_candidates)} len={len(memory_candidates) if memory_candidates else 0}")

    if not memory_candidates:
        logger.warning(f"[memory] no candidates extracted, falling through to general_chat")
        return await chat_subagent.run(context, agent)

    top_candidate = memory_candidates[0]
    logger.info(f"[memory] top_candidate={top_candidate}")
    if not isinstance(top_candidate, dict) or "memory_type" not in top_candidate or "content" not in top_candidate:
        logger.warning(f"[memory] invalid candidate structure, falling through to general_chat")
        return await chat_subagent.run(context, agent)

    is_high_importance = agent.memory_tools.HIGH_IMPORTANCE_TYPES and top_candidate["memory_type"] in agent.memory_tools.HIGH_IMPORTANCE_TYPES
    logger.info(f"[memory] memory_type={top_candidate['memory_type']}, is_high_importance={is_high_importance}")

    if is_high_importance:
        memory_action = agent.memory_tools.create_pending_memory(
            user_id=context.user_id,
            memory_type=top_candidate["memory_type"],
            content=top_candidate["content"],
            importance_score=top_candidate.get("importance_score", 5),
            confidence_score=top_candidate.get("confidence_score", 0.8),
        )
        return AgentResponse(
            text=memory_action["display_text"],
            memory_action=memory_action,
            steps=context.steps,
        )

    # Auto-save low-risk preferences
    try:
        created = agent.memory_tools.create_memory(
            user_id=context.user_id,
            memory_type=top_candidate["memory_type"],
            content=top_candidate["content"],
            importance_score=top_candidate.get("importance_score", 3),
            source="auto_extracted",
        )
        add_step(context, AgentStep.MEMORY_SAVED, {
            "memory_id": created.id if created else None,
            "memory_type": top_candidate["memory_type"],
            "content": top_candidate["content"],
            "success": created is not None,
        })
        logger.info(f"[memory] auto-saved: user_id={context.user_id}, type={top_candidate['memory_type']}, content={top_candidate['content']}, memory_id={created.id if created else 'NONE'}")
    except Exception as e:
        logger.error(f"[memory] auto-save failed: {e}", exc_info=True)
        add_step(context, AgentStep.MEMORY_SAVED, {
            "error": str(e),
            "memory_type": top_candidate["memory_type"],
            "content": top_candidate["content"],
            "success": False,
        })

    return AgentResponse(
        text=f"已记住: {top_candidate['content']}",
        steps=context.steps,
    )
