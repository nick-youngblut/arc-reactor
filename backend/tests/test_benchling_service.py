from __future__ import annotations

from backend.services import benchling as benchling_module


class _Settings:
    benchling_warehouse_host = "benchling-warehouse.arcinstitute.org"
    benchling_warehouse_db = "benchling"
    benchling_warehouse_user = "benchling_reader"
    benchling_warehouse_password = "secret"


def test_build_benchling_url(monkeypatch) -> None:
    monkeypatch.delenv("BENCHLING_WAREHOUSE_USER", raising=False)
    monkeypatch.delenv("BENCHLING_WAREHOUSE_PASSWORD", raising=False)

    url = benchling_module._build_benchling_url(_Settings())
    assert "postgresql+asyncpg://benchling_reader:secret@" in url
    assert "sslmode=require" in url
