"""
Agent module for EatFit - contains intent classification and diet agent loop.
"""

from app.agent.intent_classifier import Intent, IntentResult, classify, extract_entities
from app.agent.diet_agent_loop import DietAgentLoop, AgentContext, AgentResponse, AgentStep

__all__ = [
    "Intent",
    "IntentResult",
    "classify",
    "extract_entities",
    "DietAgentLoop",
    "AgentContext",
    "AgentResponse",
    "AgentStep",
]