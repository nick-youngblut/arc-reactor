from __future__ import annotations

from fastapi.testclient import TestClient

from backend.dependencies import (
    get_benchling_service,
    get_breakers,
    get_checkpointer_service,
    get_database_service,
    get_gemini_service,
    get_storage_service,
)
from backend.main import app
from backend.utils.circuit_breaker import Breakers
from circuitbreaker import CircuitBreaker


class _DummyService:
    def __init__(self, ok: bool = True) -> None:
        self._ok = ok

    async def health_check(self) -> bool:
        return self._ok


class _DummyStorage:
    def __init__(self, ok: bool = True) -> None:
        self._ok = ok

    def health_check(self) -> bool:
        return self._ok


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "arc-reactor"


def test_readiness_endpoint(monkeypatch) -> None:
    dummy_breakers = Breakers(benchling=CircuitBreaker(), gemini=CircuitBreaker())

    app.dependency_overrides[get_benchling_service] = lambda: _DummyService(True)
    app.dependency_overrides[get_database_service] = lambda: _DummyService(True)
    app.dependency_overrides[get_storage_service] = lambda: _DummyStorage(True)
    app.dependency_overrides[get_gemini_service] = lambda: _DummyService(True)
    app.dependency_overrides[get_checkpointer_service] = lambda: _DummyService(True)
    app.dependency_overrides[get_breakers] = lambda: dummy_breakers

    async def _batch_ok() -> bool:
        return True

    monkeypatch.setattr(
        "backend.api.routes.health.check_batch_access", _batch_ok, raising=False
    )

    client = TestClient(app)
    try:
        response = client.get("/ready")
        assert response.status_code == 200
        payload = response.json()
        assert payload["healthy"] is True
        assert payload["degraded"] is False
    finally:
        app.dependency_overrides.clear()
