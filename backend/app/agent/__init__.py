"""
Agent module for EatFit.

Public surface — the only thing callers should need to import from `app.agent`:

    from app.agent import (
        Orchestrator,         # the ReAct coordinator
        AgentContext,         # mutable per-turn state
        AgentResponse,        # sub-agent output
        AgentStep,            # trace step enum
        Intent,               # intent enum
        IntentResult,         # rule-based classifier output
        classify,             # sync rule-based intent classifier
        extract_entities,     # regex entity extraction per intent
        classify_with_llm,    # async LLM-based intent classifier (with context)
    )

Internal modules (agent_types, intent_classifier internals, subagents/,
tools/, orchestrator) are imported by orchestrator / sub-agents and should not
be touched directly by callers.
"""
from app.agent.agent_types import (
    AgentContext,
    AgentResponse,
    AgentStep,
    ReActLoopState,
)
from app.agent.intent_classifier import (
    Intent,
    IntentResult,
    classify,
    classify_with_llm,
    extract_entities,
)
from app.agent.orchestrator import Orchestrator

__all__ = [
    # Orchestrator + types
    "Orchestrator",
    "AgentContext",
    "AgentResponse",
    "AgentStep",
    "ReActLoopState",
    # Intent classification
    "Intent",
    "IntentResult",
    "classify",
    "classify_with_llm",
    "extract_entities",
]
