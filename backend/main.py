from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import api_router
from .api.routes.health import router as health_router
from .config import settings


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
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.get("app_name", "Arc Reactor"),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get("cors_allowed_origins", []),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(api_router, prefix="/api")

    dist_dir = Path(settings.get("frontend_out_dir", "frontend/out")).resolve()
    _mount_static_assets(app, dist_dir)

    @app.get("/{full_path:path}")
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
