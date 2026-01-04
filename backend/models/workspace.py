from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .database import Base


class WorkspaceState(Base):
    __tablename__ = "workspace_states"

    __table_args__ = (
        Index("idx_workspace_user_email", "user_email"),
        Index("idx_workspace_updated_at", text("updated_at DESC")),
    )

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    thread_id: Mapped[str | None] = mapped_column(String(255))

    pipeline: Mapped[str | None] = mapped_column(String(255))
    version: Mapped[str | None] = mapped_column(String(50))

    samplesheet: Mapped[str | None] = mapped_column(Text)
    samplesheet_modified_by: Mapped[str | None] = mapped_column(String(10))
    samplesheet_modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    config: Mapped[str | None] = mapped_column(Text)
    config_modified_by: Mapped[str | None] = mapped_column(String(10))
    config_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    validation_result: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )
