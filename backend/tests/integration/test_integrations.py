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
    dynaconf_env = os.getenv("DYNACONF")
    prod_vars = [
        "BENCHLING_PROD_API_KEY",
        "BENCHLING_PROD_DATABASE_URI",
        "BENCHLING_PROD_APP_CLIENT_ID",
        "BENCHLING_PROD_APP_CLIENT_SECRET",
    ]
    test_vars = [
        "BENCHLING_TEST_API_KEY",
        "BENCHLING_TEST_DATABASE_URI",
        "BENCHLING_TEST_APP_CLIENT_ID",
        "BENCHLING_TEST_APP_CLIENT_SECRET",
    ]

    has_prod = all(os.getenv(var) for var in prod_vars)
    has_test = all(os.getenv(var) for var in test_vars)

    if dynaconf_env == "prod":
        return has_prod
    if dynaconf_env in {"test", "dev"}:
        return has_test
    return has_prod or has_test


def _has_gcs_config() -> bool:
    return bool(os.getenv("ARC_REACTOR_NEXTFLOW_BUCKET"))


def _has_gemini_config() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY"))


def _has_gcp_config() -> bool:
    """Check if GCP is configured for batch operations."""
    return bool(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or
        os.getenv("GOOGLE_CLOUD_PROJECT")
    )


@pytest.mark.asyncio
async def test_benchling_connection() -> None:
    if not _has_benchling_config():
        pytest.skip("Missing Benchling credentials")

    breakers = create_breakers(settings)
    service = BenchlingService.create(breakers)

    healthy = await service.health_check()
    if not healthy:
        pytest.skip("Benchling service not available")
    assert healthy is True

    rows = await service.query("SELECT 1 AS ok", return_format="dict")
    assert rows and rows[0].get("ok") == 1

    frame = await service.query("SELECT 1 AS ok", return_format="dataframe")
    assert getattr(frame, "shape", (0, 0))[0] >= 1

    converted = await service.convert_fields_to_api_format(
        "ngs_run_output_sample",
        {"link_to_fastq_file": "gs://example.fastq.gz"},
    )
    assert "Link to FASTQ File" in converted

    service.close()


@pytest.mark.asyncio
async def test_database_connection() -> None:
    if not _has_database_config():
        pytest.skip("Missing database configuration")

    service = DatabaseService.create(settings)
    healthy = await service.health_check()
    if not healthy:
        pytest.skip("Database service not available")
    assert healthy is True
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
