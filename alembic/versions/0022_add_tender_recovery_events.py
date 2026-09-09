"""Persist managed-source integrity and recovery events."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0022_add_tender_recovery_events"
down_revision = "0021_add_tender_completeness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    required = {"tender_cases", "tender_releases", "tender_document_memberships", "documents"}
    if not required.issubset(tables):
        raise RuntimeError("tender warehouse tables are required before recovery events")
    if "tender_recovery_events" not in tables:
        op.create_table(
            "tender_recovery_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("case_id", sa.Integer(), sa.ForeignKey("tender_cases.id", ondelete="SET NULL")),
            sa.Column("release_id", sa.Integer(), sa.ForeignKey("tender_releases.id", ondelete="SET NULL")),
            sa.Column("membership_id", sa.Integer(), sa.ForeignKey("tender_document_memberships.id", ondelete="SET NULL")),
            sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="SET NULL")),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("expected_sha256", sa.String(length=64)),
            sa.Column("observed_sha256", sa.String(length=64)),
            sa.Column("candidate_sha256", sa.String(length=64)),
            sa.Column("managed_path", sa.Text()),
            sa.Column("candidate_path", sa.Text()),
            sa.Column("quarantine_path", sa.Text()),
            sa.Column("actor", sa.String(length=255), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("evidence", sa.Text(), nullable=False),
            sa.Column("result", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("tender_recovery_events")}
    for name, column in (
        ("ix_tender_recovery_events_case_id", "case_id"),
        ("ix_tender_recovery_events_release_id", "release_id"),
        ("ix_tender_recovery_events_membership_id", "membership_id"),
        ("ix_tender_recovery_events_document_id", "document_id"),
        ("ix_tender_recovery_events_action", "action"),
        ("ix_tender_recovery_events_expected_sha256", "expected_sha256"),
        ("ix_tender_recovery_events_observed_sha256", "observed_sha256"),
        ("ix_tender_recovery_events_candidate_sha256", "candidate_sha256"),
        ("ix_tender_recovery_events_result", "result"),
    ):
        if name not in indexes:
            op.create_index(name, "tender_recovery_events", [column])


def downgrade() -> None:
    if "tender_recovery_events" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table("tender_recovery_events")
