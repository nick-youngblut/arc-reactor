from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg_pool import PoolTimeout
from starlette.websockets import WebSocketDisconnect

from backend.api.routes.chat import router as chat_router
from backend.config import settings


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chat_router)
    app.state.benchling_service = object()
    app.state.storage_service = object()
    app.state.database_service = object()
    app.state.checkpointer_service = SimpleNamespace(checkpointer=object())
    return app


def _enable_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", True, raising=False)


def test_websocket_reuses_agent_for_multiple_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_debug(monkeypatch)
    app = _build_app()

    agent_instances: list[object] = []
    stream_calls: list[object] = []

    def _create_agent(*_args, **_kwargs):
        agent = SimpleNamespace(agent=object())
        agent_instances.append(agent)
        return agent

    async def _stream_agent_response(agent, _messages, _config):
        stream_calls.append(agent)
        yield "ok"

    monkeypatch.setattr("backend.api.routes.chat.PipelineAgent.create", _create_agent)
    monkeypatch.setattr("backend.api.routes.chat.stream_agent_response", _stream_agent_response)

    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as websocket:
        assert websocket.receive_json()["type"] == "connected"

        websocket.send_json({"type": "message", "content": "hello"})
        assert websocket.receive_text() == "ok"

        websocket.send_json({"type": "message", "content": "again"})
        assert websocket.receive_text() == "ok"

    assert len(agent_instances) == 1
    assert stream_calls == [agent_instances[0].agent, agent_instances[0].agent]


def test_websocket_sends_error_when_agent_init_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_debug(monkeypatch)
    app = _build_app()

    def _create_agent(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("backend.api.routes.chat.PipelineAgent.create", _create_agent)

    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as websocket:
        assert websocket.receive_json()["type"] == "connected"
        payload = websocket.receive_json()
        assert payload["type"] == "error"
        assert "Failed to initialize agent" in payload["message"]
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_text()


def test_websocket_pool_timeout_keeps_connection_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_debug(monkeypatch)
    app = _build_app()

    def _create_agent(*_args, **_kwargs):
        return SimpleNamespace(agent=object())

    call_count = {"count": 0}

    async def _stream_agent_response(_agent, _messages, _config):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise PoolTimeout("timeout")
        yield "recovered"

    monkeypatch.setattr("backend.api.routes.chat.PipelineAgent.create", _create_agent)
    monkeypatch.setattr("backend.api.routes.chat.stream_agent_response", _stream_agent_response)

    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as websocket:
        assert websocket.receive_json()["type"] == "connected"

        websocket.send_json({"type": "message", "content": "first"})
        payload = websocket.receive_json()
        assert payload["type"] == "error"
        assert "temporarily unavailable" in payload["message"]

        websocket.send_json({"type": "message", "content": "second"})
        assert websocket.receive_text() == "recovered"
