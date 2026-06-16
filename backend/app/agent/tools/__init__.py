"""
Tool registry module.

Public surface:
  - execute_tool: dispatch a tool call by name
  - TOOL_REGISTRY: name -> handler mapping (read-only; use this for introspection)
"""
from app.agent.tools.registry import TOOL_REGISTRY, execute_tool

__all__ = ["execute_tool", "TOOL_REGISTRY"]
