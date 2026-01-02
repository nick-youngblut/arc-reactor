from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import AsyncIterator

# Load .env file before any other imports to ensure environment variables
# are available to all modules, especially benchling-py which needs them
from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import api_router
from .api.routes.chat import router as chat_router
from .api.routes.health import router as health_router
from .config import settings
from .services.benchling import BenchlingService
from .services.database import DatabaseService
from .services.gemini import DisabledGeminiService, GeminiService
from .services.storage import StorageService
from .utils.circuit_breaker import create_breakers
from .utils.errors import register_exception_handlers

logger = logging.getLogger(__name__)


def _mount_static_assets(app: FastAPI, dist_dir: Path) -> None:
    if not dist_dir.exists():
        return

    next_dir = dist_dir / "_next"
    if next_dir.exists():
        app.mount("/_next", StaticFiles(directory=next_dir), name="next")

    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting Arc Reactor services")
    breakers = create_breakers(settings)
    app.state.breakers = breakers
    try:
        app.state.benchling_service = BenchlingService.create(breakers)
        tenant = os.getenv("DYNACONF", "test/dev")
        logger.info("Benchling service initialized (tenant: %s)", tenant)
    except Exception as exc:
        logger.error("Failed to initialize Benchling service: %s", exc)
        raise
    app.state.database_service = DatabaseService.create(settings)
    app.state.storage_service = StorageService.create(settings)
    try:
        app.state.gemini_service = GeminiService.create(settings, breakers)
    except Exception as exc:
        logger.warning("Gemini service failed to initialize: %s", exc)
        app.state.gemini_service = DisabledGeminiService(error=exc)

    yield

    logger.info("Shutting down Arc Reactor services")
    app.state.benchling_service.close()
    # BenchlingService.close_all_engines()
    await app.state.database_service.close()
    app.state.storage_service = None
    app.state.gemini_service = None


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.get("app_name", "Arc Reactor"),
        lifespan=lifespan,
    )
    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get("cors_allowed_origins", []),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(api_router, prefix="/api")
    app.include_router(chat_router)

    dist_dir = Path(settings.get("frontend_out_dir", "frontend/out")).resolve()
    _mount_static_assets(app, dist_dir)

    @app.get("/{full_path:path}", response_model=None)
    async def serve_frontend(full_path: str) -> FileResponse | JSONResponse:
        if not dist_dir.exists():
            return JSONResponse({"detail": "Frontend not built"}, status_code=404)

        file_path = dist_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        index_path = dist_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        return JSONResponse({"detail": "Not Found"}, status_code=404)

    return app


app = create_app()
