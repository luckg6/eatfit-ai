"""
Sub-agents — one module per Intent.

Each sub-agent exposes a single `async def run(context, agent) -> AgentResponse`
entry point. The orchestrator dispatches to the right sub-agent based on the
detected Intent.

Modules:
  - chat        : ReAct loop for general chat / advice (the only LLM-driven
                  sub-agent with tool calling + hint injection)
  - meal_log    : parse meal text → pending meal_log action
  - profile     : extract profile fields → pending profile_update action
  - memory      : extract memory candidates → auto-save or pending confirm
  - dashboard   : aggregate today's meals → snapshot
  - restaurant  : nearby search OR detail lookup with LLM analysis
"""
from app.agent.subagents import chat, dashboard, meal_log, memory, profile, restaurant

__all__ = [
    "chat",
    "meal_log",
    "profile",
    "memory",
    "dashboard",
    "restaurant",
]
