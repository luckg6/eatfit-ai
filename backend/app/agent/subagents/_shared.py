"""
Shared utilities for sub-agents.

These are imported by every sub-agent module:
  - add_step:  appends a trace step onto context.steps (used by all sub-agents
               and the orchestrator)
  - _now_iso:  ISO timestamp helper (only used by add_step)

Per-agent helpers (response formatters, LLM helpers, intent-specific logic)
live in the sub-agent module itself. Merge logic (merge_responses / merge_texts)
lives in orchestrator.py since only the orchestrator invokes it.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.agent.agent_types import AgentContext, AgentStep


def add_step(context: AgentContext, step: AgentStep, data: Dict[str, Any]) -> None:
    context.steps.append({
        "step": step.value,
        "data": data,
        "timestamp": _now_iso(),
    })


def _now_iso() -> str:
    return datetime.now().isoformat()
