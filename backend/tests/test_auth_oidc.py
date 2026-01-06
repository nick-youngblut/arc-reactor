from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.utils import auth


def _make_request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/internal/weblog",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "scheme": "https",
        "server": ("example.com", 443),
        "client": ("127.0.0.1", 1234),
    }
    return Request(scope)


def test_verify_oidc_token_allows_service_account(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_verify(_: str, __: Any, audience: str) -> dict[str, str]:
        assert audience == "https://example.com/api/internal/weblog"
        return {"email": "arc-reactor-pubsub@test-project.iam.gserviceaccount.com"}

    monkeypatch.setattr(auth.id_token, "verify_oauth2_token", fake_verify)
    monkeypatch.setattr(auth.settings, "get", lambda key, default=None: "test-project")

    claims = auth.verify_oidc_token("token", "https://example.com/api/internal/weblog")
    assert claims["email"].startswith("arc-reactor-pubsub")


def test_verify_oidc_token_rejects_unknown_service_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify(_: str, __: Any, audience: str) -> dict[str, str]:
        assert audience == "https://example.com/api/internal/weblog"
        return {"email": "other@test-project.iam.gserviceaccount.com"}

    monkeypatch.setattr(auth.id_token, "verify_oauth2_token", fake_verify)
    monkeypatch.setattr(auth.settings, "get", lambda key, default=None: "test-project")

    with pytest.raises(HTTPException) as excinfo:
        auth.verify_oidc_token("token", "https://example.com/api/internal/weblog")

    assert excinfo.value.status_code == 403


def test_verify_oidc_token_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_verify(_: str, __: Any, audience: str) -> dict[str, str]:
        raise ValueError("bad token")

    monkeypatch.setattr(auth.id_token, "verify_oauth2_token", fake_verify)

    with pytest.raises(HTTPException) as excinfo:
        auth.verify_oidc_token("token", "https://example.com/api/internal/weblog")

    assert excinfo.value.status_code == 401


@pytest.mark.asyncio
async def test_get_service_context(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_verify(_: str, __: Any, audience: str) -> dict[str, str]:
        assert audience == "https://example.com/api/internal/weblog"
        return {"email": "arc-reactor-pubsub@test-project.iam.gserviceaccount.com"}

    monkeypatch.setattr(auth.id_token, "verify_oauth2_token", fake_verify)
    monkeypatch.setattr(auth.settings, "get", lambda key, default=None: "test-project")

    request = _make_request({"Authorization": "Bearer token"})
    context = await auth.get_service_context(request)

    assert context.email == "arc-reactor-pubsub@test-project.iam.gserviceaccount.com"
    assert context.auth_type == auth.AuthType.OIDC
