from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.api.routes.tasks import get_task_summary, list_tasks
from backend.models.runs import Run
from backend.models.tasks import Task
from backend.utils.auth import UserContext
from backend.utils.errors import NotFoundError




async def _create_run(session: AsyncSession, run_id: str, user_email: str) -> None:
    run = Run(
        run_id=run_id,
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        status="running",
        user_email=user_email,
        user_name="Arc User",
        gcs_path=f"gs://arc-reactor-runs/runs/{run_id}",
        params={},
        sample_count=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(run)
    await session.commit()


async def _create_task(session: AsyncSession, run_id: str, status: str, task_id: int) -> None:
    task = Task(
        id=uuid4(),
        run_id=run_id,
        task_id=task_id,
        hash="abcd1234efgh5678ijkl9012mnop3456",
        name=f"task-{task_id}",
        process="ALIGN",
        status=status,
        submit_time=10 * task_id,
        attempt=1,
    )
    session.add(task)
    await session.commit()


@pytest.mark.asyncio
async def test_list_tasks_filters_and_sort(session: AsyncSession) -> None:
    await _create_run(session, "run-1", "user@arc.org")
    await _create_task(session, "run-1", "SUBMITTED", 2)
    await _create_task(session, "run-1", "RUNNING", 1)

    user = UserContext(email="user@arc.org", name="Arc User")
    tasks = await list_tasks(
        run_id="run-1",
        status_filter=["RUNNING"],
        process=None,
        sort_by="submit_time",
        sort_order="asc",
        user=user,
        session=session,
    )

    assert len(tasks) == 1
    assert tasks[0].status == "RUNNING"

    all_tasks = await list_tasks(
        run_id="run-1",
        status_filter=None,
        process=None,
        sort_by="submit_time",
        sort_order="desc",
        user=user,
        session=session,
    )

    assert [task.task_id for task in all_tasks] == [2, 1]


@pytest.mark.asyncio
async def test_get_task_summary_counts(session: AsyncSession) -> None:
    await _create_run(session, "run-2", "user@arc.org")
    await _create_task(session, "run-2", "COMPLETED", 1)
    await _create_task(session, "run-2", "FAILED", 2)
    await _create_task(session, "run-2", "CACHED", 3)

    user = UserContext(email="user@arc.org", name="Arc User")
    summary = await get_task_summary(run_id="run-2", user=user, session=session)

    assert summary.total == 3
    assert summary.completed == 1
    assert summary.failed == 1
    assert summary.cached == 1
    assert summary.running == 0
    assert summary.submitted == 0


@pytest.mark.asyncio
async def test_list_tasks_access_denied(session: AsyncSession) -> None:
    await _create_run(session, "run-3", "owner@arc.org")

    user = UserContext(email="other@arc.org", name="Other User")
    with pytest.raises(HTTPException) as excinfo:
        await list_tasks(
            run_id="run-3",
            status_filter=None,
            process=None,
            sort_by="submit_time",
            sort_order="asc",
            user=user,
            session=session,
        )

    assert excinfo.value.status_code == 403


@pytest.mark.asyncio
async def test_list_tasks_not_found(session: AsyncSession) -> None:
    user = UserContext(email="user@arc.org", name="Arc User")
    with pytest.raises(NotFoundError):
        await list_tasks(
            run_id="missing-run",
            status_filter=None,
            process=None,
            sort_by="submit_time",
            sort_order="asc",
            user=user,
            session=session,
        )
