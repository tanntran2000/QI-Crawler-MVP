"""Add source-neutral opportunity review events.

Revision ID: 0015_add_opportunity_review_events
Revises: 0014_add_source_type_review_events
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0015_add_opportunity_review_events"
down_revision = "0014_add_source_type_review_events"
branch_labels = None
depends_on = None


_INDEXES = (
    ("ix_opportunity_review_events_observation_key_id", ["observation_key", "id"]),
    ("ix_opportunity_review_events_source_sha256", ["source_sha256"]),
    ("ix_opportunity_review_events_source_type", ["source_type"]),
    ("ix_opportunity_review_events_identity_base_id", ["identity_base_id"]),
    ("ix_opportunity_review_events_identity_revision", ["identity_revision"]),
    ("ix_opportunity_review_events_decision", ["decision"]),
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("opportunity_review_events"):
        op.create_table(
            "opportunity_review_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("observation_key", sa.String(length=64), nullable=False),
            sa.Column("source_type", sa.String(length=16), nullable=False),
            sa.Column("identity_namespace", sa.String(length=16), nullable=False),
            sa.Column("identity_raw", sa.String(length=255), nullable=False),
            sa.Column("identity_base_id", sa.String(length=255), nullable=False),
            sa.Column("identity_revision", sa.String(length=64), nullable=True),
            sa.Column("source_sha256", sa.String(length=64), nullable=False),
            sa.Column("source_sheet", sa.String(length=255), nullable=False),
            sa.Column("source_row", sa.Integer(), nullable=False),
            sa.Column("decision", sa.String(length=32), nullable=False),
            sa.Column("reviewer", sa.String(length=255), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("opportunity_snapshot_json", sa.Text(), nullable=False),
            sa.Column("snapshot_schema_version", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("opportunity_review_events")}
    for name, columns in _INDEXES:
        if name not in indexes:
            op.create_index(name, "opportunity_review_events", columns)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("opportunity_review_events"):
        return
    indexes = {index["name"] for index in inspector.get_indexes("opportunity_review_events")}
    for name, _columns in reversed(_INDEXES):
        if name in indexes:
            op.drop_index(name, table_name="opportunity_review_events")
    op.drop_table("opportunity_review_events")
