from __future__ import annotations

import os

import pytest

from backend.config import settings
from backend.services.benchling import BenchlingService
from backend.services.database import DatabaseService
from backend.services.gemini import GeminiService
from backend.services.storage import StorageService
from backend.utils.circuit_breaker import create_breakers

pytestmark = pytest.mark.integration


def _has_database_config() -> bool:
    if os.getenv("DATABASE_URL"):
        return True
    required = ["DB_USER", "DB_PASSWORD", "DB_NAME", "DB_HOST"]
    return all(os.getenv(var) for var in required)


def _has_benchling_config() -> bool:
    return bool(os.getenv("BENCHLING_WAREHOUSE_PASSWORD"))


def _has_gcs_config() -> bool:
    return bool(os.getenv("ARC_REACTOR_NEXTFLOW_BUCKET"))


def _has_gemini_config() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY"))


@pytest.mark.asyncio
async def test_benchling_connection() -> None:
    if not _has_benchling_config():
        pytest.skip("Missing Benchling warehouse credentials")

    breakers = create_breakers(settings)
    service = BenchlingService.create(settings, breakers)
    assert await service.health_check() is True
    await service.close()


@pytest.mark.asyncio
async def test_database_connection() -> None:
    if not _has_database_config():
        pytest.skip("Missing database configuration")

    service = DatabaseService.create(settings)
    assert await service.health_check() is True
    await service.close()


def test_gcs_upload_download() -> None:
    if not _has_gcs_config():
        pytest.skip("Missing ARC_REACTOR_NEXTFLOW_BUCKET")

    settings.set("nextflow_bucket", os.getenv("ARC_REACTOR_NEXTFLOW_BUCKET"))
    service = StorageService.create(settings)

    run_id = "smoke-test"
    uri = service.upload_run_file(run_id, "smoke.txt", "ping", "smoke@arc.org")
    downloaded = service.download_file(uri).decode()
    assert downloaded == "ping"


@pytest.mark.asyncio
async def test_gemini_completion() -> None:
    if not _has_gemini_config():
        pytest.skip("Missing Gemini credentials")

    breakers = create_breakers(settings)
    service = GeminiService.create(settings, breakers)
    response = await service.complete([{"role": "user", "content": "ping"}])
    assert response is not None
