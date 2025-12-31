from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.users import User

DEFAULT_PREFERENCES: dict[str, Any] = {"notifications_enabled": False}
DEFAULT_STATS: dict[str, Any] = {
    "total_runs": 0,
    "successful_runs": 0,
    "total_samples_processed": 0,
}


@dataclass
class UserService:
    session: AsyncSession

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    async def get_or_create_user(self, email: str, display_name: str) -> User:
        user = await self.session.get(User, email)
        now = self._now()
        if user:
            user.last_login_at = now
            if display_name and user.display_name != display_name:
                user.display_name = display_name
        else:
            user = User(
                email=email,
                display_name=display_name,
                created_at=now,
                last_login_at=now,
                preferences=DEFAULT_PREFERENCES.copy(),
                stats=DEFAULT_STATS.copy(),
            )
            self.session.add(user)
        await self.session.commit()
        return user

    async def get_user(self, email: str) -> User | None:
        return await self.session.get(User, email)

    async def update_preferences(self, email: str, updates: dict[str, Any]) -> User | None:
        user = await self.session.get(User, email)
        if not user:
            return None
        current = user.preferences or DEFAULT_PREFERENCES.copy()
        current.update(updates)
        user.preferences = current
        await self.session.commit()
        return user

    async def update_stats(
        self,
        email: str,
        *,
        sample_count: int,
        successful: bool = False,
    ) -> User | None:
        user = await self.session.get(User, email)
        if not user:
            return None
        stats = user.stats or DEFAULT_STATS.copy()
        stats["total_runs"] = int(stats.get("total_runs", 0)) + 1
        stats["total_samples_processed"] = int(stats.get("total_samples_processed", 0)) + int(
            sample_count
        )
        if successful:
            stats["successful_runs"] = int(stats.get("successful_runs", 0)) + 1
        user.stats = stats
        await self.session.commit()
        return user
