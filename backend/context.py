from __future__ import annotations

from dataclasses import dataclass

from .config import settings


@dataclass(frozen=True)
class AppContext:
    settings: object = settings
