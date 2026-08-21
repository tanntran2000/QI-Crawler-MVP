"""Add append-only KHMT candidate review events.

Revision ID: 0013_add_candidate_review_events
Revises: 0012_add_document_bundle_membership
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0013_add_candidate_review_events"
down_revision = "0012_add_document_bundle_membership"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("candidate_review_events"):
        op.create_table(
            "candidate_review_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("candidate_key", sa.String(length=64), nullable=False),
            sa.Column("source_sha256", sa.String(length=64), nullable=False),
            sa.Column("source_sheet", sa.String(length=255), nullable=False),
            sa.Column("source_row", sa.Integer(), nullable=False),
            sa.Column("plan_id_raw", sa.String(length=255), nullable=False),
            sa.Column("plan_base_id", sa.String(length=255), nullable=False),
            sa.Column("plan_revision", sa.String(length=64), nullable=True),
            sa.Column("decision", sa.String(length=32), nullable=False),
            sa.Column("reviewer", sa.String(length=255), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("package_snapshot_json", sa.Text(), nullable=False),
            sa.Column("snapshot_schema_version", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    inspector = sa.inspect(op.get_bind())
    indexes = {item["name"] for item in inspector.get_indexes("candidate_review_events")}
    for name, columns in (
        ("ix_candidate_review_events_candidate_key_id", ["candidate_key", "id"]),
        ("ix_candidate_review_events_source_sha256", ["source_sha256"]),
        ("ix_candidate_review_events_plan_base_id", ["plan_base_id"]),
        ("ix_candidate_review_events_plan_revision", ["plan_revision"]),
        ("ix_candidate_review_events_decision", ["decision"]),
    ):
        if name not in indexes:
            op.create_index(name, "candidate_review_events", columns)


def downgrade() -> None:
    op.drop_index("ix_candidate_review_events_decision", table_name="candidate_review_events")
    op.drop_index("ix_candidate_review_events_plan_revision", table_name="candidate_review_events")
    op.drop_index("ix_candidate_review_events_plan_base_id", table_name="candidate_review_events")
    op.drop_index("ix_candidate_review_events_source_sha256", table_name="candidate_review_events")
    op.drop_index(
        "ix_candidate_review_events_candidate_key_id",
        table_name="candidate_review_events",
    )
    op.drop_table("candidate_review_events")
