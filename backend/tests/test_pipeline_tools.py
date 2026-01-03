from __future__ import annotations

import json

import pytest

from backend.agents.tools.file_generation import (
    generate_config,
    generate_samplesheet,
    validate_inputs,
)
from backend.agents.tools.pipeline_tools import get_pipeline_schema, list_pipelines


class _BenchlingStub:
    async def query(self, sql: str, params: dict | None = None, return_format: str | None = None):
        if "ngs_run_pooling_v2$raw" in sql:
            return [
                {
                    "ngs_run": "NR-2024-0156",
                    "pooled_sample": "SspArc0050",
                    "sample_id": "LPS-001",
                    "sample_name": "LPS-001",
                    "fastq_1": "gs://arc-ngs-data/NR-2024-0156/LPS-001_R1.fastq.gz",
                    "fastq_2": "gs://arc-ngs-data/NR-2024-0156/LPS-001_R2.fastq.gz",
                },
                {
                    "ngs_run": "NR-2024-0156",
                    "pooled_sample": "SspArc0050",
                    "sample_id": "LPS-002",
                    "sample_name": "LPS-002",
                    "fastq_1": "gs://arc-ngs-data/NR-2024-0156/LPS-002_R1.fastq.gz",
                    "fastq_2": "gs://arc-ngs-data/NR-2024-0156/LPS-002_R2.fastq.gz",
                },
            ]
        return []


class _StorageStub:
    def __init__(self, missing: set[str] | None = None) -> None:
        self.missing = missing or set()

    def files_exist(self, gcs_paths):
        return {path: path not in self.missing for path in gcs_paths}


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
async def test_list_pipelines_includes_scrnaseq():
    output = await list_pipelines.arun()
    assert "nf-core/scrnaseq" in output


@pytest.mark.asyncio
async def test_get_pipeline_schema_formats_params():
    output = await get_pipeline_schema.arun("nf-core/scrnaseq")
    assert "Required Parameters" in output
    assert "genome" in output


@pytest.mark.asyncio
async def test_generate_samplesheet_stores_file():
    runtime = _Runtime(_BenchlingStub(), _StorageStub())
    output = await generate_samplesheet.arun(
        ngs_run="NR-2024-0156",
        pipeline="nf-core/scrnaseq",
        runtime=runtime,
    )
    assert "samplesheet" in output
    generated = runtime.config["configurable"].get("generated_files", {})
    assert "samplesheet.csv" in generated
    assert "LPS-001" in generated["samplesheet.csv"]["content"]


@pytest.mark.asyncio
async def test_generate_config_renders_profile():
    output = await generate_config.arun(
        pipeline="nf-core/scrnaseq",
        params={"genome": "GRCh38", "protocol": "10XV3"},
    )
    assert "google-batch" in output
    assert "params {" in output


@pytest.mark.asyncio
async def test_validate_inputs_reports_missing_files():
    samplesheet = (
        "sample,fastq_1,fastq_2,expected_cells\n"
        "LPS-001,gs://bucket/file1.fastq.gz,gs://bucket/file2.fastq.gz,4000\n"
    )
    config = 'params {\n  genome = "GRCh38"\n  protocol = "10XV3"\n}\n'
    runtime = _Runtime(_BenchlingStub(), _StorageStub(missing={"gs://bucket/file2.fastq.gz"}))
    output = await validate_inputs.arun(samplesheet, config, "nf-core/scrnaseq", runtime=runtime)
    payload = json.loads(output)
    assert payload["valid"] is False
    assert any(error["type"] == "MISSING_FILE" for error in payload["errors"])
