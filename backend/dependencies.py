from __future__ import annotations

from .config import settings
from .context import AppContext


def get_settings() -> object:
    return settings


def get_context() -> AppContext:
    return AppContext(settings=settings)
