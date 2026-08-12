"""Add per-URL crawl checkpoints.

Revision ID: 0001_add_crawl_tasks
Revises:
Create Date: 2026-08-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_add_crawl_tasks"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crawl_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("crawl_run_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["crawl_run_id"], ["crawl_runs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("crawl_run_id", "url", name="uq_crawl_task_run_url"),
    )
    op.create_index("ix_crawl_tasks_crawl_run_id", "crawl_tasks", ["crawl_run_id"])
    op.create_index("ix_crawl_tasks_status", "crawl_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_crawl_tasks_status", table_name="crawl_tasks")
    op.drop_index("ix_crawl_tasks_crawl_run_id", table_name="crawl_tasks")
    op.drop_table("crawl_tasks")
