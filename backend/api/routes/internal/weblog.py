from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db_session
from backend.models.runs import Run
from backend.models.tasks import Task
from backend.models.weblog_event_log import WeblogEventLog
from backend.utils.auth import ServiceContext, get_service_context

router = APIRouter()
logger = logging.getLogger(__name__)


class PubSubMessage(BaseModel):
    message: dict
    subscription: str


def _parse_timestamp(utc_time: str) -> datetime:
    return datetime.fromisoformat(utc_time.replace("Z", "+00:00"))


def _make_dedup_key(run_id: str, event: dict) -> tuple:
    event_type = event["event"]
    trace = event.get("trace") or {}
    task_id = trace.get("task_id")
    attempt = trace.get("attempt", 1)
    return (run_id, event_type, task_id, attempt)


async def _is_duplicate(session: AsyncSession, key: tuple) -> bool:
    run_id, event_type, task_id, attempt = key
    result = await session.execute(
        select(WeblogEventLog).where(
            WeblogEventLog.run_id == run_id,
            WeblogEventLog.event_type == event_type,
            WeblogEventLog.task_id == task_id,
            WeblogEventLog.attempt == attempt,
        )
    )
    return result.scalar_one_or_none() is not None


async def _record_event(session: AsyncSession, key: tuple, event: dict) -> None:
    run_id, event_type, task_id, attempt = key
    record = WeblogEventLog(
        run_id=run_id,
        event_type=event_type,
        task_id=task_id,
        attempt=attempt,
        event_timestamp=_parse_timestamp(event["utcTime"]),
    )
    session.add(record)


async def _update_run_event_time(session: AsyncSession, run_id: str) -> None:
    await session.execute(
        update(Run)
        .where(Run.run_id == run_id)
        .values(
            last_weblog_event_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )


async def _handle_run_started(session: AsyncSession, run_id: str, event: dict) -> None:
    await session.execute(
        update(Run)
        .where(Run.run_id == run_id)
        .values(
            status="running",
            started_at=_parse_timestamp(event["utcTime"]),
            weblog_run_id=event["runId"],
            weblog_run_name=event["runName"],
            last_weblog_event_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )


async def _handle_task_submitted(session: AsyncSession, run_id: str, event: dict) -> None:
    trace = event.get("trace", {})

    task = Task(
        run_id=run_id,
        task_id=trace.get("task_id"),
        hash=trace.get("hash", ""),
        name=trace.get("name", ""),
        process=trace.get("process", ""),
        status="SUBMITTED",
        submit_time=trace.get("submit"),
        attempt=trace.get("attempt", 1),
        container=trace.get("container"),
        trace_data=trace,
    )

    session.add(task)
    await _update_run_event_time(session, run_id)


async def _handle_task_started(session: AsyncSession, run_id: str, event: dict) -> None:
    trace = event.get("trace", {})

    await session.execute(
        update(Task)
        .where(
            Task.run_id == run_id,
            Task.task_id == trace.get("task_id"),
            Task.attempt == trace.get("attempt", 1),
        )
        .values(
            status="RUNNING",
            start_time=trace.get("start"),
            native_id=trace.get("native_id"),
            workdir=trace.get("workdir"),
            updated_at=datetime.now(timezone.utc),
        )
    )

    await _update_run_event_time(session, run_id)


async def _handle_task_completed(session: AsyncSession, run_id: str, event: dict) -> None:
    trace = event.get("trace", {})

    status = "COMPLETED" if trace.get("exit") == 0 else "FAILED"
    if trace.get("status") == "CACHED":
        status = "CACHED"

    await session.execute(
        update(Task)
        .where(
            Task.run_id == run_id,
            Task.task_id == trace.get("task_id"),
            Task.attempt == trace.get("attempt", 1),
        )
        .values(
            status=status,
            exit_code=trace.get("exit"),
            complete_time=trace.get("complete"),
            duration_ms=trace.get("duration"),
            realtime_ms=trace.get("realtime"),
            cpu_percent=trace.get("%cpu"),
            peak_rss=trace.get("peak_rss"),
            peak_vmem=trace.get("peak_vmem"),
            read_bytes=trace.get("rchar"),
            write_bytes=trace.get("wchar"),
            error_message=trace.get("error_action") if status == "FAILED" else None,
            trace_data=trace,
            updated_at=datetime.now(timezone.utc),
        )
    )

    await _update_run_event_time(session, run_id)


async def _handle_run_completed(session: AsyncSession, run_id: str, event: dict) -> None:
    metadata = event.get("metadata", {})
    workflow = metadata.get("workflow", {})
    stats = metadata.get("stats", {})

    success = workflow.get("success", False)

    await session.execute(
        update(Run)
        .where(Run.run_id == run_id)
        .values(
            status="completed" if success else "failed",
            completed_at=_parse_timestamp(event["utcTime"]) if success else None,
            failed_at=_parse_timestamp(event["utcTime"]) if not success else None,
            exit_code=workflow.get("exitStatus"),
            error_message=workflow.get("errorMessage"),
            metrics={
                "duration_seconds": (workflow.get("duration", 0) or 0) / 1000,
                "tasks_total": stats.get("succeedCount", 0)
                + stats.get("failedCount", 0)
                + stats.get("cachedCount", 0),
                "tasks_succeeded": stats.get("succeedCount", 0),
                "tasks_failed": stats.get("failedCount", 0),
                "tasks_cached": stats.get("cachedCount", 0),
            },
            last_weblog_event_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )


async def _handle_run_error(session: AsyncSession, run_id: str, event: dict) -> None:
    metadata = event.get("metadata", {})
    workflow = metadata.get("workflow", {})

    await session.execute(
        update(Run)
        .where(Run.run_id == run_id)
        .values(
            status="failed",
            failed_at=_parse_timestamp(event["utcTime"]),
            error_message=workflow.get("errorMessage", "Unknown error"),
            last_weblog_event_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )


@router.post("/weblog")
async def process_weblog_event(
    pubsub_message: PubSubMessage,
    service: ServiceContext = Depends(get_service_context),
    session: AsyncSession = Depends(get_db_session),
):
    data = base64.b64decode(pubsub_message.message["data"]).decode()
    payload = json.loads(data)

    arc_run_id = payload["arc_run_id"]
    event = payload["event"]

    dedup_key = _make_dedup_key(arc_run_id, event)
    if await _is_duplicate(session, dedup_key):
        logger.info("Skipping duplicate event: %s", dedup_key)
        return {"status": "duplicate"}

    event_type = event["event"]

    try:
        match event_type:
            case "started":
                await _handle_run_started(session, arc_run_id, event)
            case "process_submitted":
                await _handle_task_submitted(session, arc_run_id, event)
            case "process_started":
                await _handle_task_started(session, arc_run_id, event)
            case "process_completed":
                await _handle_task_completed(session, arc_run_id, event)
            case "completed":
                await _handle_run_completed(session, arc_run_id, event)
            case "error":
                await _handle_run_error(session, arc_run_id, event)
            case _:
                logger.warning("Unknown event type: %s", event_type)

        await _record_event(session, dedup_key, event)
        await session.commit()

    except Exception as exc:
        logger.exception("Error processing weblog event: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(exc))

    return {"status": "processed"}
