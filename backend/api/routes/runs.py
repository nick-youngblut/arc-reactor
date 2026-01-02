from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.dependencies import get_current_user_context, get_db_session, get_storage_service
from backend.models.schemas.runs import (
    RunCreateRequest,
    RunListResponse,
    RunRecoverRequest,
    RunResponse,
    RunStatus,
)
from backend.services.pipelines import PipelineRegistry
from backend.services.batch import BatchService
from backend.services.runs import RunStoreService
from backend.services.storage import StorageService
from backend.utils.auth import UserContext
from backend.utils.errors import NotFoundError, ValidationError

router = APIRouter(tags=["runs"])

_TERMINAL_STATUSES = {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}
logger = logging.getLogger(__name__)


def _ensure_owner_or_admin(run: RunResponse, user: UserContext) -> None:
    if run.user_email != user.email and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _count_samples(samplesheet_csv: str) -> int:
    reader = csv.reader(io.StringIO(samplesheet_csv))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return 0
    return max(len(rows) - 1, 0)


def _sse_event(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


def _status_timestamp(run: RunResponse) -> datetime:
    if run.status == RunStatus.SUBMITTED and run.submitted_at:
        return run.submitted_at
    if run.status == RunStatus.RUNNING and run.started_at:
        return run.started_at
    if run.status == RunStatus.COMPLETED and run.completed_at:
        return run.completed_at
    if run.status == RunStatus.FAILED and run.failed_at:
        return run.failed_at
    if run.status == RunStatus.CANCELLED and run.cancelled_at:
        return run.cancelled_at
    return run.updated_at


def _progress_from_metrics(metrics: dict[str, Any] | None) -> float | None:
    if not metrics:
        return None
    raw = metrics.get("progress")
    if isinstance(raw, (int, float)):
        return float(raw)
    completed = metrics.get("tasks_completed")
    total = metrics.get("tasks_total")
    if isinstance(completed, (int, float)) and isinstance(total, (int, float)) and total:
        return float(completed) / float(total)
    return None


def _cancel_batch_job(batch_job_name: str | None) -> None:
    if not batch_job_name:
        return
    try:
        from google.cloud import batch_v1

        client = batch_v1.BatchServiceClient()
        client.delete_job(name=batch_job_name)
    except Exception as exc:
        logger.warning("Failed to cancel Batch job %s: %s", batch_job_name, exc)


@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    status: RunStatus | None = Query(default=None),
    pipeline: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    include_all: bool = Query(default=False, alias="all"),
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> RunListResponse:
    if include_all and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    service = RunStoreService.create(session, settings)
    user_filter = None if include_all and user.is_admin else user.email
    return await service.list_runs(
        user_email=user_filter,
        status=status,
        pipeline=pipeline,
        page=page,
        page_size=page_size,
    )


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> RunResponse:
    service = RunStoreService.create(session, settings)
    run = await service.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run, user)
    return run


@router.post("/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreateRequest,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> RunResponse:
    registry = PipelineRegistry.create()
    pipeline = registry.get_pipeline(payload.pipeline)
    if not pipeline:
        raise ValidationError("Pipeline not found", detail=payload.pipeline)
    if payload.pipeline_version not in pipeline.versions:
        raise ValidationError("Pipeline version not available", detail=payload.pipeline_version)

    errors = registry.validate_params(payload.pipeline, payload.params)
    if errors:
        raise ValidationError("Invalid pipeline parameters", detail="; ".join(errors))

    sample_count = _count_samples(payload.samplesheet_csv)
    if sample_count <= 0:
        raise ValidationError("samplesheet_csv must include at least one sample")

    service = RunStoreService.create(session, settings)
    batch = BatchService.create(settings)
    run_id = await service.submit_run(
        payload=payload,
        user_email=user.email,
        user_name=user.name,
        sample_count=sample_count,
        storage=storage,
        batch=batch,
    )

    run = await service.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    return run


@router.delete("/runs/{run_id}", response_model=RunResponse)
async def cancel_run(
    run_id: str,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> RunResponse:
    service = RunStoreService.create(session, settings)
    run = await service.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run, user)

    if run.status in _TERMINAL_STATUSES:
        raise ValidationError("Run is already in terminal state", detail=run.status.value)

    _cancel_batch_job(run.batch_job_name)
    await service.update_run_status(run_id=run_id, status=RunStatus.CANCELLED)
    updated = await service.get_run(run_id)
    if not updated:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    return updated


@router.post("/runs/{run_id}/recover", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def recover_run(
    run_id: str,
    payload: RunRecoverRequest,
    storage: StorageService = Depends(get_storage_service),
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> RunResponse:
    service = RunStoreService.create(session, settings)
    run = await service.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run, user)

    batch = BatchService.create(settings)
    recovery_id = await service.submit_recovery_run(
        parent_run_id=run_id,
        user_email=user.email,
        user_name=user.name,
        storage=storage,
        batch=batch,
        notes=payload.notes,
        override_params=payload.override_params,
        override_config=payload.override_config,
        reuse_work_dir=payload.reuse_work_dir,
    )

    recovery = await service.get_run(recovery_id)
    if not recovery:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {recovery_id}")
    return recovery


@router.get("/runs/{run_id}/files")
async def list_run_files(
    run_id: str,
    storage: StorageService = Depends(get_storage_service),
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    service = RunStoreService.create(session, settings)
    run = await service.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run, user)

    grouped = storage.get_run_files(run_id)
    for entries in grouped.values():
        for entry in entries:
            gcs_uri = str(entry.get("gcs_uri"))
            entry["download_url"] = storage.generate_signed_url(gcs_uri)
            updated = entry.get("updated")
            if isinstance(updated, datetime):
                entry["updated_at"] = updated.isoformat()
            elif updated is not None:
                entry["updated_at"] = updated
    return grouped


@router.get("/runs/{run_id}/events")
async def stream_run_events(
    run_id: str,
    request: Request,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    service = RunStoreService.create(session, settings)
    run = await service.get_run(run_id)
    if not run:
        raise NotFoundError("Run not found", detail=f"No run exists with ID {run_id}")
    _ensure_owner_or_admin(run, user)

    async def event_generator():
        last_status = run.status
        start = datetime.now(timezone.utc)
        yield _sse_event(
            "status",
            {
                "status": last_status.value,
                "timestamp": _status_timestamp(run).isoformat(),
                "progress": _progress_from_metrics(run.metrics),
            },
        )
        while True:
            if await request.is_disconnected():
                break
            current = await service.get_run(run_id)
            if not current:
                yield _sse_event("done", {"status": "not_found"})
                break
            if current.status != last_status:
                last_status = current.status
                yield _sse_event(
                    "status",
                    {
                        "status": last_status.value,
                        "timestamp": _status_timestamp(current).isoformat(),
                        "progress": _progress_from_metrics(current.metrics),
                    },
                )
                if last_status in _TERMINAL_STATUSES:
                    yield _sse_event(
                        "done",
                        {
                            "status": last_status.value,
                            "timestamp": _status_timestamp(current).isoformat(),
                        },
                    )
                    break
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            if elapsed > 600:
                yield _sse_event("done", {"status": "timeout"})
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
