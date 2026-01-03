from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base
from backend.models.schemas.runs import RunCreateRequest, RunStatus
from backend.services.runs import RunStoreService


class _Settings:
    nextflow_bucket = "arc-reactor-runs"


class _StorageStub:
    def __init__(self, bucket_name: str = "arc-reactor-runs") -> None:
        self.bucket_name = bucket_name
        self.files: dict[str, str] = {}
        self.work_dirs: set[str] = set()

    def upload_run_files(self, run_id: str, files: dict[str, str], user_email: str):
        for name, content in files.items():
            self.files[f"{run_id}/inputs/{name}"] = content
        return [f"gs://{self.bucket_name}/runs/{run_id}/inputs/{name}" for name in files]

    def get_file_content(self, gcs_uri: str, text: bool = True):
        key = gcs_uri.split("/runs/")[-1]
        return self.files[key]

    def check_work_dir_exists(self, run_id: str) -> bool:
        return run_id in self.work_dirs


class _BatchStub:
    def __init__(self) -> None:
        self.submissions: list[dict[str, str]] = []

    def submit_orchestrator_job(self, **kwargs):
        self.submissions.append(kwargs)
        return f"batch/{kwargs['run_id']}"


@pytest.fixture
async def session() -> AsyncSession:
    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()
    os.unlink(path)


@pytest.mark.asyncio
async def test_submit_run_flow(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    storage = _StorageStub()
    batch = _BatchStub()

    payload = RunCreateRequest(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        samplesheet_csv="sample,fastq_1,fastq_2\nA,gs://a,gs://b",
        config_content="params { genome = \"GRCh38\" }",
        params={"genome": "GRCh38"},
    )

    run_id = await service.submit_run(
        payload=payload,
        user_email="user@arc.org",
        user_name="Arc User",
        sample_count=1,
        storage=storage,
        batch=batch,
    )

    run = await service.get_run(run_id)
    assert run is not None
    assert run.status == RunStatus.SUBMITTED
    assert run.batch_job_name == f"batch/{run_id}"
    assert f"{run_id}/inputs/samplesheet.csv" in storage.files
    assert batch.submissions[0]["weblog_secret"]


@pytest.mark.asyncio
async def test_submit_recovery_run_flow(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    storage = _StorageStub()
    batch = _BatchStub()

    parent_id, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name="Arc User",
        params={"genome": "GRCh38"},
        sample_count=1,
    )
    await service.update_run_status(run_id=parent_id, status=RunStatus.FAILED)

    storage.upload_run_files(
        parent_id,
        {
            "samplesheet.csv": "sample,fastq_1,fastq_2\nA,gs://a,gs://b",
            "nextflow.config": "params { genome = \"GRCh38\" }",
            "params.yaml": "genome: \"GRCh38\"",
        },
        "user@arc.org",
    )
    storage.work_dirs.add(parent_id)

    recovery_id = await service.submit_recovery_run(
        parent_run_id=parent_id,
        user_email="user@arc.org",
        user_name="Arc User",
        storage=storage,
        batch=batch,
        reuse_work_dir=True,
    )

    recovery = await service.get_run(recovery_id)
    assert recovery is not None
    assert recovery.status == RunStatus.SUBMITTED
    assert recovery.parent_run_id == parent_id
    assert recovery.batch_job_name == f"batch/{recovery_id}"
    assert batch.submissions[0]["weblog_secret"]
