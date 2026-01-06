from types import SimpleNamespace

import pytest

from backend.services.checkpointer import _build_checkpointer_connection_string


def _clear_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("DATABASE_URL", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_HOST", "DB_PORT"):
        monkeypatch.delenv(key, raising=False)


def test_build_connection_string_with_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/dbname")

    settings = SimpleNamespace()
    assert (
        _build_checkpointer_connection_string(settings)
        == "postgresql://user:pass@host:5432/dbname"
    )


def test_build_connection_string_converts_asyncpg_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host:5432/dbname")

    settings = SimpleNamespace()
    assert (
        _build_checkpointer_connection_string(settings)
        == "postgresql://user:pass@host:5432/dbname"
    )


def test_build_connection_string_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_db_env(monkeypatch)

    settings = SimpleNamespace(
        db_user="arc",
        db_password="secret",
        db_name="reactor",
        db_host="localhost",
        db_port=6543,
    )
    assert (
        _build_checkpointer_connection_string(settings)
        == "postgresql://arc:secret@localhost:6543/reactor"
    )


def test_build_connection_string_missing_config(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_db_env(monkeypatch)

    settings = SimpleNamespace()
    with pytest.raises(ValueError, match="Database configuration is missing"):
        _build_checkpointer_connection_string(settings)
