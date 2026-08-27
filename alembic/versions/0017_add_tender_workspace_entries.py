"""Persist explicit logical Team Bid workspace zone assignments."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0017_add_tender_workspace_entries"
down_revision = "0016_add_tender_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tender_workspace_entries" not in inspector.get_table_names():
        op.create_table(
            "tender_workspace_entries",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "membership_id",
                sa.Integer(),
                sa.ForeignKey("tender_document_memberships.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("zone_code", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "membership_id", "zone_code", name="uq_tender_workspace_entry"
            ),
        )
    existing = {
        index["name"]
        for index in sa.inspect(bind).get_indexes("tender_workspace_entries")
    }
    for name, column in (
        ("ix_tender_workspace_entries_membership_id", "membership_id"),
        ("ix_tender_workspace_entries_zone_code", "zone_code"),
    ):
        if name not in existing:
            op.create_index(name, "tender_workspace_entries", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "tender_workspace_entries" in sa.inspect(bind).get_table_names():
        op.drop_table("tender_workspace_entries")
