from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from backend.agents.tools.output_tools import get_run_outputs, get_signed_download_url
from backend.models.schemas.runs import RunStatus


@dataclass
class _RunStub:
    run_id: str
    status: RunStatus
    pipeline: str = "nf-core/scrnaseq"
    pipeline_version: str = "2.7.1"
    user_email: str = "dev@example.com"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sample_count: int = 4


class _RunStoreStub:
    def __init__(self, run: _RunStub):
        self._run = run

    async def get_run(self, run_id: str):
        if run_id != self._run.run_id:
            return None
        return self._run


class _StorageStub:
    bucket_name = "test-bucket"

    def __init__(self):
        self.files = {
            "results": [
                {"name": "results/counts.h5ad", "size": 1024, "updated": "2025-01-01"},
                {"name": "results/multiqc/report.html", "size": 512, "updated": "2025-01-01"},
            ]
        }

    def get_run_files(self, _run_id: str):
        return self.files

    def generate_signed_url(self, _gcs_path: str, _expiration: int):
        return "https://storage.googleapis.com/signed-url?token=abc"


class _Runtime:
    def __init__(self, run_store, storage):
        self.config = {
            "configurable": {
                "run_store_service": run_store,
                "storage_service": storage,
                "user_email": "dev@example.com",
                "user_name": "Developer",
            }
        }


@pytest.mark.asyncio
async def test_get_run_outputs_lists_files():
    run = _RunStub(run_id="run-abc123", status=RunStatus.COMPLETED)
    runtime = _Runtime(_RunStoreStub(run), _StorageStub())

    output = await get_run_outputs.ainvoke({"run_id": "run-abc123", "runtime": runtime})

    assert "Outputs for run-abc123" in output
    assert "counts.h5ad" in output
    assert "multiqc/report.html" in output


@pytest.mark.asyncio
async def test_get_run_outputs_applies_filter():
    run = _RunStub(run_id="run-abc123", status=RunStatus.COMPLETED)
    runtime = _Runtime(_RunStoreStub(run), _StorageStub())

    output = await get_run_outputs.ainvoke(
        {"run_id": "run-abc123", "path_filter": "multiqc/*", "runtime": runtime}
    )

    assert "multiqc/report.html" in output
    assert "counts.h5ad" not in output


@pytest.mark.asyncio
async def test_get_signed_download_url_generates_url():
    run = _RunStub(run_id="run-abc123", status=RunStatus.COMPLETED)
    runtime = _Runtime(_RunStoreStub(run), _StorageStub())

    output = await get_signed_download_url.ainvoke({
        "run_id": "run-abc123",
        "file_path": "counts.h5ad",
        "runtime": runtime,
    })

    assert output.startswith("https://storage.googleapis.com/")


@pytest.mark.asyncio
async def test_get_signed_download_url_rejects_missing():
    run = _RunStub(run_id="run-abc123", status=RunStatus.COMPLETED)
    runtime = _Runtime(_RunStoreStub(run), _StorageStub())

    output = await get_signed_download_url.ainvoke({
        "run_id": "run-abc123",
        "file_path": "missing.txt",
        "runtime": runtime,
    })

    assert "Error: File not found" in output
