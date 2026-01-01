from __future__ import annotations

from backend.agents.tools import (
    execute_warehouse_query,
    get_entities,
    get_entity_relationships,
    get_entry_entities,
    get_ngs_run_samples,
    list_entries,
    search_ngs_runs,
)

BENCHLING_EXPERT_PROMPT = """You are an expert at querying Arc Institute's Benchling database.

You have deep knowledge of:
- NGS workflow: samples -> library prep -> pooling -> sequencing
- Benchling schema relationships and entity link fields
- Common data quality issues and how to handle them

When given a complex query:
1. Break it down into simpler sub-queries
2. Use get_entity_relationships for lineage traversal
3. Combine and reconcile results
4. Present a clear summary

Available schemas in the NGS workflow:
- NGS Library Prep Sample: Individual samples prepared for sequencing
- NGS Pooled Sample: Pooled samples ready for loading
- NGS Run: Sequencing run metadata
- NGS Run Output v2: Per-sample outputs with FASTQ paths
"""


def create_benchling_expert(model):
    return {
        "name": "benchling_expert",
        "description": (
            "Expert at complex Benchling queries involving multiple data sources, "
            "relationship traversal, and data reconciliation"
        ),
        "prompt": BENCHLING_EXPERT_PROMPT,
        "tools": [
            search_ngs_runs,
            get_ngs_run_samples,
            get_entities,
            get_entity_relationships,
            list_entries,
            get_entry_entities,
            execute_warehouse_query,
        ],
        "model": model,
    }
