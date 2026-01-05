from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.schemas.runs import RunStatus
from backend.models.tasks import Task
from backend.services.runs import RunStoreService


class _Settings:
    nextflow_bucket = "arc-reactor-runs"


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

    recovery_result = await service.create_recovery_run(
        parent_run_id=parent_id,
        user_email="user@arc.org",
        user_name="Recovery User",
        notes="Retry",
    )

    assert recovery_result is not None
    recovery_id, _weblog_secret = recovery_result
    recovery = await service.get_run(recovery_id)
    assert recovery is not None
    assert recovery.parent_run_id == parent_id
    assert recovery.is_recovery is True
    assert recovery.reused_work_dir == f"gs://arc-reactor-runs/runs/{parent_id}/work/"


@pytest.mark.asyncio
async def test_get_task_summary(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    run_id, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name=None,
        params={},
        sample_count=1,
    )

    now = datetime.now(timezone.utc)
    tasks = [
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=1,
            hash="abc123",
            name="FASTQC (1)",
            process="FASTQC",
            status="COMPLETED",
            created_at=now,
            updated_at=now,
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=2,
            hash="def456",
            name="STAR_ALIGN (1)",
            process="STAR_ALIGN",
            status="RUNNING",
            created_at=now,
            updated_at=now,
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=3,
            hash="ghi789",
            name="STAR_ALIGN (2)",
            process="STAR_ALIGN",
            status="FAILED",
            created_at=now,
            updated_at=now,
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=4,
            hash="jkl012",
            name="CACHE (1)",
            process="CACHE",
            status="CACHED",
            created_at=now,
            updated_at=now,
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=5,
            hash="mno345",
            name="SUBMIT (1)",
            process="SUBMIT",
            status="SUBMITTED",
            created_at=now,
            updated_at=now,
        ),
    ]
    session.add_all(tasks)
    await session.commit()

    summary = await service.get_task_summary(run_id)

    assert summary.total == 5
    assert summary.completed == 1
    assert summary.running == 1
    assert summary.failed == 1
    assert summary.cached == 1
    assert summary.submitted == 1


@pytest.mark.asyncio
async def test_get_run_tasks_filters_and_orders(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    run_id, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name=None,
        params={},
        sample_count=1,
    )

    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    created_at = datetime.now(timezone.utc)
    tasks = [
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=1,
            hash="abc123",
            name="FASTQC (1)",
            process="FASTQC",
            status="COMPLETED",
            submit_time=now - 2000,
            created_at=created_at,
            updated_at=created_at,
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=2,
            hash="def456",
            name="FASTQC (2)",
            process="FASTQC",
            status="COMPLETED",
            submit_time=now - 1000,
            created_at=created_at,
            updated_at=created_at,
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=3,
            hash="ghi789",
            name="STAR_ALIGN (1)",
            process="STAR_ALIGN",
            status="FAILED",
            submit_time=now,
            created_at=created_at,
            updated_at=created_at,
        ),
    ]
    session.add_all(tasks)
    await session.commit()

    completed_tasks = await service.get_run_tasks(run_id, status_filter="completed", limit=10)
    assert [task.name for task in completed_tasks] == ["FASTQC (2)", "FASTQC (1)"]

    limited_tasks = await service.get_run_tasks(run_id, limit=1)
    assert len(limited_tasks) == 1
    assert limited_tasks[0].name == "STAR_ALIGN (1)"


@pytest.mark.asyncio
async def test_get_task_by_name_returns_latest_attempt(session: AsyncSession) -> None:
    service = RunStoreService.create(session, _Settings())
    run_id, _weblog_secret = await service.create_run(
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        user_email="user@arc.org",
        user_name=None,
        params={},
        sample_count=1,
    )

    now = datetime.now(timezone.utc)
    tasks = [
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=1,
            hash="abc123",
            name="STAR_ALIGN (1)",
            process="STAR_ALIGN",
            status="FAILED",
            attempt=1,
            created_at=now,
            updated_at=now,
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            task_id=1,
            hash="abc123",
            name="STAR_ALIGN (1)",
            process="STAR_ALIGN",
            status="COMPLETED",
            attempt=2,
            created_at=now,
            updated_at=now,
        ),
    ]
    session.add_all(tasks)
    await session.commit()

    task = await service.get_task_by_name(run_id, "STAR_ALIGN (1)")

    assert task is not None
    assert task.attempt == 2
    assert task.status == "COMPLETED"
