from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest

from backend.agents.tools.monitoring_tools import get_run_status, get_run_tasks, list_user_runs
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
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    error_message: str | None = None
    sample_count: int = 8


@dataclass
class _SummaryStub:
    total: int
    completed: int
    running: int
    submitted: int
    failed: int
    cached: int


class _TaskStub:
    def __init__(self, name: str, status: str, submit_time: int | None = None):
        self.name = name
        self.status = status
        self.duration_ms = 120_000
        self.cpu_percent = 75.5
        self.peak_rss = 8 * 1024**3
        self.exit_code = None
        self.submit_time = submit_time


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
    def __init__(self, run: _RunStub, *, session=None, summary=None, runs=None):
        self._run = run
        self.session = session
        self._summary = summary
        self._runs = runs or []

    async def get_run(self, run_id: str):
        if run_id != self._run.run_id:
            return None
        return self._run

    async def get_task_summary(self, _run_id: str):
        return self._summary

    async def list_runs(self, **_kwargs):
        return type(
            "RunList",
            (),
            {
                "runs": self._runs,
                "total": len(self._runs),
                "page": 1,
                "page_size": 25,
            },
        )()


class _Runtime:
    def __init__(self, run_store):
        self.config = {
            "configurable": {
                "run_store_service": run_store,
                "user_email": "dev@example.com",
                "user_name": "Developer",
            }
        }


@pytest.mark.asyncio
async def test_get_run_status_returns_summary():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    summary = _SummaryStub(total=10, completed=4, running=2, submitted=1, failed=1, cached=2)
    run_store = _RunStoreStub(run, summary=summary)
    runtime = _Runtime(run_store)

    output = await get_run_status.ainvoke({"run_id": "run-abc123", "runtime": runtime})

    assert "Run ID: run-abc123" in output
    assert "Status: running" in output
    assert "Task Progress" in output
    assert "Completed: 4" in output


@pytest.mark.asyncio
async def test_get_run_status_missing_run():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run)
    runtime = _Runtime(run_store)

    output = await get_run_status.ainvoke({"run_id": "run-missing", "runtime": runtime})

    assert "Error: Run not found" in output


@pytest.mark.asyncio
async def test_get_run_tasks_returns_table():
    tasks = [_TaskStub("FASTQC (1)", "COMPLETED", submit_time=10), _TaskStub("STAR_ALIGN (1)", "RUNNING")]
    session = _FakeSession(tasks)
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run, session=session)
    runtime = _Runtime(run_store)

    output = await get_run_tasks.ainvoke({"run_id": "run-abc123", "runtime": runtime})

    assert "Tasks for run-abc123" in output
    assert "FASTQC" in output
    assert "STAR_ALIGN" in output


@pytest.mark.asyncio
async def test_get_run_tasks_with_filter_no_results():
    session = _FakeSession([])
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run, session=session)
    runtime = _Runtime(run_store)

    output = await get_run_tasks.ainvoke(
        {"run_id": "run-abc123", "status_filter": "failed", "runtime": runtime}
    )

    assert "No failed tasks" in output


@pytest.mark.asyncio
async def test_list_user_runs_returns_table():
    now = datetime.now(timezone.utc)
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING, created_at=now)
    recent = _RunStub(run_id="run-def456", status=RunStatus.COMPLETED, created_at=now - timedelta(days=1))
    run_store = _RunStoreStub(run, runs=[run, recent])
    runtime = _Runtime(run_store)

    output = await list_user_runs.ainvoke({"runtime": runtime})

    assert "Your Recent Runs" in output
    assert "run-abc123" in output


@pytest.mark.asyncio
async def test_list_user_runs_respects_limit():
    now = datetime.now(timezone.utc)
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING, created_at=now)
    recent = _RunStub(run_id="run-def456", status=RunStatus.COMPLETED, created_at=now - timedelta(days=1))
    run_store = _RunStoreStub(run, runs=[run, recent])
    runtime = _Runtime(run_store)

    output = await list_user_runs.ainvoke({"runtime": runtime, "limit": 1})

    assert "run-abc123" in output
    assert "run-def456" not in output


@pytest.mark.asyncio
async def test_list_user_runs_rejects_invalid_status():
    run = _RunStub(run_id="run-abc123", status=RunStatus.RUNNING)
    run_store = _RunStoreStub(run)
    runtime = _Runtime(run_store)

    output = await list_user_runs.ainvoke({"runtime": runtime, "status_filter": "bad"})

    assert "Error: Invalid status_filter" in output
