from __future__ import annotations

from backend.agents.tools.collections import (
    get_benchling_expert_tools,
    get_config_expert_tools,
    get_execution_expert_tools,
    get_orchestrator_tools,
)


def _tool_names(tools):
    return [tool.name for tool in tools]


def test_orchestrator_tools_match_spec():
    tools = get_orchestrator_tools()
    expected = [
        "get_workspace_status",
        "get_current_samplesheet",
        "get_current_config",
    ]

    assert _tool_names(tools) == expected
    assert len(tools) == len(expected)
    assert len(set(_tool_names(tools))) == len(tools)


def test_config_expert_tools_match_spec():
    tools = get_config_expert_tools()
    expected = [
        "list_pipelines",
        "get_pipeline_schema",
        "generate_samplesheet",
        "generate_config",
        "get_workspace_status",
        "get_current_samplesheet",
        "get_current_config",
    ]

    assert _tool_names(tools) == expected
    assert len(tools) == len(expected)
    assert len(set(_tool_names(tools))) == len(tools)


def test_benchling_expert_tools_match_spec():
    tools = get_benchling_expert_tools()
    expected = [
        "search_ngs_runs",
        "get_ngs_run_samples",
        "get_ngs_run_qc",
        "get_fastq_paths",
        "get_entities",
        "get_entity_relationships",
        "trace_sample_lineage",
        "find_sample_descendants",
        "list_entries",
        "get_entry_content",
        "get_entry_entities",
        "get_schemas",
        "get_schema_field_info",
        "get_dropdown_values",
        "list_projects",
        "execute_warehouse_query",
    ]

    assert _tool_names(tools) == expected
    assert len(tools) == len(expected)
    assert len(set(_tool_names(tools))) == len(tools)


def test_execution_expert_tools_match_spec():
    tools = get_execution_expert_tools()
    expected = [
        "validate_inputs",
        "submit_run",
        "cancel_run",
        "recover_run",
        "delete_file",
        "clear_samplesheet",
        "get_workspace_status",
        "get_current_samplesheet",
        "get_current_config",
        "get_run_status",
        "get_run_tasks",
        "list_user_runs",
        "get_run_logs",
        "get_task_logs",
        "analyze_failure",
        "get_run_outputs",
        "get_signed_download_url",
    ]

    assert _tool_names(tools) == expected
    assert len(tools) == len(expected)
    assert len(set(_tool_names(tools))) == len(tools)
