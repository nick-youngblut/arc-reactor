"""initial_schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2025-01-02

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Runs table with weblog columns included
    op.create_table(
        "runs",
        sa.Column("run_id", sa.String(length=50), nullable=False),
        sa.Column("pipeline", sa.String(length=100), nullable=False),
        sa.Column("pipeline_version", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("user_name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("gcs_path", sa.Text(), nullable=False),
        sa.Column("batch_job_name", sa.Text(), nullable=True),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("source_ngs_runs", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("source_project", sa.Text(), nullable=True),
        sa.Column("parent_run_id", sa.String(length=50), nullable=True),
        sa.Column(
            "is_recovery",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("recovery_notes", sa.Text(), nullable=True),
        sa.Column("reused_work_dir", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_task", sa.Text(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Weblog integration columns
        sa.Column("weblog_secret_hash", sa.String(length=64), nullable=True),
        sa.Column("weblog_run_id", sa.String(length=36), nullable=True),
        sa.Column("weblog_run_name", sa.String(length=255), nullable=True),
        sa.Column("last_weblog_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("run_id"),
    )

    # Runs indexes
    op.create_index(
        "idx_runs_user_email_created_at",
        "runs",
        ["user_email", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_runs_status_created_at",
        "runs",
        ["status", sa.text("created_at DESC")],
    )
    op.create_index("idx_runs_created_at", "runs", [sa.text("created_at DESC")])
    op.create_index(
        "idx_runs_stale_detection",
        "runs",
        ["status", "updated_at"],
        postgresql_where=sa.text("status IN ('submitted', 'running')"),
    )

    # Users table
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "stats",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("email"),
    )
    op.create_index("idx_users_last_login_at", "users", [sa.text("last_login_at DESC")])

    # Checkpoints table (LangGraph)
    op.create_table(
        "checkpoints",
        sa.Column("thread_id", sa.String(length=100), nullable=False),
        sa.Column("checkpoint_id", sa.String(length=100), nullable=False),
        sa.Column("parent_checkpoint_id", sa.String(length=100), nullable=True),
        sa.Column(
            "checkpoint", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "checkpoint_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_id"),
    )

    # Tasks table (NEW - for weblog integration)
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("run_id", sa.String(length=50), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("hash", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("process", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("submit_time", sa.BigInteger(), nullable=True),
        sa.Column("start_time", sa.BigInteger(), nullable=True),
        sa.Column("complete_time", sa.BigInteger(), nullable=True),
        sa.Column("duration_ms", sa.BigInteger(), nullable=True),
        sa.Column("realtime_ms", sa.BigInteger(), nullable=True),
        sa.Column("cpu_percent", sa.Float(), nullable=True),
        sa.Column("peak_rss", sa.BigInteger(), nullable=True),
        sa.Column("peak_vmem", sa.BigInteger(), nullable=True),
        sa.Column("read_bytes", sa.BigInteger(), nullable=True),
        sa.Column("write_bytes", sa.BigInteger(), nullable=True),
        sa.Column("workdir", sa.Text(), nullable=True),
        sa.Column("container", sa.String(length=500), nullable=True),
        sa.Column("attempt", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("native_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("trace_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("run_id", "task_id", "attempt", name="uq_tasks_run_task_attempt"),
    )
    op.create_index("idx_tasks_run_id", "tasks", ["run_id"])
    op.create_index("idx_tasks_run_status", "tasks", ["run_id", "status"])
    op.create_index("idx_tasks_process", "tasks", ["process"])
    op.create_index("idx_tasks_created_at", "tasks", [sa.text("created_at DESC")])

    # Weblog event log table (NEW - for deduplication)
    op.create_table(
        "weblog_event_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("run_id", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "event_type", "task_id", "attempt", name="uq_weblog_event_dedup"
        ),
    )
    op.create_index("idx_weblog_event_log_cleanup", "weblog_event_log", ["processed_at"])


def downgrade() -> None:
    op.drop_table("weblog_event_log")
    op.drop_table("tasks")
    op.drop_table("checkpoints")
    op.drop_table("users")
    op.drop_table("runs")
