from __future__ import annotations

import warnings

from langchain_core.tools import BaseTool

from .collections import (
    get_benchling_expert_tools,
    get_config_expert_tools,
    get_execution_expert_tools,
    get_orchestrator_tools,
)

from .benchling_discovery import get_entities, get_entry_content, get_entry_entities, list_entries
from .entity_tools import (
    find_sample_descendants,
    get_entity_relationships,
    trace_sample_lineage,
)
from .ngs_discovery import (
    get_fastq_paths,
    get_ngs_run_qc,
    get_ngs_run_samples,
    search_ngs_runs,
)
from .pipeline_tools import get_pipeline_schema, list_pipelines
from .schema_tools import (
    execute_warehouse_query,
    get_dropdown_values,
    get_schema_field_info,
    get_schemas,
    list_projects,
)
from .submission import cancel_run, clear_samplesheet, delete_file, recover_run, submit_run
from .monitoring_tools import get_run_status, get_run_tasks, list_user_runs
from .troubleshooting_tools import analyze_failure, get_run_logs, get_task_logs
from .output_tools import get_run_outputs, get_signed_download_url
from .file_generation import generate_config, generate_samplesheet, validate_inputs
from .workspace_tools import (
    get_current_config,
    get_current_samplesheet,
    get_workspace_status,
    update_config,
    update_samplesheet,
)

NGS_TOOL_CATEGORY = "ngs"
BENCHLING_TOOL_CATEGORY = "benchling"
SCHEMA_TOOL_CATEGORY = "schema"


def get_agent_tools() -> list[BaseTool]:
    """Get all agent tools (DEPRECATED).

    .. deprecated::
        Use tool collections from `backend.agents.tools.collections` instead.
        This function returns all 30 tools for backwards compatibility only.
    """
    warnings.warn(
        "get_agent_tools() is deprecated. Use tool collections from "
        "backend.agents.tools.collections instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return [
        search_ngs_runs,
        get_ngs_run_samples,
        get_ngs_run_qc,
        get_fastq_paths,
        list_pipelines,
        get_pipeline_schema,
        generate_samplesheet,
        generate_config,
        validate_inputs,
        get_current_samplesheet,
        get_current_config,
        get_workspace_status,
        update_samplesheet,
        update_config,
        submit_run,
        cancel_run,
        delete_file,
        clear_samplesheet,
        get_entities,
        get_entity_relationships,
        trace_sample_lineage,
        find_sample_descendants,
        list_entries,
        get_entry_content,
        get_entry_entities,
        get_schemas,
        get_schema_field_info,
        get_dropdown_values,
        list_projects,
        execute_warehouse_query,
    ]


__all__ = [
    "BENCHLING_TOOL_CATEGORY",
    "NGS_TOOL_CATEGORY",
    "SCHEMA_TOOL_CATEGORY",
    "get_agent_tools",
    "get_benchling_expert_tools",
    "get_config_expert_tools",
    "get_execution_expert_tools",
    "get_orchestrator_tools",
    "get_run_status",
    "get_run_tasks",
    "list_user_runs",
    "get_run_logs",
    "get_task_logs",
    "analyze_failure",
    "get_run_outputs",
    "get_signed_download_url",
    "recover_run",
    "update_samplesheet",
    "update_config",
]
