from __future__ import annotations

from langchain_core.tools import BaseTool

from .ngs_discovery import (
    get_fastq_paths,
    get_ngs_run_qc,
    get_ngs_run_samples,
    search_ngs_runs,
)

NGS_TOOL_CATEGORY = "ngs"


def get_agent_tools() -> list[BaseTool]:
    return [
        search_ngs_runs,
        get_ngs_run_samples,
        get_ngs_run_qc,
        get_fastq_paths,
    ]
