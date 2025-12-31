from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .database import Base


class Run(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    pipeline: Mapped[str] = mapped_column(String(100), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    user_name: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    gcs_path: Mapped[str] = mapped_column(Text, nullable=False)
    batch_job_name: Mapped[str | None] = mapped_column(Text)

    params: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=False
    )
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_ngs_runs: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite")
    )
    source_project: Mapped[str | None] = mapped_column(Text)

    parent_run_id: Mapped[str | None] = mapped_column(String(50))
    is_recovery: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    recovery_notes: Mapped[str | None] = mapped_column(Text)
    reused_work_dir: Mapped[str | None] = mapped_column(Text)

    exit_code: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_task: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite")
    )

    __table_args__ = (
        Index(
            "idx_runs_user_email_created_at",
            "user_email",
            text("created_at DESC"),
        ),
        Index("idx_runs_status_created_at", "status", text("created_at DESC")),
        Index("idx_runs_created_at", text("created_at DESC")),
    )
