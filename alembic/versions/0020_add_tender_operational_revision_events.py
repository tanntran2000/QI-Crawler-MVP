"""Persist append-only operational tender revision decision events.

Revision ID: 0020_add_tender_operational_revision_events
Revises: 0019_add_source_child_lifecycle
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0020_add_tender_operational_revision_events"
down_revision = "0019_add_source_child_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    required = {"tender_cases", "tender_releases"}
    if not required.issubset(tables):
        raise RuntimeError("tender cases and releases are required before revision events")
    if "tender_operational_revision_events" not in tables:
        op.create_table(
            "tender_operational_revision_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "case_id",
                sa.Integer(),
                sa.ForeignKey("tender_cases.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "release_id",
                sa.Integer(),
                sa.ForeignKey("tender_releases.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("base_id", sa.String(length=255), nullable=False),
            sa.Column("revision", sa.String(length=64), nullable=False),
            sa.Column("decision", sa.String(length=32), nullable=False),
            sa.Column("from_release_id", sa.Integer(), sa.ForeignKey("tender_releases.id", ondelete="SET NULL"), nullable=True),
            sa.Column("comparison_schema_version", sa.String(length=32), nullable=True),
            sa.Column("comparison_payload", sa.Text(), nullable=True),
            sa.Column("source_observation_complete", sa.Boolean(), nullable=True),
            sa.Column("completeness_evidence", sa.Text(), nullable=True),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("actor", sa.String(length=255), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("evidence", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes(
        "tender_operational_revision_events"
    )}
    for name, column in (
        ("ix_tender_operational_revision_events_case_id", "case_id"),
        ("ix_tender_operational_revision_events_release_id", "release_id"),
        ("ix_tender_operational_revision_events_base_id", "base_id"),
        ("ix_tender_operational_revision_events_revision", "revision"),
        ("ix_tender_operational_revision_events_decision", "decision"),
        ("ix_tender_operational_revision_events_from_release_id", "from_release_id"),
    ):
        if name not in indexes:
            op.create_index(name, "tender_operational_revision_events", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "tender_operational_revision_events" in sa.inspect(bind).get_table_names():
        op.drop_table("tender_operational_revision_events")
