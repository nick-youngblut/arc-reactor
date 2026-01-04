from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg_pool import PoolTimeout

from backend.api.routes.chat_rest import router as chat_rest_router
from backend.dependencies import get_current_user_context
from backend.utils.auth import UserContext


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chat_rest_router)
    app.state.benchling_service = object()
    app.state.storage_service = object()
    app.state.database_service = object()
    app.state.checkpointer_service = SimpleNamespace(checkpointer=object())
    return app


def test_chat_rest_streaming_success(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _build_app()

    def _create_agent(*_args, **_kwargs):
        return SimpleNamespace(agent=object())

    async def _stream_agent_response(_agent, _messages, _config):
        yield "ok"

    monkeypatch.setattr("backend.api.routes.chat_rest.PipelineAgent.create", _create_agent)
    monkeypatch.setattr("backend.api.routes.chat_rest.stream_agent_response", _stream_agent_response)

    app.dependency_overrides[get_current_user_context] = lambda: UserContext(
        email="dev@example.com",
        name="Developer",
    )

    client = TestClient(app)
    with client.stream("POST", "/chat", json={"type": "message", "content": "hi"}) as response:
        assert response.status_code == 200
        lines = [line for line in response.iter_lines() if line]
        assert lines[0] == "data: ok"

    app.dependency_overrides.clear()


def test_chat_rest_pool_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _build_app()

    def _create_agent(*_args, **_kwargs):
        return SimpleNamespace(agent=object())

    async def _stream_agent_response(_agent, _messages, _config):
        raise PoolTimeout("timeout")

    monkeypatch.setattr("backend.api.routes.chat_rest.PipelineAgent.create", _create_agent)
    monkeypatch.setattr("backend.api.routes.chat_rest.stream_agent_response", _stream_agent_response)

    app.dependency_overrides[get_current_user_context] = lambda: UserContext(
        email="dev@example.com",
        name="Developer",
    )

    client = TestClient(app)
    with client.stream("POST", "/chat", json={"type": "message", "content": "hi"}) as response:
        assert response.status_code == 200
        lines = [line for line in response.iter_lines() if line]
        assert lines[0] == 'data: 3:"Service temporarily unavailable"'
        assert lines[1] == 'd:{"finishReason":"error"}'

    app.dependency_overrides.clear()
