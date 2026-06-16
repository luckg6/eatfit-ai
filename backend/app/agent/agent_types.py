"""
Agent state types — dataclasses shared across the ReAct loop, handlers, and tool executor.

Kept in their own module so subagents/ / tools/registry / orchestrator
can all import without dragging in the LLM/prompt deps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.agent.intent_classifier import Intent


class AgentStep(Enum):
    """Agent execution steps surfaced to the frontend trace panel."""
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
    # ReAct loop specific steps
    REACT_CALL_LLM = "react_call_llm"
    REACT_TOOL_CALL = "react_tool_call"
    REACT_TOOL_RESULT = "react_tool_result"
    REACT_TOOL_ERROR = "react_tool_error"
    REACT_DIRECT_RESPONSE = "react_direct_response"
    REACT_MAX_ITERATIONS = "react_max_iterations"
    REACT_HINT_PROGRESS = "react_hint_progress"
    REACT_HINT_TOOL_REMINDER = "react_hint_tool_reminder"
    REACT_HINT_NEAR_LIMIT = "react_hint_near_limit"
    REACT_HINT_STUCK = "react_hint_stuck"


@dataclass
class ReActLoopState:
    """Tracks state across ReAct loop iterations for progressive hint injection."""
    iteration: int = 0
    tool_calls_this_turn: int = 0
    consecutive_no_tool_calls: int = 0
    total_tool_calls: int = 0
    last_tool_name: Optional[str] = None
    tool_errors: int = 0
    llm_errors: int = 0

    def record_tool_call(self, tool_name: str) -> None:
        self.tool_calls_this_turn += 1
        self.total_tool_calls += 1
        self.consecutive_no_tool_calls = 0
        self.last_tool_name = tool_name

    def record_no_tool_call(self) -> None:
        self.consecutive_no_tool_calls += 1

    def record_tool_error(self) -> None:
        self.tool_errors += 1

    def record_llm_error(self) -> None:
        self.llm_errors += 1

    def reset_turn(self) -> None:
        self.tool_calls_this_turn = 0


@dataclass
class AgentContext:
    """Context passed through the agent loop."""
    user_id: int
    session_id: int
    message: str
    intent: Intent = Intent.GENERAL_CHAT
    intent_confidence: float = 0.5
    intents: List[Tuple[Intent, float, str]] = field(default_factory=list)
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
    """Response from an intent handler."""
    text: str
    action: Optional[Dict[str, Any]] = None          # pending action to confirm
    memory_action: Optional[Dict[str, Any]] = None   # memory confirm action
    steps: List[Dict[str, Any]] = field(default_factory=list)
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
