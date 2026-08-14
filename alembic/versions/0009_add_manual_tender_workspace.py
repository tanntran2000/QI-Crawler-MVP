"""Add human-declared Team Bid tender workspace metadata.

Revision ID: 0009_add_manual_tender_workspace
Revises: 0008_add_ground_truth_reviews
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0009_add_manual_tender_workspace"
down_revision = "0008_add_ground_truth_reviews"
branch_labels = None
depends_on = None


def _sqlite_notice_fts_triggers() -> list[tuple[str, str]]:
    if op.get_bind().dialect.name != "sqlite":
        return []
    rows = op.get_bind().execute(
        sa.text(
            """
            SELECT name, sql FROM sqlite_master
            WHERE type = 'trigger' AND name LIKE 'notice_fts_%' AND sql IS NOT NULL
            """
        )
    )
    return [(row[0], row[1]) for row in rows]


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("notices")}
    for column in (
        sa.Column("source_origin", sa.String(length=32), nullable=False, server_default="WEB"),
        sa.Column("identity_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("screening_status", sa.String(length=32), nullable=True),
        sa.Column("business_priority", sa.String(length=16), nullable=False, server_default="NORMAL"),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_note", sa.Text(), nullable=True),
    ):
        if column.name not in columns:
            op.add_column("notices", column)
    indexes = {index["name"] for index in inspector.get_indexes("notices")}
    for name, columns in (
        ("ix_notices_source_origin", ["source_origin"]),
        ("ix_notices_identity_status", ["identity_status"]),
        ("ix_notices_screening_status", ["screening_status"]),
        ("ix_notices_business_priority", ["business_priority"]),
    ):
        if name not in indexes:
            op.create_index(name, "notices", columns)

    trigger_sql = _sqlite_notice_fts_triggers()
    if op.get_bind().dialect.name == "sqlite":
        for name, _statement in trigger_sql:
            safe_name = name.replace('"', '""')
            op.execute(f'DROP TRIGGER IF EXISTS "{safe_name}"')
        with op.batch_alter_table("notices", recreate="always") as batch:
            batch.alter_column("source_url", existing_type=sa.Text(), nullable=True)
        for _name, statement in trigger_sql:
            op.execute(statement)
    else:
        op.alter_column("notices", "source_url", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    raise NotImplementedError("Manual tender workspace migration is intentionally forward-only.")
