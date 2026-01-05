from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from backend.agents.tools.troubleshooting_tools import analyze_failure, get_run_logs, get_task_logs
from backend.models.schemas.logs import LogEntry, TaskLogs
from backend.models.schemas.runs import RunStatus


@dataclass
class _RunStub:
    run_id: str
    status: RunStatus
    pipeline: str = "nf-core/scrnaseq"
    pipeline_version: str = "2.7.1"
    user_email: str = "dev@example.com"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    failed_at: datetime | None = None
    error_message: str | None = None


class _TaskStub:
    def __init__(self, name: str, exit_code: int | None = None, duration_ms: int | None = None, peak_rss: int | None = None):
        self.name = name
        self.status = "FAILED"
        self.exit_code = exit_code
        self.duration_ms = duration_ms
        self.peak_rss = peak_rss


class _FakeResult:
    def __init__(self, tasks):
        self._tasks = tasks

    def scalars(self):
        return self

    def all(self):
        return self._tasks


class _FakeSession:
    def __init__(self, tasks):
        self._tasks = tasks

    async def execute(self, _query):
        return _FakeResult(self._tasks)


class _RunStoreStub:
    def __init__(self, run: _RunStub, *, session=None):
        self._run = run
        self.session = session

    async def get_run(self, run_id: str):
        if run_id != self._run.run_id:
            return None
        return self._run


class _LogServiceStub:
    async def get_workflow_log(self, _run_id: str):
        return [
            LogEntry(timestamp=datetime.now(timezone.utc), source="nextflow", message="Test log")
        ]

    async def get_task_logs(self, _run_id: str, task_name: str):
        return TaskLogs(task_id=task_name, stdout="ok", stderr="Killed: out of memory")


class _StorageStub:
    bucket_name = "test-bucket"

    def get_file_content(self, _path: str, text: bool = False):
        return "line1\nline2\nline3"


class _Runtime:
    def __init__(self, run_store, log_service=None, storage=None):
        self.config = {
            "configurable": {
                "run_store_service": run_store,
                "log_service": log_service,
                "storage_service": storage,
                "user_email": "dev@example.com",
                "user_name": "Developer",
            }
        }


@pytest.mark.asyncio
async def test_get_run_logs_nextflow():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run)
    runtime = _Runtime(run_store, log_service=_LogServiceStub())

    output = await get_run_logs.ainvoke({"run_id": "run-abc123", "runtime": runtime})

    assert "Test log" in output


@pytest.mark.asyncio
async def test_get_run_logs_trace():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run)
    runtime = _Runtime(run_store, log_service=_LogServiceStub(), storage=_StorageStub())

    output = await get_run_logs.ainvoke({"run_id": "run-abc123", "log_type": "trace", "runtime": runtime})

    assert "line3" in output


@pytest.mark.asyncio
async def test_get_run_logs_invalid_type():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run)
    runtime = _Runtime(run_store, log_service=_LogServiceStub())

    output = await get_run_logs.ainvoke({"run_id": "run-abc123", "log_type": "invalid", "runtime": runtime})

    assert "Error: Invalid log_type" in output


@pytest.mark.asyncio
async def test_get_task_logs_stdout():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run)
    runtime = _Runtime(run_store, log_service=_LogServiceStub())

    output = await get_task_logs.ainvoke({
        "run_id": "run-abc123",
        "task_name": "STAR_ALIGN (1)",
        "log_stream": "stdout",
        "runtime": runtime,
    })

    assert "ok" in output


@pytest.mark.asyncio
async def test_get_task_logs_stderr():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run)
    runtime = _Runtime(run_store, log_service=_LogServiceStub())

    output = await get_task_logs.ainvoke({
        "run_id": "run-abc123",
        "task_name": "STAR_ALIGN (1)",
        "runtime": runtime,
    })

    assert "Killed" in output


@pytest.mark.asyncio
async def test_analyze_failure_identifies_oom():
    run = _RunStub(
        run_id="run-failed",
        status=RunStatus.FAILED,
        failed_at=datetime.now(timezone.utc),
    )
    tasks = [_TaskStub("STAR_ALIGN (1)", exit_code=137, duration_ms=3_600_000, peak_rss=32 * 1024**3)]
    session = _FakeSession(tasks)
    run_store = _RunStoreStub(run, session=session)
    runtime = _Runtime(run_store, log_service=_LogServiceStub())

    output = await analyze_failure.ainvoke({"run_id": "run-failed", "runtime": runtime})

    assert "Failure Analysis" in output
    assert "Out of memory" in output


@pytest.mark.asyncio
async def test_analyze_failure_rejects_non_failed_run():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run)
    runtime = _Runtime(run_store, log_service=_LogServiceStub())

    output = await analyze_failure.ainvoke({"run_id": "run-abc123", "runtime": runtime})

    assert "Error: Run is not in failed state" in output
