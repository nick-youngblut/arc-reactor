from __future__ import annotations

import pytest

from backend.agents.tools import get_agent_tools
from backend.agents.tools.ngs_discovery import (
    get_fastq_paths,
    get_ngs_run_qc,
    get_ngs_run_samples,
    search_ngs_runs,
)
from backend.agents.tools.base import ToolContext


class _BenchlingStub:
    def __init__(self) -> None:
        self.last_sql: str | None = None
        self.last_params: dict | None = None

    async def query(self, sql: str, params: dict | None = None):
        self.last_sql = sql
        self.last_params = params or {}

        if "ngs_run_output_detailed" in sql and "GROUP BY nrod.lane" in sql:
            return [
                {"lane": "1", "reads": 300, "avg_q30": 92.4, "error_rate": 0.8},
                {"lane": "2", "reads": 280, "avg_q30": 91.1, "error_rate": 0.9},
            ]
        if "GROUP BY nrod.lane, nrod.read" in sql:
            return [
                {"lane": "1", "read": "R1", "avg_q30": 92.4, "reads_millions": 150},
                {"lane": "1", "read": "R2", "avg_q30": 91.8, "reads_millions": 150},
            ]
        if "GROUP BY lps.sample_id" in sql:
            return [
                {"sample_id": "LPS-001", "total_reads": 40000000, "avg_q30": 94.1},
                {"sample_id": "LPS-002", "total_reads": 38000000, "avg_q30": 88.9},
            ]
        if "AVG(nros.q30_percent)" in sql and "Run Metrics" not in sql:
            return [
                {
                    "ngs_run": "NR-2024-0156",
                    "pooled_sample": "SspArc0050",
                    "instrument": "NovaSeqX",
                    "completion_date": "2024-12-18",
                    "sample_count": 24,
                    "total_reads": 1200000000,
                    "avg_q30": 94.5,
                    "avg_read_length": 150,
                }
            ]
        if "WITH run_info" in sql:
            return [
                {
                    "ngs_run": "NR-2024-0156",
                    "pooled_sample": "SspArc0050",
                    "submitter_first_name": "Jane",
                    "submitter_last_name": "Smith",
                    "instrument": "NovaSeqX",
                    "completion_date": "2024-12-18",
                    "run_path": "gs://arc-ngs-data/NR-2024-0156",
                    "sample_id": "LPS-001",
                    "sample_name": "LPS-001",
                    "fastq_r1": "gs://arc-ngs-data/NR-2024-0156/LPS-001_R1.fastq.gz",
                    "fastq_r2": "gs://arc-ngs-data/NR-2024-0156/LPS-001_R2.fastq.gz",
                    "organism": "Human",
                    "cell_line": "HeLa",
                },
                {
                    "ngs_run": "NR-2024-0156",
                    "pooled_sample": "SspArc0050",
                    "submitter_first_name": "Jane",
                    "submitter_last_name": "Smith",
                    "instrument": "NovaSeqX",
                    "completion_date": "2024-12-18",
                    "run_path": "gs://arc-ngs-data/NR-2024-0156",
                    "sample_id": "LPS-002",
                    "sample_name": "LPS-002",
                    "fastq_r1": "gs://arc-ngs-data/NR-2024-0156/LPS-002_R1.fastq.gz",
                    "fastq_r2": "gs://arc-ngs-data/NR-2024-0156/LPS-002_R2.fastq.gz",
                    "organism": "Human",
                    "cell_line": "HeLa",
                },
            ]
        if "library_prep_sample$raw" in sql and "fastq_r1" in sql:
            return [
                {
                    "sample_id": "LPS-001",
                    "ngs_run": "NR-2024-0156",
                    "fastq_r1": "gs://arc-ngs-data/NR-2024-0156/LPS-001_R1.fastq.gz",
                    "fastq_r2": "gs://arc-ngs-data/NR-2024-0156/LPS-001_R2.fastq.gz",
                },
                {
                    "sample_id": "LPS-002",
                    "ngs_run": "NR-2024-0156",
                    "fastq_r1": "gs://arc-ngs-data/NR-2024-0156/LPS-002_R1.fastq.gz",
                    "fastq_r2": "gs://arc-ngs-data/NR-2024-0156/LPS-002_R2.fastq.gz",
                },
            ]
        return [
            {
                "ngs_run": "NR-2024-0156",
                "pooled_sample": "SspArc0050",
                "submitter": "Jane Smith",
                "instrument": "NovaSeqX",
                "completion_date": "2024-12-18",
                "sample_count": 24,
                "run_path": "gs://arc-ngs-data/NR-2024-0156",
            },
            {
                "ngs_run": "NR-2024-0152",
                "pooled_sample": "SspArc0048",
                "submitter": "Jane Smith",
                "instrument": "NovaSeqX",
                "completion_date": "2024-12-16",
                "sample_count": 12,
                "run_path": "gs://arc-ngs-data/NR-2024-0152",
            },
        ]


class _StorageStub:
    def files_exist(self, gcs_paths):
        return {path: True for path in gcs_paths}


class _Runtime:
    def __init__(self, benchling, storage=None):
        self.config = {
            "configurable": {
                "benchling_service": benchling,
                "storage_service": storage,
                "user_email": "dev@example.com",
                "user_name": "Developer",
            }
        }


@pytest.mark.asyncio
async def test_search_ngs_runs_with_wildcards():
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    output = await search_ngs_runs(
        pooled_sample="SspArc%",
        use_wildcards=True,
        include_qc_summary=True,
        runtime=runtime,
    )

    assert "Found 2 NGS runs" in output
    assert "NR-2024-0156" in output
    assert benchling.last_sql is not None
    assert "LIKE" in benchling.last_sql


@pytest.mark.asyncio
async def test_get_ngs_run_samples_formats_summary():
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    output = await get_ngs_run_samples(ngs_run="NR-2024-0156", runtime=runtime)

    assert "NGS Run: NR-2024-0156" in output
    assert "Samples:" in output
    assert "LPS-001" in output


@pytest.mark.asyncio
async def test_get_ngs_run_samples_requires_filter():
    output = await get_ngs_run_samples()
    assert "Error: Please provide either ngs_run or pooled_sample" in output


@pytest.mark.asyncio
async def test_get_ngs_run_qc_summary_lane_sample():
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    summary = await get_ngs_run_qc(ngs_run="NR-2024-0156", level="summary", runtime=runtime)
    assert "QC Summary" in summary
    assert "Lane Summary" in summary

    lane = await get_ngs_run_qc(ngs_run="NR-2024-0156", level="lane", runtime=runtime)
    assert "lane" in lane
    assert "avg_q30" in lane

    sample = await get_ngs_run_qc(ngs_run="NR-2024-0156", level="sample", runtime=runtime)
    assert "sample_id" in sample
    assert "avg_q30" in sample


@pytest.mark.asyncio
async def test_get_fastq_paths_verification():
    benchling = _BenchlingStub()
    storage = _StorageStub()
    runtime = _Runtime(benchling, storage=storage)

    output = await get_fastq_paths(
        sample_names="LPS-001;LPS-002",
        verify_exists=True,
        runtime=runtime,
    )

    assert "FASTQ paths for 2 samples" in output
    assert "All files verified in GCS." in output
    assert "YES" in output


def test_agent_tools_exports():
    tools = get_agent_tools()
    assert {tool.name for tool in tools} >= {
        "search_ngs_runs",
        "get_ngs_run_samples",
        "get_ngs_run_qc",
        "get_fastq_paths",
    }
