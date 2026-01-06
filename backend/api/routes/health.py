from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from google.cloud import batch_v1

from ... import __version__
from ...dependencies import (
    get_benchling_service,
    get_breakers,
    get_checkpointer_service,
    get_database_service,
    get_gemini_service,
    get_storage_service,
)
from ...services.benchling import BenchlingService
from ...services.checkpointer import CheckpointerService
from ...services.database import DatabaseService
from ...services.gemini import DisabledGeminiService, GeminiService
from ...services.storage import StorageService
from ...utils.circuit_breaker import Breakers, breaker_state, is_breaker_open

router = APIRouter(tags=["health"])


async def check_batch_access() -> bool:
    def _check() -> bool:
        client = batch_v1.BatchServiceClient()
        _ = client.transport
        return True

    try:
        return await asyncio.to_thread(_check)
    except Exception:
        return False


@router.get("/health")
async def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "arc-reactor",
        "version": __version__,
    }


@router.get("/ready")
async def readiness_check(
    benchling: BenchlingService = Depends(get_benchling_service),
    database: DatabaseService = Depends(get_database_service),
    storage: StorageService = Depends(get_storage_service),
    gemini: GeminiService | DisabledGeminiService = Depends(get_gemini_service),
    checkpointer: CheckpointerService = Depends(get_checkpointer_service),
    breakers: Breakers = Depends(get_breakers),
) -> JSONResponse:
    benchling_ok = await benchling.health_check()
    postgres_ok = await database.health_check()
    gcs_ok = await asyncio.to_thread(storage.health_check)
    batch_ok = await check_batch_access()
    gemini_ok = await gemini.health_check()
    checkpointer_ok = await checkpointer.health_check()

    if is_breaker_open(breakers.benchling):
        benchling_ok = False
    if is_breaker_open(breakers.gemini):
        gemini_ok = False

    checks = {
        "benchling": benchling_ok,
        "postgres": postgres_ok,
        "gcs": gcs_ok,
        "batch": batch_ok,
        "gemini": gemini_ok,
        "checkpointer": checkpointer_ok,
    }

    critical = ["postgres", "gcs", "batch", "checkpointer"]
    critical_healthy = all(checks[name] for name in critical)
    degraded = not all(checks.values())

    return JSONResponse(
        status_code=200 if critical_healthy else 503,
        content={
            "healthy": critical_healthy,
            "degraded": degraded,
            "checks": checks,
            "circuit_breakers": {
                "benchling": breaker_state(breakers.benchling),
                "gemini": breaker_state(breakers.gemini),
            },
        },
    )
