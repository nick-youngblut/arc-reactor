from fastapi import APIRouter

from .reconcile import router as reconcile_router
from .weblog import router as weblog_router

internal_router = APIRouter(prefix="/api/internal", tags=["internal"])
internal_router.include_router(weblog_router)
internal_router.include_router(reconcile_router)
