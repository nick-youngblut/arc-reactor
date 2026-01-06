"""Output retrieval tools for pipeline runs."""

from __future__ import annotations

import fnmatch
from typing import Any

from langchain_core.tools import tool

from backend.agents.tools.base import format_table, get_tool_context, tool_error_handler
from backend.config import settings
from backend.services.database import DatabaseService
from backend.services.runs import RunStoreService


MAX_EXPIRATION_MINUTES = 1440


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


def _normalize_results_path(path: str) -> str:
    """Normalize a results path to be relative to the results directory.

    Args:
        path: Raw path or filename.

    Returns:
        Normalized relative path without leading results/ prefix.
    """
    normalized = path.lstrip("/")
    if normalized.startswith("results/"):
        return normalized[len("results/") :]
    return normalized


@tool
@tool_error_handler
async def get_run_outputs(
    run_id: str,
    path_filter: str | None = None,
    runtime: Any | None = None,
) -> str:
    """
    List output files for a completed pipeline run.

    Args:
        run_id: The run identifier
        path_filter: Optional glob pattern (e.g., "*.h5ad", "multiqc/*")

    Returns:
        List of output files with sizes.
    """
    if not run_id:
        return "Error: run_id is required."

    context = get_tool_context(runtime)
    if context.storage is None:
        return "Error: Storage service unavailable."

    run_store, session = await _get_run_store(runtime)
    try:
        run = await run_store.get_run(run_id)
        if not run:
            return "Error: Run not found."
        if context.user_email and run.user_email != context.user_email:
            return "Error: Access denied."

        files = context.storage.get_run_files(run_id)
        results = files.get("results", [])
        rows = []
        for entry in results:
            name = str(entry.get("name", ""))
            display_name = _normalize_results_path(name)
            if path_filter and not fnmatch.fnmatch(display_name, path_filter):
                continue
            rows.append(
                {
                    "path": display_name,
                    "size": entry.get("size"),
                    "updated": entry.get("updated"),
                }
            )

        if not rows:
            return "No output files found for this run."

        table = format_table(rows)
        return f"Outputs for {run_id} (showing {len(rows)}):\n\n{table}"
    finally:
        await _close_session(session)


@tool
@tool_error_handler
async def get_signed_download_url(
    run_id: str,
    file_path: str,
    expiration_minutes: int = 60,
    runtime: Any | None = None,
) -> str:
    """
    Generate a signed URL for downloading a run output file.

    Args:
        run_id: The run identifier
        file_path: Path relative to results directory
        expiration_minutes: URL validity period (default 60, max 1440)

    Returns:
        Signed URL for direct download.
    """
    if not run_id or not file_path:
        return "Error: run_id and file_path are required."

    expiration_minutes = max(1, min(expiration_minutes, MAX_EXPIRATION_MINUTES))

    context = get_tool_context(runtime)
    if context.storage is None:
        return "Error: Storage service unavailable."

    run_store, session = await _get_run_store(runtime)
    try:
        run = await run_store.get_run(run_id)
        if not run:
            return "Error: Run not found."
        if context.user_email and run.user_email != context.user_email:
            return "Error: Access denied."

        normalized = _normalize_results_path(file_path)
        gcs_path = f"gs://{context.storage.bucket_name}/runs/{run_id}/results/{normalized}"

        files = context.storage.get_run_files(run_id)
        result_files = files.get("results", [])
        if not any(_normalize_results_path(str(entry.get("name", ""))) == normalized for entry in result_files):
            return "Error: File not found in results directory."

        signed_url = context.storage.generate_signed_url(gcs_path, expiration_minutes)
        return signed_url
    finally:
        await _close_session(session)
