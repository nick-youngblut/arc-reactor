from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user_context, get_db_session
from backend.models.runs import Run
from backend.models.tasks import Task
from backend.utils.auth import UserContext
from backend.utils.errors import NotFoundError

router = APIRouter(tags=["tasks"])


class TaskResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    run_id: str
    task_id: int
    hash: str
    name: str
    process: str
    status: str
    exit_code: int | None = None
    submit_time: int | None = None
    start_time: int | None = None
    complete_time: int | None = None
    duration_ms: int | None = None
    realtime_ms: int | None = None
    cpu_percent: float | None = None
    peak_rss: int | None = None
    peak_vmem: int | None = None
    workdir: str | None = None
    container: str | None = None
    attempt: int
    error_message: str | None = None


class TaskSummaryResponse(BaseModel):
    total: int
    completed: int
    running: int
    submitted: int
    failed: int
    cached: int


async def _get_run_or_404(session: AsyncSession, run_id: str) -> Run:
    run = await session.get(Run, run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    return run


def _ensure_owner_or_admin(run: Run, user: UserContext) -> None:
    if run.user_email != user.email and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/runs/{run_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    run_id: str,
    status_filter: list[str] | None = Query(None, alias="status"),
    process: str | None = None,
    sort_by: Literal["submit_time", "start_time", "complete_time", "name"] = "submit_time",
    sort_order: Literal["asc", "desc"] = "asc",
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[TaskResponse]:
    run = await _get_run_or_404(session, run_id)
    _ensure_owner_or_admin(run, user)

    query = select(Task).where(Task.run_id == run_id)

    if status_filter:
        query = query.where(Task.status.in_(status_filter))
    if process:
        query = query.where(Task.process.ilike(f"%{process}%"))

    sort_column = getattr(Task, sort_by)
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    result = await session.execute(query)
    tasks = result.scalars().all()

    return [TaskResponse.model_validate(t) for t in tasks]


@router.get("/runs/{run_id}/tasks/summary", response_model=TaskSummaryResponse)
async def get_task_summary(
    run_id: str,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> TaskSummaryResponse:
    run = await _get_run_or_404(session, run_id)
    _ensure_owner_or_admin(run, user)

    result = await session.execute(
        select(
            Task.status,
            func.count(Task.id).label("count"),
        )
        .where(Task.run_id == run_id)
        .group_by(Task.status)
    )

    counts = {row.status: row.count for row in result}

    return TaskSummaryResponse(
        total=sum(counts.values()),
        completed=counts.get("COMPLETED", 0),
        running=counts.get("RUNNING", 0),
        submitted=counts.get("SUBMITTED", 0),
        failed=counts.get("FAILED", 0),
        cached=counts.get("CACHED", 0),
    )
