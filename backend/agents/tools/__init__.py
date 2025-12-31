from __future__ import annotations

from langchain_core.tools import BaseTool

from .benchling_discovery import (
    get_entities,
    get_entity_relationships,
    get_entry_content,
    get_entry_entities,
    list_entries,
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
from .file_generation import generate_config, generate_samplesheet, validate_inputs

NGS_TOOL_CATEGORY = "ngs"
BENCHLING_TOOL_CATEGORY = "benchling"
SCHEMA_TOOL_CATEGORY = "schema"


def get_agent_tools() -> list[BaseTool]:
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
        get_entities,
        get_entity_relationships,
        list_entries,
        get_entry_content,
        get_entry_entities,
        get_schemas,
        get_schema_field_info,
        get_dropdown_values,
        list_projects,
        execute_warehouse_query,
    ]
