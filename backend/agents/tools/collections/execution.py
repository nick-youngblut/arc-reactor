"""Execution expert tool collection."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from backend.agents.tools.file_generation import validate_inputs
from backend.agents.tools.submission import (
    cancel_run,
    clear_samplesheet,
    delete_file,
    recover_run,
    submit_run,
)
from backend.agents.tools.workspace_tools import (
    get_current_config,
    get_current_samplesheet,
    get_workspace_status,
)


# New tools added in Phase 4
from backend.agents.tools.monitoring_tools import (
    get_run_status,
    get_run_tasks,
    list_user_runs,
)
from backend.agents.tools.troubleshooting_tools import (
    analyze_failure,
    get_run_logs,
    get_task_logs,
)
from backend.agents.tools.output_tools import (
    get_run_outputs,
    get_signed_download_url,
)


def get_execution_expert_tools() -> list[BaseTool]:
    """Tools for the execution_expert subagent (15 tools after Phase 4).

    Categories:
    - Validation (1): validate_inputs
    - Execution HITL (3): submit_run, cancel_run, recover_run
    - Monitoring NEW (3): get_run_status, get_run_tasks, list_user_runs
    - Troubleshooting NEW (3): get_run_logs, get_task_logs, analyze_failure
    - Outputs NEW (2): get_run_outputs, get_signed_download_url
    - Cleanup HITL (2): delete_file, clear_samplesheet
    - Workspace (3): get_workspace_status, get_current_samplesheet, get_current_config
    """
    tools = [
        # Validation
        validate_inputs,
        # Execution (HITL)
        submit_run,
        cancel_run,
        recover_run,
        # Cleanup (HITL)
        delete_file,
        clear_samplesheet,
        # Workspace (shared)
        get_workspace_status,
        get_current_samplesheet,
        get_current_config,
        # Monitoring
        get_run_status,
        get_run_tasks,
        list_user_runs,
        # Troubleshooting
        get_run_logs,
        get_task_logs,
        analyze_failure,
        # Outputs
        get_run_outputs,
        get_signed_download_url,
    ]

    return tools
