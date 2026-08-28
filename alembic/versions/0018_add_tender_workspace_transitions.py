"""Persist append-only Team Bid workspace transitions and slot lineage."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0018_add_tender_workspace_transitions"
down_revision = "0017_add_tender_workspace_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tender_workspace_entries" not in inspector.get_table_names():
        raise RuntimeError("tender_workspace_entries is required before workspace transitions")
    columns = {column["name"] for column in inspector.get_columns("tender_workspace_entries")}
    if "slot_key" not in columns:
        op.add_column(
            "tender_workspace_entries",
            sa.Column("slot_key", sa.String(length=128), nullable=True),
        )
    op.execute(
        sa.text(
            "UPDATE tender_workspace_entries "
            "SET slot_key = 'legacy-entry-' || CAST(id AS VARCHAR(32)) "
            "WHERE slot_key IS NULL"
        )
    )
    if "tender_workspace_transitions" not in inspector.get_table_names():
        op.create_table(
            "tender_workspace_transitions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "prior_entry_id",
                sa.Integer(),
                sa.ForeignKey("tender_workspace_entries.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "successor_entry_id",
                sa.Integer(),
                sa.ForeignKey("tender_workspace_entries.id", ondelete="RESTRICT"),
                nullable=True,
            ),
            sa.Column("transition_type", sa.String(length=32), nullable=False),
            sa.Column("actor", sa.String(length=255), nullable=True),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("evidence", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "prior_entry_id", name="uq_tender_workspace_transition_prior"
            ),
            sa.UniqueConstraint(
                "successor_entry_id", name="uq_tender_workspace_transition_successor"
            ),
        )
    transition_indexes = {
        index["name"]
        for index in sa.inspect(bind).get_indexes("tender_workspace_transitions")
    }
    for name, column in (
        ("ix_tender_workspace_transitions_prior_entry_id", "prior_entry_id"),
        ("ix_tender_workspace_transitions_successor_entry_id", "successor_entry_id"),
        ("ix_tender_workspace_transitions_transition_type", "transition_type"),
    ):
        if name not in transition_indexes:
            op.create_index(name, "tender_workspace_transitions", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "tender_workspace_transitions" in sa.inspect(bind).get_table_names():
        op.drop_table("tender_workspace_transitions")
    columns = {column["name"] for column in sa.inspect(bind).get_columns("tender_workspace_entries")}
    if "slot_key" in columns:
        op.drop_column("tender_workspace_entries", "slot_key")
