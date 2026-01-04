"""Config expert tool collection."""
from __future__ import annotations

from langchain_core.tools import BaseTool

from backend.agents.tools.file_generation import generate_config, generate_samplesheet
from backend.agents.tools.pipeline_tools import get_pipeline_schema, list_pipelines
from backend.agents.tools.workspace_tools import (
    get_current_config,
    get_current_samplesheet,
    get_workspace_status,
)


def get_config_expert_tools() -> list[BaseTool]:
    """Tools for the config_expert subagent (7 tools).

    Categories:
    - Pipeline Info (2): list_pipelines, get_pipeline_schema
    - File Generation (2): generate_samplesheet, generate_config
    - Workspace (3): get_workspace_status, get_current_samplesheet, get_current_config
    """
    return [
        # Pipeline Info
        list_pipelines,
        get_pipeline_schema,
        # File Generation
        generate_samplesheet,
        generate_config,
        # Workspace (shared)
        get_workspace_status,
        get_current_samplesheet,
        get_current_config,
    ]
