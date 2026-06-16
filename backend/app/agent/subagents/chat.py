"""
Chat sub-agent — the ReAct (think-act-observe) loop.

This is the only sub-agent that runs a full ReAct loop:
  1) Build conversation history (system + recent messages + new user message)
  2) Call LLM
  3) If tool_call → execute tool → append result → loop
  4) If direct response → format + return
  5) If max iterations hit → bail with a message

Progressive hint injection (NEAR_LIMIT / TOOL_REMINDER / STUCK) keeps the LLM
on track without being too prescriptive. The loop is bounded by
`max_iterations` (5) so a stuck loop can't burn tokens forever.

Imports from:
  - app.prompts.agent_prompts: get_agent_system_prompt, build_advice_context,
    build_advice_user_prompt, NEAR_LIMIT_HINT, TOOL_REMINDER_HINT, STUCK_HINT,
    EMPTY_SEARCH_RETRY_HINT
  - app.services.llm_service: get_llm_service
  - app.agent.tools.registry: execute_tool
  - app.agent.subagents._shared: add_step
  - app.agent.agent_types: AgentContext, AgentResponse, AgentStep, ReActLoopState
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.agent.agent_types import (
    AgentContext,
    AgentResponse,
    AgentStep,
    ReActLoopState,
)
from app.agent.subagents._shared import add_step
from app.agent.tools.registry import execute_tool

logger = logging.getLogger("eatfit.agent.subagents.chat")


# ---------------------------------------------------------------------------
# Response formatter
# ---------------------------------------------------------------------------

def format_advice_response(response_data: Dict[str, Any], context: AgentContext) -> str:
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


# ---------------------------------------------------------------------------
# Sub-agent entry — ReAct loop
# ---------------------------------------------------------------------------

async def run(context: AgentContext, agent) -> AgentResponse:
    """ReAct loop: think → act → observe → repeat."""
    from app.services.llm_service import get_llm_service
    llm = get_llm_service()

    add_step(context, AgentStep.GENERATING_ADVICE, {})

    from app.prompts.agent_prompts import (
        EMPTY_SEARCH_RETRY_HINT,
        NEAR_LIMIT_HINT,
        STUCK_HINT,
        TOOL_REMINDER_HINT,
        build_advice_context,
        build_advice_user_prompt,
        get_agent_system_prompt,
    )

    conversation_history: List[Dict[str, Any]] = [
        {"role": "system", "content": get_agent_system_prompt()}
    ]
    if context.recent_messages:
        for msg in context.recent_messages[-6:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            content = msg.get("content", "")
            if content:
                conversation_history.append({"role": role, "content": content})

    prompt_context = build_advice_context(context)
    user_prompt = build_advice_user_prompt(prompt_context, context.message)
    conversation_history.append({"role": "user", "content": user_prompt})

    max_iterations = 5
    iteration = 0
    state = ReActLoopState()
    response_text = ""
    response_data: Dict[str, Any] = {"one_sentence_summary": ""}

    def inject_hint() -> None:
        remaining = max_iterations - iteration
        if remaining <= 2 and remaining > 0:
            hint = NEAR_LIMIT_HINT.format(remaining=remaining)
            conversation_history.append({"role": "system", "content": hint})
            add_step(context, AgentStep.REACT_HINT_NEAR_LIMIT, {
                "hint": hint, "remaining": remaining, "iteration": iteration,
            })
        if state.consecutive_no_tool_calls >= 2:
            if state.total_tool_calls == 0:
                conversation_history.append({"role": "system", "content": TOOL_REMINDER_HINT})
                add_step(context, AgentStep.REACT_HINT_TOOL_REMINDER, {
                    "hint": "never_called_tools", "iteration": iteration,
                })
            else:
                hint = STUCK_HINT.format(turns=state.consecutive_no_tool_calls)
                conversation_history.append({"role": "system", "content": hint})
                add_step(context, AgentStep.REACT_HINT_STUCK, {
                    "hint": "stuck_no_tool_calls",
                    "consecutive": state.consecutive_no_tool_calls,
                    "iteration": iteration,
                })

    while iteration < max_iterations:
        iteration += 1
        state.iteration = iteration
        state.reset_turn()

        add_step(context, AgentStep.REACT_CALL_LLM, {
            "iteration": iteration,
            "total_tool_calls": state.total_tool_calls,
            "consecutive_no_tool": state.consecutive_no_tool_calls,
        })
        inject_hint()

        try:
            response_text = await llm.generate_from_history(conversation_history)
            try:
                response_data = json.loads(response_text)
                context.llm_response = response_data
            except json.JSONDecodeError:
                response_data = {"one_sentence_summary": response_text}
                context.llm_response = response_data

            is_tool_call = response_data.get("response_type") == "tool_call" or (
                "tool_name" in response_data and "tool_args" in response_data
            )

            if is_tool_call:
                tool_name = response_data.get("tool_name")
                tool_args = response_data.get("tool_args", {})
                add_step(context, AgentStep.REACT_TOOL_CALL, {
                    "iteration": iteration,
                    "tool_name": tool_name,
                    "tool_args_keys": list(tool_args.keys()) if tool_args else [],
                })

                tool_result = await execute_tool(tool_name, tool_args, context, agent)
                state.record_tool_call(tool_name)

                if not tool_result.get("success", False):
                    state.record_tool_error()
                    error_msg = tool_result.get("error", "unknown error")
                    conversation_history.append({"role": "assistant", "content": json.dumps(response_data, ensure_ascii=False)})
                    conversation_history.append({"role": "system", "content": f"[TOOL ERROR] {tool_name} failed: {error_msg}"})
                    add_step(context, AgentStep.REACT_TOOL_ERROR, {
                        "iteration": iteration, "tool_name": tool_name, "error": error_msg,
                    })
                    continue

                conversation_history.append({"role": "assistant", "content": json.dumps(response_data, ensure_ascii=False)})
                conversation_history.append({"role": "system", "content": f"[Tool Result for {tool_name}]: {json.dumps(tool_result, ensure_ascii=False)}"})
                add_step(context, AgentStep.REACT_TOOL_RESULT, {
                    "iteration": iteration,
                    "tool_name": tool_name,
                    "success": True,
                    "result_count": len(tool_result.get("restaurants", [])) if tool_name == "map_search_places" else None,
                })

                if tool_name == "map_search_places" and tool_result.get("restaurants") == []:
                    conversation_history.append({"role": "system", "content": EMPTY_SEARCH_RETRY_HINT})
                    add_step(context, AgentStep.REACT_HINT_PROGRESS, {
                        "hint": "retry_search", "reason": "empty_results", "iteration": iteration,
                    })
                    continue
                continue

            add_step(context, AgentStep.REACT_DIRECT_RESPONSE, {
                "iteration": iteration, "preview": response_text[:80] if response_text else "",
            })
            state.record_no_tool_call()
            break

        except Exception as e:
            logger.error(f"[ReAct loop] iteration {iteration} error: {e}", exc_info=True)
            state.record_llm_error()
            return AgentResponse(
                text=f"处理请求时出错: {str(e)[:100]}",
                steps=context.steps,
            )

    if iteration >= max_iterations:
        add_step(context, AgentStep.REACT_MAX_ITERATIONS, {
            "total_iterations": iteration,
            "total_tool_calls": state.total_tool_calls,
            "tool_errors": state.tool_errors,
            "preview": response_text[:100] if response_text else "no response",
        })
        return AgentResponse(
            text="已达最大对话轮次（5轮），请尝试简化问题或重新开始。",
            steps=context.steps,
        )

    add_step(context, AgentStep.FINAL_RESPONSE, {
        "iteration": iteration,
        "total_tool_calls": state.total_tool_calls,
        "preview": response_text[:100] if response_text else "no response",
    })
    return AgentResponse(
        text=format_advice_response(response_data, context),
        steps=context.steps,
    )
