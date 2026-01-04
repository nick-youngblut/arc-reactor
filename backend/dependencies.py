from __future__ import annotations

from fastapi import Depends, Request

from .config import settings
from .context import AppContext
from .services.benchling import BenchlingService
from .services.checkpointer import CheckpointerService
from .services.database import DatabaseService
from .services.gemini import DisabledGeminiService, GeminiService
from .services.storage import StorageService
from .utils.circuit_breaker import Breakers
from .utils.auth import UserContext, get_current_user


def get_settings() -> object:
    return settings


def get_context() -> AppContext:
    return AppContext(settings=settings)


def get_breakers(request: Request) -> Breakers:
    return request.app.state.breakers


def get_benchling_service(request: Request) -> BenchlingService:
    return request.app.state.benchling_service


def get_database_service(request: Request) -> DatabaseService:
    return request.app.state.database_service


def get_storage_service(request: Request) -> StorageService:
    return request.app.state.storage_service


def get_checkpointer_service(request: Request) -> CheckpointerService:
    return request.app.state.checkpointer_service


def get_gemini_service(request: Request) -> GeminiService | DisabledGeminiService:
    return request.app.state.gemini_service


async def get_db_session(
    database: DatabaseService = Depends(get_database_service),
):
    async for session in database.get_session():
        yield session


async def get_current_user_context(request: Request) -> UserContext:
    return await get_current_user(request)
