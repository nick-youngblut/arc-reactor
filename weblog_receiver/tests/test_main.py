from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.models import Base
from backend.models.runs import Run


@pytest.fixture
def app_client(monkeypatch, tmp_path):
    db_path = tmp_path / "weblog.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("GCP_PROJECT", "test-project")
    monkeypatch.setenv("PUBSUB_TOPIC", "arc-reactor-weblog-events")

    class _BootstrapPublisher:
        def topic_path(self, project: str, topic: str) -> str:
            return f"projects/{project}/topics/{topic}"

    from google.cloud import pubsub_v1

    monkeypatch.setattr(pubsub_v1, "PublisherClient", lambda: _BootstrapPublisher())

    import importlib
    from weblog_receiver import main as weblog_main

    importlib.reload(weblog_main)

    published = []

    class _Future:
        def __init__(self, message_id: str) -> None:
            self._message_id = message_id

        def result(self, timeout: int | None = None) -> str:
            return self._message_id

    class _Publisher:
        def publish(self, topic_path: str, *, data: bytes, ordering_key: str):
            payload = json.loads(data.decode())
            published.append(
                {
                    "topic": topic_path,
                    "ordering_key": ordering_key,
                    "payload": payload,
                }
            )
            return _Future("message-1")

    monkeypatch.setattr(weblog_main, "publisher", _Publisher())
    monkeypatch.setattr(
        weblog_main,
        "TOPIC_PATH",
        "projects/test-project/topics/arc-reactor-weblog-events",
    )

    async def _init_db() -> None:
        async with weblog_main.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init_db())

    client = TestClient(weblog_main.app)
    return SimpleNamespace(client=client, main=weblog_main, published=published)


def _insert_run(main, *, run_id: str, status: str, secret: str) -> None:
    secret_hash = main.hashlib.sha256(secret.encode()).hexdigest()
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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        weblog_secret_hash=secret_hash,
    )

    async def _commit() -> None:
        async with main.async_session() as session:
            session.add(run)
            await session.commit()

    asyncio.run(_commit())


def test_receive_weblog_event_publishes(app_client) -> None:
    _insert_run(app_client.main, run_id="run-123", status="running", secret="secret")

    payload = {
        "runName": "friendly_turing",
        "runId": "nf-uuid",
        "event": "started",
        "utcTime": "2025-01-01T00:00:00Z",
        "trace": None,
        "metadata": None,
    }

    response = app_client.client.post("/weblog/run-123/secret", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

    assert app_client.published
    published = app_client.published[0]
    assert published["ordering_key"] == "run-123"
    assert published["payload"]["arc_run_id"] == "run-123"


def test_receive_weblog_event_invalid_secret(app_client) -> None:
    _insert_run(app_client.main, run_id="run-123", status="running", secret="secret")

    payload = {
        "runName": "friendly_turing",
        "runId": "nf-uuid",
        "event": "started",
        "utcTime": "2025-01-01T00:00:00Z",
    }

    response = app_client.client.post("/weblog/run-123/badsecret", json=payload)
    assert response.status_code == 403


def test_receive_weblog_event_terminal_run(app_client) -> None:
    _insert_run(app_client.main, run_id="run-123", status="completed", secret="secret")

    payload = {
        "runName": "friendly_turing",
        "runId": "nf-uuid",
        "event": "started",
        "utcTime": "2025-01-01T00:00:00Z",
    }

    response = app_client.client.post("/weblog/run-123/secret", json=payload)
    assert response.status_code == 409
