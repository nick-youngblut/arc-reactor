from __future__ import annotations

from typing import Any

from backend.agents.middleware.hitl import build_hitl_interrupt_map
from backend.agents.model import create_agent_model, get_agent_config
from backend.agents.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from backend.agents.subagents import (
    create_benchling_expert,
    create_config_expert,
    create_execution_expert,
)
from backend.agents.tools.collections.workspace import get_orchestrator_tools

try:
    from deepagents import create_deep_agent
except ImportError as exc:  # pragma: no cover - optional dependency until installed
    create_deep_agent = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _ensure_available() -> None:
    """Raise if DeepAgents dependency is unavailable."""
    if _IMPORT_ERROR is not None:
        raise RuntimeError("DeepAgents is not available") from _IMPORT_ERROR


class PipelineAgent:
    """Orchestrator agent that delegates to specialized subagents."""

    def __init__(self, agent: Any, model: Any, tools: list[Any]) -> None:
        self.agent = agent
        self.model = model
        self.tools = tools

    @classmethod
    def create(
        cls,
        settings: object,
        *,
        checkpointer: Any | None = None,
    ) -> "PipelineAgent":
        """Create the pipeline orchestrator agent.

        Args:
            settings: Dynaconf settings object
            checkpointer: Optional LangGraph checkpointer for state persistence

        Returns:
            Configured PipelineAgent instance
        """
        _ensure_available()
        config = get_agent_config(settings, "orchestrator")
        model = create_agent_model(config)
        orchestrator_tools = get_orchestrator_tools()
        subagents = [
            create_benchling_expert(settings),
            create_config_expert(settings),
            create_execution_expert(settings),
        ]
        interrupt_on = build_hitl_interrupt_map()
        agent = create_deep_agent(
            model=model,
            tools=orchestrator_tools,
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT.strip(),
            checkpointer=checkpointer,
            subagents=subagents,
            interrupt_on=interrupt_on,
        )
        return cls(agent=agent, model=model, tools=orchestrator_tools)
