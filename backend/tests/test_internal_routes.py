from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.routes.internal.reconcile import reconcile_stale_runs
from backend.api.routes.internal.weblog import PubSubMessage, process_weblog_event
from backend.models.runs import Run
from backend.models.tasks import Task
from backend.utils.auth import ServiceContext


def _build_pubsub_message(payload: dict) -> PubSubMessage:
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return PubSubMessage(message={"data": encoded}, subscription="test")


async def _create_run(
    session: AsyncSession,
    run_id: str,
    status: str,
    batch_job_name: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> None:
    run = Run(
        run_id=run_id,
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        status=status,
        user_email="user@arc.org",
        user_name="Arc User",
        gcs_path=f"gs://arc-reactor-runs/runs/{run_id}",
        params={},
        sample_count=1,
        batch_job_name=batch_job_name,
        created_at=created_at or datetime.now(timezone.utc),
        updated_at=updated_at or datetime.now(timezone.utc),
    )
    session.add(run)
    await session.commit()


@pytest.mark.asyncio
async def test_reconcile_stale_runs_updates_status(session: AsyncSession, monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(minutes=20)
    orphan_time = now - timedelta(hours=25)

    await _create_run(
        session,
        "run-success",
        "running",
        batch_job_name="job-success",
        created_at=now - timedelta(hours=1),
        updated_at=stale_time,
    )
    await _create_run(
        session,
        "run-orphan",
        "running",
        batch_job_name="job-missing",
        created_at=orphan_time,
        updated_at=stale_time,
    )
    await _create_run(
        session,
        "run-submitted",
        "submitted",
        batch_job_name="job-running",
        created_at=now - timedelta(hours=1),
        updated_at=stale_time,
    )

    class _DummyJob:
        def __init__(self, state: str) -> None:
            self.status = type("Status", (), {"state": type("State", (), {"name": state})()})()

    class _DummyClient:
        def get_job(self, name: str):
            if name == "job-success":
                return _DummyJob("SUCCEEDED")
            if name == "job-running":
                return _DummyJob("RUNNING")
            raise Exception("not found")

    monkeypatch.setattr(
        "backend.api.routes.internal.reconcile.batch_v1.BatchServiceClient",
        lambda: _DummyClient(),
    )

    service = ServiceContext(email="arc-reactor-scheduler@test-project.iam.gserviceaccount.com")
    result = await reconcile_stale_runs(service=service, session=session)

    assert result["checked"] == 3
    assert {item["run_id"] for item in result["reconciled"]} == {
        "run-success",
        "run-orphan",
    }

    run_success = await session.get(Run, "run-success")
    assert run_success is not None
    assert run_success.status == "completed"

    run_orphan = await session.get(Run, "run-orphan")
    assert run_orphan is not None
    assert run_orphan.status == "failed"

    run_submitted = await session.get(Run, "run-submitted")
    assert run_submitted is not None
    assert run_submitted.status == "submitted"
