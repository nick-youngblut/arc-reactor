from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from langchain_core.tools import tool
from sqlalchemy import func, select

from backend.agents.tools.base import format_table, get_tool_context, tool_error_handler
from backend.config import settings
from backend.models.tasks import Task
from backend.models.schemas.runs import RunStatus
from backend.services.database import DatabaseService
from backend.services.runs import RunStoreService


MAX_TASK_LIMIT = 200
MAX_RUN_LIMIT = 50
MAX_DAYS_BACK = 90


def _runtime_config(runtime: Any | None) -> dict[str, Any]:
    if runtime is None:
        return {}
    config = getattr(runtime, "config", None)
    return config if isinstance(config, dict) else {}


def _runtime_configurable(runtime: Any | None) -> dict[str, Any]:
    config = _runtime_config(runtime)
    configurable = config.get("configurable")
    return configurable if isinstance(configurable, dict) else {}


async def _get_run_store(runtime: Any | None) -> tuple[RunStoreService, Any | None]:
    configurable = _runtime_configurable(runtime)
    run_store = configurable.get("run_store_service")
    if run_store is not None and hasattr(run_store, "get_run"):
        return run_store, None

    database_service = configurable.get("database_service")
    if database_service is None:
        database_service = DatabaseService.create(settings)

    session = await anext(database_service.get_session())
    return RunStoreService.create(session, settings), session


async def _close_session(session: Any | None) -> None:
    if session is None:
        return
    await session.close()


def _format_duration_ms(duration_ms: int | None) -> str:
    if not duration_ms:
        return "-"
    seconds = duration_ms / 1000.0
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60.0
    return f"{hours:.1f}h"


def _format_cpu_percent(cpu_percent: float | None) -> str:
    if cpu_percent is None:
        return "-"
    return f"{cpu_percent:.1f}%"


def _format_memory_gb(value: int | None) -> str:
    if value is None:
        return "-"
    gb = value / (1024**3)
    return f"{gb:.1f}"


async def _get_task_summary(run_store: Any, session: Any | None, run_id: str) -> dict[str, int] | None:
    if hasattr(run_store, "get_task_summary"):
        summary = await run_store.get_task_summary(run_id)
        if summary is None:
            return None
        return {
            "total": int(getattr(summary, "total", 0)),
            "completed": int(getattr(summary, "completed", 0)),
            "running": int(getattr(summary, "running", 0)),
            "submitted": int(getattr(summary, "submitted", 0)),
            "failed": int(getattr(summary, "failed", 0)),
            "cached": int(getattr(summary, "cached", 0)),
        }

    session_to_use = session or getattr(run_store, "session", None)
    if session_to_use is None:
        return None

    result = await session_to_use.execute(
        select(Task.status, func.count(Task.id).label("count"))
        .where(Task.run_id == run_id)
        .group_by(Task.status)
    )
    counts = {row.status: row.count for row in result}
    return {
        "total": int(sum(counts.values())),
        "completed": int(counts.get("COMPLETED", 0)),
        "running": int(counts.get("RUNNING", 0)),
        "submitted": int(counts.get("SUBMITTED", 0)),
        "failed": int(counts.get("FAILED", 0)),
        "cached": int(counts.get("CACHED", 0)),
    }


def _validate_status_filter(status_filter: str | None) -> RunStatus | None:
    if not status_filter:
        return None
    try:
        return RunStatus(status_filter)
    except ValueError:
        raise ValueError("Invalid status_filter")


@tool
@tool_error_handler
async def get_run_status(run_id: str, runtime: Any | None = None) -> str:
    """
    Get status and task progress for a pipeline run.

    Args:
        run_id: The run identifier

    Returns:
        Status summary with task progress.
    """
    if not run_id:
        return "Error: run_id is required."

    context = get_tool_context(runtime)
    run_store, session = await _get_run_store(runtime)
    try:
        run = await run_store.get_run(run_id)
        if not run:
            return "Error: Run not found."
        if context.user_email and run.user_email != context.user_email:
            return "Error: Access denied."

        summary = await _get_task_summary(run_store, session, run_id)
        lines = [
            f"Run ID: {run.run_id}",
            f"Pipeline: {run.pipeline} {run.pipeline_version}",
            f"Status: {run.status.value}",
            f"Created: {run.created_at.isoformat()}",
        ]
        if run.started_at:
            lines.append(f"Started: {run.started_at.isoformat()}")
        if run.completed_at:
            lines.append(f"Completed: {run.completed_at.isoformat()}")
        if run.failed_at:
            lines.append(f"Failed: {run.failed_at.isoformat()}")
        if run.error_message:
            lines.append(f"Error: {run.error_message}")

        if summary:
            lines.extend(
                [
                    "",
                    "Task Progress:",
                    f"  Total: {summary['total']}",
                    f"  Completed: {summary['completed']}",
                    f"  Running: {summary['running']}",
                    f"  Submitted: {summary['submitted']}",
                    f"  Failed: {summary['failed']}",
                    f"  Cached: {summary['cached']}",
                ]
            )

        return "\n".join(lines)
    finally:
        await _close_session(session)


@tool
@tool_error_handler
async def get_run_tasks(
    run_id: str,
    status_filter: str | None = None,
    limit: int = 50,
    runtime: Any | None = None,
) -> str:
    """
    Get task-level details for a pipeline run.

    Args:
        run_id: The run identifier
        status_filter: Filter by status (running, completed, failed, pending, cached)
        limit: Maximum tasks to return (default 50, max 200)

    Returns:
        Table of tasks with name, status, duration, and resource usage.
    """
    if not run_id:
        return "Error: run_id is required."

    limit = max(1, min(limit, MAX_TASK_LIMIT))
    normalized_status = status_filter.upper() if status_filter else None

    context = get_tool_context(runtime)
    run_store, session = await _get_run_store(runtime)
    try:
        run = await run_store.get_run(run_id)
        if not run:
            return "Error: Run not found."
        if context.user_email and run.user_email != context.user_email:
            return "Error: Access denied."

        session_to_use = session or getattr(run_store, "session", None)
        if session_to_use is None:
            return "Error: Task data unavailable."

        query = select(Task).where(Task.run_id == run_id)
        if normalized_status:
            query = query.where(Task.status == normalized_status)
        query = query.order_by(Task.submit_time.desc().nullslast()).limit(limit)

        result = await session_to_use.execute(query)
        tasks = result.scalars().all()

        if not tasks:
            if normalized_status:
                return f"No {status_filter} tasks found for {run_id}."
            return f"No tasks found for {run_id}."

        rows = []
        for task in tasks:
            rows.append(
                {
                    "task_name": task.name,
                    "status": task.status,
                    "duration": _format_duration_ms(task.duration_ms),
                    "cpus": _format_cpu_percent(task.cpu_percent),
                    "memory_gb": _format_memory_gb(task.peak_rss),
                    "exit_code": task.exit_code if task.exit_code is not None else "-",
                }
            )

        table = format_table(rows)
        return f"Tasks for {run_id} (showing {len(rows)}):\n\n{table}"
    finally:
        await _close_session(session)


@tool
@tool_error_handler
async def list_user_runs(
    status_filter: str | None = None,
    pipeline_filter: str | None = None,
    days_back: int = 30,
    limit: int = 20,
    runtime: Any | None = None,
) -> str:
    """
    List recent pipeline runs for the current user.

    Args:
        status_filter: Filter by status (pending, submitted, running, completed, failed, cancelled)
        pipeline_filter: Filter by pipeline name
        days_back: How far back to search (default 30 days, max 90)
        limit: Maximum runs to return (default 20, max 50)

    Returns:
        Table of runs with ID, pipeline, status, and timing.
    """
    limit = max(1, min(limit, MAX_RUN_LIMIT))
    if days_back <= 0:
        return "Error: days_back must be positive."
    if days_back > MAX_DAYS_BACK:
        days_back = MAX_DAYS_BACK

    status = _validate_status_filter(status_filter) if status_filter else None

    context = get_tool_context(runtime)
    if not context.user_email:
        return "Error: user_email is required."

    run_store, session = await _get_run_store(runtime)
    try:
        response = await run_store.list_runs(
            user_email=context.user_email,
            status=status,
            pipeline=pipeline_filter,
            page=1,
            page_size=max(limit, 25),
        )

        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        filtered = [run for run in response.runs if run.created_at >= cutoff]
        filtered = filtered[:limit]

        if not filtered:
            return "No runs found for the requested filters."

        rows = []
        for run in filtered:
            rows.append(
                {
                    "run_id": run.run_id,
                    "pipeline": run.pipeline,
                    "status": run.status.value,
                    "samples": run.sample_count,
                    "created": run.created_at.isoformat(),
                }
            )

        table = format_table(rows)
        return f"Your Recent Runs ({len(filtered)} of {response.total}):\n\n{table}"
    finally:
        await _close_session(session)
