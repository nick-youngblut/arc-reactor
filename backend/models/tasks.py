from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    run_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )

    task_id: Mapped[int] = mapped_column(Integer, nullable=False)
    hash: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    process: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False)
    exit_code: Mapped[int | None] = mapped_column(Integer)

    submit_time: Mapped[int | None] = mapped_column(BigInteger)
    start_time: Mapped[int | None] = mapped_column(BigInteger)
    complete_time: Mapped[int | None] = mapped_column(BigInteger)

    duration_ms: Mapped[int | None] = mapped_column(BigInteger)
    realtime_ms: Mapped[int | None] = mapped_column(BigInteger)
    cpu_percent: Mapped[float | None] = mapped_column(Float)
    peak_rss: Mapped[int | None] = mapped_column(BigInteger)
    peak_vmem: Mapped[int | None] = mapped_column(BigInteger)
    read_bytes: Mapped[int | None] = mapped_column(BigInteger)
    write_bytes: Mapped[int | None] = mapped_column(BigInteger)

    workdir: Mapped[str | None] = mapped_column(Text)
    container: Mapped[str | None] = mapped_column(String(500))
    attempt: Mapped[int] = mapped_column(Integer, server_default=text("1"), nullable=False)
    native_id: Mapped[str | None] = mapped_column(String(255))

    error_message: Mapped[str | None] = mapped_column(Text)

    trace_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "task_id",
            "attempt",
            name="uq_tasks_run_task_attempt",
        ),
        Index("idx_tasks_run_id", "run_id"),
        Index("idx_tasks_run_status", "run_id", "status"),
        Index("idx_tasks_process", "process"),
        Index("idx_tasks_created_at", text("created_at DESC")),
    )
