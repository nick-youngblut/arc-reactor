from __future__ import annotations

import json

import pytest

from backend.agents.tools.submission import cancel_run, clear_samplesheet, delete_file, submit_run
from backend.models.schemas.runs import RunStatus


class _RunStub:
    def __init__(self, run_id: str, user_email: str, status: RunStatus) -> None:
        self.run_id = run_id
        self.user_email = user_email
        self.status = status
        self.batch_job_name = None


class _RunStoreStub:
    def __init__(self) -> None:
        self.run = _RunStub("run-abc123", "dev@example.com", RunStatus.PENDING)
        self.created = False
        self.updated_status = None

    async def create_run(self, **kwargs):
        self.created = True
        return self.run.run_id, "secret"

    async def get_run(self, run_id: str):
        if run_id != self.run.run_id:
            return None
        return self.run

    async def update_run_status(self, **kwargs):
        status = kwargs.get("status")
        if isinstance(status, RunStatus):
            self.run.status = status
        self.updated_status = status
        return True


class _StorageStub:
    def __init__(self, exists: bool = True) -> None:
        self.exists = exists
        self.bucket_name = "arc-reactor-runs"

    def upload_run_files(self, run_id, files, user_email):
        return [f"gs://{self.bucket_name}/runs/{run_id}/inputs/{name}" for name in files]

    def delete_run_file(self, run_id, file_path):
        return self.exists


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
async def test_submit_run_creates_run():
    run_store = _RunStoreStub()
    storage = _StorageStub()
    runtime = _Runtime(run_store, storage)
    samplesheet = "sample,fastq_1,fastq_2\nA,gs://a,gs://b"
    config = "params {\n  genome = \"GRCh38\"\n  protocol = \"10XV3\"\n}\n"

    output = await submit_run(
        samplesheet_csv=samplesheet,
        config_content=config,
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        runtime=runtime,
    )

    payload = json.loads(output)
    assert payload["run_id"] == "run-abc123"
    assert run_store.created is True


@pytest.mark.asyncio
async def test_cancel_run_updates_status():
    run_store = _RunStoreStub()
    storage = _StorageStub()
    runtime = _Runtime(run_store, storage)

    output = await cancel_run(run_id="run-abc123", runtime=runtime)
    payload = json.loads(output)
    assert payload["status"] == RunStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_delete_file_missing():
    run_store = _RunStoreStub()
    storage = _StorageStub(exists=False)
    runtime = _Runtime(run_store, storage)

    output = await delete_file(run_id="run-abc123", file_path="inputs/missing.txt", runtime=runtime)
    assert "Error: File not found" in output


@pytest.mark.asyncio
async def test_clear_samplesheet():
    run_store = _RunStoreStub()
    storage = _StorageStub()
    runtime = _Runtime(run_store, storage)
    runtime.config["configurable"]["generated_files"] = {"samplesheet.csv": {"content": "x"}}

    output = await clear_samplesheet(confirm=True, runtime=runtime)
    assert "Samplesheet cleared" in output
    assert "samplesheet.csv" not in runtime.config["configurable"]["generated_files"]
