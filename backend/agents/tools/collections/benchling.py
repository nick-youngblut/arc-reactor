"""Benchling expert tool collection."""
from __future__ import annotations

from langchain_core.tools import BaseTool

from backend.agents.tools.benchling_discovery import (
    get_entities,
    get_entry_content,
    get_entry_entities,
    list_entries,
)
from backend.agents.tools.entity_tools import (
    find_sample_descendants,
    get_entity_relationships,
    trace_sample_lineage,
)
from backend.agents.tools.ngs_discovery import (
    get_fastq_paths,
    get_ngs_run_qc,
    get_ngs_run_samples,
    search_ngs_runs,
)
from backend.agents.tools.schema_tools import (
    execute_warehouse_query,
    get_dropdown_values,
    get_schema_field_info,
    get_schemas,
    list_projects,
)


def get_benchling_expert_tools() -> list[BaseTool]:
    """Tools for the benchling_expert subagent (16 tools).

    Categories:
    - NGS Discovery (4): search_ngs_runs, get_ngs_run_samples, get_ngs_run_qc, get_fastq_paths
    - Benchling Discovery (7): get_entities, get_entity_relationships, trace_sample_lineage,
        find_sample_descendants, list_entries, get_entry_content, get_entry_entities
    - Schema Introspection (4): get_schemas, get_schema_field_info, get_dropdown_values, list_projects
    - Advanced (1): execute_warehouse_query
    """
    return [
        # NGS Discovery
        search_ngs_runs,
        get_ngs_run_samples,
        get_ngs_run_qc,
        get_fastq_paths,
        # Benchling Discovery
        get_entities,
        get_entity_relationships,
        trace_sample_lineage,
        find_sample_descendants,
        list_entries,
        get_entry_content,
        get_entry_entities,
        # Schema Introspection
        get_schemas,
        get_schema_field_info,
        get_dropdown_values,
        list_projects,
        # Advanced
        execute_warehouse_query,
    ]
