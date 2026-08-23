"""Persist source-type detection and human correction history.

Revision ID: 0014_add_source_type_review_events
Revises: 0013_add_candidate_review_events
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0014_add_source_type_review_events"
down_revision = "0013_add_candidate_review_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "source_type_review_events" in inspector.get_table_names():
        return
    op.create_table(
        "source_type_review_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("filename_type", sa.String(length=16), nullable=False),
        sa.Column("content_type", sa.String(length=16), nullable=False),
        sa.Column("identity_namespace", sa.String(length=16)),
        sa.Column("auto_type", sa.String(length=16), nullable=False),
        sa.Column("final_type", sa.String(length=16), nullable=False),
        sa.Column("authority", sa.String(length=16), nullable=False),
        sa.Column("reviewer", sa.String(length=255), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("identity_values_json", sa.Text()),
        sa.Column("identity_raw_values_json", sa.Text()),
        sa.Column("evidence_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_source_type_review_events_source_sha256",
        "source_type_review_events",
        ["source_sha256"],
    )
    op.create_index(
        "ix_source_type_review_events_created_at",
        "source_type_review_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_source_type_review_events_created_at",
        table_name="source_type_review_events",
    )
    op.drop_index(
        "ix_source_type_review_events_source_sha256",
        table_name="source_type_review_events",
    )
    op.drop_table("source_type_review_events")
