from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.dependencies import get_current_user_context, get_db_session, get_storage_service
from backend.models.schemas.logs import LogEntry, TaskInfo, TaskLogs
from backend.services.logs import LogService
from backend.services.runs import RunStoreService
from backend.services.storage import StorageService
from backend.utils.auth import UserContext
from backend.utils.errors import NotFoundError

router = APIRouter(tags=["logs"])


def _ensure_owner_or_admin(run_email: str, user: UserContext) -> None:
    if run_email != user.email and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _sse_event(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


@router.get("/runs/{run_id}/logs", response_model=list[LogEntry])
async def get_workflow_log(
    run_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> list[LogEntry]:
    runs = RunStoreService.create(session, settings)
    run = await runs.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run.user_email, user)

    service = LogService.create(storage, settings)
    return await service.get_workflow_log(run_id, offset=offset, limit=limit)


@router.get("/runs/{run_id}/logs/stream")
async def stream_workflow_log(
    run_id: str,
    request: Request,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> StreamingResponse:
    runs = RunStoreService.create(session, settings)
    run = await runs.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run.user_email, user)

    service = LogService.create(storage, settings)

    async def event_generator():
        async for entry in service.stream_workflow_log(run_id):
            if await request.is_disconnected():
                break
            payload = entry.model_dump()
            yield _sse_event("log", payload)
        yield _sse_event("done", {"status": "complete"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/runs/{run_id}/tasks", response_model=list[TaskInfo])
async def list_tasks(
    run_id: str,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> list[TaskInfo]:
    runs = RunStoreService.create(session, settings)
    run = await runs.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run.user_email, user)

    service = LogService.create(storage, settings)
    return await service.list_tasks(run_id)


@router.get("/runs/{run_id}/tasks/{task_id}/logs", response_model=TaskLogs)
async def get_task_logs(
    run_id: str,
    task_id: str,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> TaskLogs:
    runs = RunStoreService.create(session, settings)
    run = await runs.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run.user_email, user)

    service = LogService.create(storage, settings)
    return await service.get_task_logs(run_id, task_id)


@router.get("/runs/{run_id}/logs/download")
async def download_logs(
    run_id: str,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> Response:
    runs = RunStoreService.create(session, settings)
    run = await runs.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run.user_email, user)

    service = LogService.create(storage, settings)
    archive = await service.create_log_archive(run_id)
    filename = f"{run_id}-logs.zip"
    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\"",
        "Content-Type": "application/zip",
    }
    return Response(content=archive, media_type="application/zip", headers=headers)
