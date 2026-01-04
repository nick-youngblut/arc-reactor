"""Orchestrator tool collection (workspace tools only)."""
from __future__ import annotations

from langchain_core.tools import BaseTool

from backend.agents.tools.workspace_tools import (
    get_current_config,
    get_current_samplesheet,
    get_workspace_status,
)


def get_orchestrator_tools() -> list[BaseTool]:
    """Tools for the orchestrator/main agent (3 tools).

    The orchestrator has minimal tools - it delegates specialized work
    to subagents via the `task` tool (built into DeepAgents).

    Workspace tools are shared so the orchestrator can check current
    state before deciding which subagent to delegate to.
    """
    return [
        get_workspace_status,
        get_current_samplesheet,
        get_current_config,
    ]
