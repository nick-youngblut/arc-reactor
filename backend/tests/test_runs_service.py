from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base
from backend.models.schemas.runs import RunStatus
from backend.services.runs import RunStoreService


class _Settings:
    nextflow_bucket = "arc-reactor-runs"


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
async def test_create_and_get_run(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    run_id, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name="Arc User",
        params={"genome": "GRCh38"},
        sample_count=4,
    )

    run = await service.get_run(run_id)
    assert run is not None
    assert run.run_id == run_id
    assert run.status == RunStatus.PENDING
    assert run.gcs_path == f"gs://arc-reactor-runs/runs/{run_id}"


@pytest.mark.asyncio
async def test_list_runs_filters(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    first_run, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name=None,
        params={},
        sample_count=1,
    )
    await service.create_run(
        pipeline="nf-core/rnaseq",
        pipeline_version="3.0.0",
        user_email="other@arc.org",
        user_name=None,
        params={},
        sample_count=1,
    )

    response = await service.list_runs(user_email="user@arc.org")
    assert response.total == 1
    assert response.runs[0].run_id == first_run


@pytest.mark.asyncio
async def test_update_run_status_transitions(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    run_id, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name=None,
        params={},
        sample_count=1,
    )

    assert await service.update_run_status(run_id=run_id, status=RunStatus.SUBMITTED)
    assert await service.update_run_status(run_id=run_id, status=RunStatus.RUNNING)
    assert await service.update_run_status(run_id=run_id, status=RunStatus.COMPLETED)

    run = await service.get_run(run_id)
    assert run is not None
    assert run.status == RunStatus.COMPLETED


@pytest.mark.asyncio
async def test_invalid_status_transition(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    run_id, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name=None,
        params={},
        sample_count=1,
    )

    with pytest.raises(ValueError):
        await service.update_run_status(run_id=run_id, status=RunStatus.COMPLETED)


@pytest.mark.asyncio
async def test_create_recovery_run(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    parent_id, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name=None,
        params={"genome": "GRCh38"},
        sample_count=5,
        source_ngs_runs=["NR-001"],
        source_project="CellAtlas",
    )
    await service.update_run_status(run_id=parent_id, status=RunStatus.FAILED)

    recovery_id = await service.create_recovery_run(
        parent_run_id=parent_id,
        user_email="user@arc.org",
        user_name="Recovery User",
        notes="Retry",
    )

    assert recovery_id is not None
    recovery = await service.get_run(recovery_id)
    assert recovery is not None
    assert recovery.parent_run_id == parent_id
    assert recovery.is_recovery is True
    assert recovery.reused_work_dir == f"gs://arc-reactor-runs/runs/{parent_id}/work/"
