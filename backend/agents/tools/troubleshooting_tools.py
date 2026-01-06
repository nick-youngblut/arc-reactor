"""Troubleshooting tools for failed pipeline runs."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from sqlalchemy import select

from backend.agents.tools.base import get_tool_context, tool_error_handler
from backend.config import settings
from backend.models.tasks import Task
from backend.models.schemas.runs import RunStatus
from backend.services.database import DatabaseService
from backend.services.logs import LogService
from backend.services.runs import RunStoreService


MAX_LOG_TAIL = 500
MAX_TASK_LOG_TAIL = 1000


def _runtime_config(runtime: Any | None) -> dict[str, Any]:
    """Extract the runtime config dict from a tool runtime.

    Args:
        runtime: Tool runtime passed by LangChain/DeepAgents.

    Returns:
        Configuration dictionary (empty if unavailable).
    """
    if runtime is None:
        return {}
    config = getattr(runtime, "config", None)
    return config if isinstance(config, dict) else {}


def _runtime_configurable(runtime: Any | None) -> dict[str, Any]:
    """Extract configurable overrides from runtime config.

    Args:
        runtime: Tool runtime passed by LangChain/DeepAgents.

    Returns:
        Configurable dict (empty if unavailable).
    """
    config = _runtime_config(runtime)
    configurable = config.get("configurable")
    return configurable if isinstance(configurable, dict) else {}


async def _get_run_store(runtime: Any | None) -> tuple[RunStoreService, Any | None]:
    """Resolve the run store service and optional session.

    Args:
        runtime: Tool runtime passed by LangChain/DeepAgents.

    Returns:
        Tuple of (RunStoreService, session or None).
    """
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
    """Close the database session if provided.

    Args:
        session: SQLAlchemy session or None.
    """
    if session is None:
        return
    await session.close()


def _get_log_service(runtime: Any | None) -> LogService | None:
    """Resolve the log service from runtime or storage.

    Args:
        runtime: Tool runtime passed by LangChain/DeepAgents.

    Returns:
        LogService instance or None when unavailable.
    """
    configurable = _runtime_configurable(runtime)
    log_service = configurable.get("log_service")
    if log_service is not None:
        return log_service

    context = get_tool_context(runtime)
    if context.storage is None:
        return None
    return LogService.create(context.storage, settings)


def _tail_lines(content: str, tail: int) -> str:
    """Return the last N lines of content.

    Args:
        content: Full log content.
        tail: Line count to return.

    Returns:
        Trailing lines joined by newlines.
    """
    lines = content.splitlines()
    return "\n".join(lines[-tail:]) if lines else ""


def _diagnose_error(log_text: str, exit_code: int | None) -> tuple[str, str] | None:
    """Infer common failure patterns from log output.

    Args:
        log_text: Log content (stderr or stdout).
        exit_code: Exit code from the task, if any.

    Returns:
        Tuple of (diagnosis, suggested_fix) or None if unknown.
    """
    haystack = log_text.lower()
    if exit_code == 137 or "oom" in haystack or "out of memory" in haystack or "killed" in haystack:
        return (
            "Out of memory (OOM killed)",
            "Increase memory allocation for the failing process.",
        )
    if "no space left" in haystack or "disk quota" in haystack:
        return (
            "Insufficient disk space",
            "Increase work directory storage or clean intermediate files.",
        )
    if "permission denied" in haystack:
        return (
            "Permission denied",
            "Check service account permissions and file access policies.",
        )
    if "no such file" in haystack or "not found" in haystack:
        return (
            "Missing input file",
            "Verify input paths and samplesheet entries.",
        )
    if "connection refused" in haystack or "timeout" in haystack:
        return (
            "Network or service timeout",
            "Retry the run or verify external service availability.",
        )
    return None


@tool
@tool_error_handler
async def get_run_logs(
    run_id: str,
    log_type: str = "nextflow",
    tail: int = 100,
    runtime: Any | None = None,
) -> str:
    """
    Get execution logs for a pipeline run.

    Args:
        run_id: The run identifier
        log_type: Type of log (nextflow, trace). Default: nextflow
        tail: Number of lines from end (default 100, max 500)

    Returns:
        Log content (last N lines).
    """
    if not run_id:
        return "Error: run_id is required."

    tail = max(1, min(tail, MAX_LOG_TAIL))
    log_type = log_type.lower().strip()
    if log_type not in {"nextflow", "trace"}:
        return "Error: Invalid log_type. Use 'nextflow' or 'trace'."

    context = get_tool_context(runtime)
    run_store, session = await _get_run_store(runtime)
    try:
        run = await run_store.get_run(run_id)
        if not run:
            return "Error: Run not found."
        if context.user_email and run.user_email != context.user_email:
            return "Error: Access denied."

        log_service = _get_log_service(runtime)
        if log_service is None:
            return "Error: Log service unavailable."

        if log_type == "nextflow":
            entries = await log_service.get_workflow_log(run_id)
            if not entries:
                return "No log entries found."
            entries = entries[-tail:]
            lines = [f"{entry.timestamp.isoformat()} {entry.message}" for entry in entries]
            return "\n".join(lines)

        if context.storage is None:
            return "Error: Storage service unavailable."
        path = f"gs://{context.storage.bucket_name}/runs/{run_id}/logs/trace.txt"
        try:
            content = context.storage.get_file_content(path, text=True)
        except Exception:
            return "No trace log found."

        return _tail_lines(content, tail)
    finally:
        await _close_session(session)


@tool
@tool_error_handler
async def get_task_logs(
    run_id: str,
    task_name: str,
    log_stream: str = "stderr",
    tail: int = 200,
    runtime: Any | None = None,
) -> str:
    """
    Get logs for a specific task (useful for debugging failures).

    Args:
        run_id: The run identifier
        task_name: Name of the task (e.g., "STAR_ALIGN (1)")
        log_stream: Which stream (stdout, stderr). Default: stderr
        tail: Number of lines from end (default 200, max 1000)

    Returns:
        Task log content.
    """
    if not run_id or not task_name:
        return "Error: run_id and task_name are required."

    log_stream = log_stream.lower().strip()
    if log_stream not in {"stdout", "stderr"}:
        return "Error: Invalid log_stream. Use 'stdout' or 'stderr'."

    tail = max(1, min(tail, MAX_TASK_LOG_TAIL))
    context = get_tool_context(runtime)
    run_store, session = await _get_run_store(runtime)
    try:
        run = await run_store.get_run(run_id)
        if not run:
            return "Error: Run not found."
        if context.user_email and run.user_email != context.user_email:
            return "Error: Access denied."

        log_service = _get_log_service(runtime)
        if log_service is None:
            return "Error: Log service unavailable."

        logs = await log_service.get_task_logs(run_id, task_name)
        content = logs.stdout if log_stream == "stdout" else logs.stderr
        if not content:
            return "No logs found for that task."

        return _tail_lines(content, tail)
    finally:
        await _close_session(session)


@tool
@tool_error_handler
async def analyze_failure(run_id: str, runtime: Any | None = None) -> str:
    """
    Analyze why a pipeline run failed and suggest fixes.

    Args:
        run_id: The run identifier

    Returns:
        Diagnosis with error details, likely cause, and suggested fixes.
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
        if run.status != RunStatus.FAILED:
            return "Error: Run is not in failed state."

        session_to_use = session or getattr(run_store, "session", None)
        if session_to_use is None:
            return "Error: Task data unavailable."

        result = await session_to_use.execute(
            select(Task).where(Task.run_id == run_id, Task.status == "FAILED")
        )
        failed_tasks = result.scalars().all()

        if not failed_tasks:
            return "No failed tasks found for this run."

        log_service = _get_log_service(runtime)

        lines = [
            f"# Failure Analysis for {run_id}",
            "",
            f"**Pipeline**: {run.pipeline} {run.pipeline_version}",
            f"**Status**: {run.status.value}",
            f"**Failed at**: {run.failed_at.isoformat() if run.failed_at else 'unknown'}",
        ]

        if run.error_message:
            lines.append(f"**Run Error**: {run.error_message}")

        lines.extend(["", f"## Failed Tasks ({len(failed_tasks)})", ""])

        for task in failed_tasks:
            lines.append(f"### {task.name}")
            lines.append(f"- Exit code: {task.exit_code if task.exit_code is not None else 'unknown'}")
            if task.duration_ms:
                seconds = task.duration_ms / 1000.0
                lines.append(f"- Duration: {seconds:.0f}s")
            if task.peak_rss:
                mem_gb = task.peak_rss / (1024**3)
                lines.append(f"- Memory: {mem_gb:.1f} GB")

            diagnosis = None
            if log_service is not None:
                try:
                    logs = await log_service.get_task_logs(run_id, task.name)
                    diagnosis = _diagnose_error(logs.stderr or logs.stdout, task.exit_code)
                except Exception:
                    diagnosis = None

            if diagnosis:
                lines.append("")
                lines.append(f"**Diagnosis**: {diagnosis[0]}")
                lines.append(f"**Fix**: {diagnosis[1]}")

            lines.append("")

        lines.extend(
            [
                "## Suggested Actions",
                "",
                "1. Review the failed task logs for specific errors.",
                "2. Update your config to address the diagnosed issue.",
                "3. Use recover_run to resume from the last successful checkpoint.",
            ]
        )

        return "\n".join(lines)
    finally:
        await _close_session(session)
