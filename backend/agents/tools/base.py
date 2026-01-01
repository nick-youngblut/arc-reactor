from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from typing import Any, Iterable, Mapping, Sequence

from backend.config import settings
from backend.services.benchling import BenchlingService
from backend.services.storage import StorageService
from backend.utils.circuit_breaker import create_breakers

from toon.encoder import encode as toon_encode

try:  # LangChain v1 runtime injection
    from langchain.tools import ToolRuntime
except Exception:  # pragma: no cover - optional typing only
    ToolRuntime = Any  # type: ignore


DEFAULT_LIMIT = 50
MAX_LIMIT = 500
Q30_PASS_THRESHOLD = 90.0
Q30_WARN_THRESHOLD = 80.0


@dataclass(frozen=True)
class ToolContext:
    benchling: BenchlingService
    storage: StorageService | None
    user_email: str | None = None
    user_name: str | None = None


def parse_semicolon_delimited(value: str | None) -> list[str]:
    if not value or not isinstance(value, str):
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def compute_date_range(
    *,
    days_back: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
) -> tuple[str | None, str | None]:
    if days_back:
        today = date.today()
        return (today - timedelta(days=days_back)).isoformat(), today.isoformat()
    if start_date or end_date:
        return start_date, end_date
    if min_date or max_date:
        return min_date, max_date
    return None, None


def q30_status(q30_value: float | None) -> str:
    if q30_value is None:
        return "unknown"
    if q30_value >= Q30_PASS_THRESHOLD:
        return "PASS"
    if q30_value >= Q30_WARN_THRESHOLD:
        return "WARN"
    return "FAIL"


def format_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "No results found."
    return toon_encode([dict(row) for row in rows])


def format_run_summary(summary: Mapping[str, Any]) -> str:
    lines = [
        f"NGS Run: {summary.get('ngs_run', '')}",
        f"Pooled Sample: {summary.get('pooled_sample', '')}",
        f"Submitter: {summary.get('submitter', '')}",
        f"Instrument: {summary.get('instrument', '')}",
        f"Completion Date: {summary.get('completion_date', '')}",
        f"Sample Count: {summary.get('sample_count', '')}",
    ]
    run_path = summary.get("run_path")
    if run_path:
        lines.append(f"Run Path: {run_path}")
    return "\n".join(lines)


def format_ngs_run_results(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "No NGS runs matched your criteria."
    table = format_table(rows)
    return (
        f"Found {len(rows)} NGS runs matching your criteria:\n\n"
        f"{table}\n\n"
        "Use get_ngs_run_samples to retrieve detailed sample information for a specific run."
    )


def format_run_samples_result(
    summary: Mapping[str, Any],
    samples: Sequence[Mapping[str, Any]],
) -> str:
    table = format_table(samples)
    summary_text = format_run_summary(summary)
    return f"{summary_text}\n\nSamples:\n{table}"


def format_fastq_paths(rows: Sequence[Mapping[str, Any]], validated: bool) -> str:
    if not rows:
        return "No FASTQ paths found for the requested samples."
    table = format_table(rows)
    suffix = "\n\nAll files verified in GCS." if validated else ""
    return f"FASTQ paths for {len(rows)} samples:\n\n{table}{suffix}"


def format_qc_summary(summary: Mapping[str, Any], lane_rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        f"NGS Run QC Summary: {summary.get('ngs_run', '')}",
        "",
        "Run Metrics:",
        f"  Instrument: {summary.get('instrument', '')}",
        f"  Completion Date: {summary.get('completion_date', '')}",
        f"  Total Samples: {summary.get('sample_count', '')}",
        f"  Total Reads: {summary.get('total_reads', '')}",
        f"  Average Q30: {summary.get('avg_q30', '')}%",
        f"  Average Read Length: {summary.get('avg_read_length', '')}",
    ]
    if lane_rows:
        lines.append("")
        lines.append("Lane Summary (TOON):")
        lines.append(format_table(lane_rows))
    status = summary.get("qc_status", "unknown")
    lines.append("")
    lines.append(f"QC Status: {status}")
    return "\n".join(lines)


def _runtime_config(runtime: ToolRuntime | None) -> dict[str, Any]:
    if runtime is None:
        return {}
    config = getattr(runtime, "config", None)
    if isinstance(config, dict):
        return config
    return {}


def _runtime_configurable(runtime: ToolRuntime | None) -> dict[str, Any]:
    config = _runtime_config(runtime)
    return config.get("configurable", {}) if isinstance(config.get("configurable"), dict) else {}


@lru_cache(maxsize=1)
def _default_benchling_service() -> BenchlingService:
    breakers = create_breakers(settings)
    return BenchlingService.create(settings, breakers)


@lru_cache(maxsize=1)
def _default_storage_service() -> StorageService:
    return StorageService.create(settings)


def get_tool_context(runtime: ToolRuntime | None) -> ToolContext:
    configurable = _runtime_configurable(runtime)
    benchling = configurable.get("benchling_service") or _default_benchling_service()
    storage = configurable.get("storage_service")
    if storage is None:
        try:
            storage = _default_storage_service()
        except Exception:
            storage = None
    return ToolContext(
        benchling=benchling,
        storage=storage,
        user_email=configurable.get("user_email"),
        user_name=configurable.get("user_name"),
    )


def tool_error_handler(func):
    async def _wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as exc:
            return f"Error: {exc}"
        except Exception as exc:  # pragma: no cover - defensive
            return f"Error: {exc}"

    return _wrapper


def ensure_limit(limit: int | None, default: int = DEFAULT_LIMIT) -> int:
    if limit is None:
        return default
    return max(1, min(limit, MAX_LIMIT))


def flatten_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]
