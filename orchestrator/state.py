"""Shared state passed between nodes in the orchestrator's LangGraph graph."""

from typing import TypedDict, Optional, Any


class AgentState(TypedDict, total=False):
    request: str                 # raw user request text
    intent: str                  # classified intent
    target_function: Optional[str]   # e.g. "orders.create_order"
    repo_path: str
    retry_count: int
    output: dict[str, Any]       # accumulated results, keyed by agent name
    error: Optional[str]
