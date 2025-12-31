"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2025-12-31

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
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
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index(
        "idx_runs_created_at",
        "runs",
        [sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_runs_status_created_at",
        "runs",
        ["status", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_runs_user_email_created_at",
        "runs",
        ["user_email", sa.text("created_at DESC")],
        unique=False,
    )

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
            server_default=sa.text("'{\"notifications_enabled\": false}'"),
            nullable=False,
        ),
        sa.Column(
            "stats",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                "'{\"total_runs\": 0, \"successful_runs\": 0, \"total_samples_processed\": 0}'"
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("email"),
    )
    op.create_index(
        "idx_users_last_login_at",
        "users",
        [sa.text("last_login_at DESC")],
        unique=False,
    )

    op.create_table(
        "checkpoints",
        sa.Column("thread_id", sa.String(length=100), nullable=False),
        sa.Column("checkpoint_id", sa.String(length=100), nullable=False),
        sa.Column("parent_checkpoint_id", sa.String(length=100), nullable=True),
        sa.Column("checkpoint", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_id"),
    )


def downgrade() -> None:
    op.drop_table("checkpoints")
    op.drop_index("idx_users_last_login_at", table_name="users")
    op.drop_table("users")
    op.drop_index("idx_runs_user_email_created_at", table_name="runs")
    op.drop_index("idx_runs_status_created_at", table_name="runs")
    op.drop_index("idx_runs_created_at", table_name="runs")
    op.drop_table("runs")
