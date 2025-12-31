from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.dependencies import get_current_user_context
from .benchling import router as benchling_router
from .pipelines import router as pipelines_router
from .runs import router as runs_router

api_router = APIRouter(dependencies=[Depends(get_current_user_context)])

api_router.include_router(runs_router)
api_router.include_router(pipelines_router)
api_router.include_router(benchling_router)
