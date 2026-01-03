from __future__ import annotations

from typing import Any

from backend.agents.model import get_chat_model
from backend.agents.prompts import PIPELINE_AGENT_SYSTEM_PROMPT
from backend.agents.subagents import create_benchling_expert, create_config_expert
from backend.agents.tools import get_agent_tools
from backend.agents.middleware.hitl import build_hitl_middleware
from langchain.agents.middleware import TodoListMiddleware

from backend.agents.middleware.large_output import LargeOutputMiddleware
from backend.agents.middleware.summarization import SummarizationMiddleware

try:
    from deepagents import create_deep_agent
except ImportError as exc:  # pragma: no cover - optional dependency until installed
    create_deep_agent = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _ensure_available() -> None:
    if _IMPORT_ERROR is not None:
        raise RuntimeError("DeepAgents is not available") from _IMPORT_ERROR


class PipelineAgent:
    def __init__(self, agent: Any, model: Any, tools: list[Any]) -> None:
        self.agent = agent
        self.model = model
        self.tools = tools

    @classmethod
    def create(
        cls,
        settings: object,
        *,
        tools: list[Any] | None = None,
        checkpointer: Any | None = None,
    ) -> "PipelineAgent":
        _ensure_available()
        tool_list = tools if tools is not None else get_agent_tools()
        model = get_chat_model(settings)
        subagents = [
            create_benchling_expert(model),
            create_config_expert(model),
        ]
        middleware = [
            build_hitl_middleware(),
        ]
        agent = create_deep_agent(
            model=model,
            tools=tool_list,
            system_prompt=PIPELINE_AGENT_SYSTEM_PROMPT,
            checkpointer=checkpointer,
            middleware=middleware,
            subagents=subagents,
        )
        return cls(agent=agent, model=model, tools=tool_list)
