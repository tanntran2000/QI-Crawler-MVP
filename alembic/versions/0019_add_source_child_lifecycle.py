"""Track source membership lifecycle without deleting child evidence."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0019_add_source_child_lifecycle"
down_revision = "0018_add_tender_workspace_transitions"
branch_labels = None
depends_on = None


def _add_lifecycle_columns(table_name: str) -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns(table_name)}
    if "source_active" not in columns:
        op.add_column(
            table_name,
            sa.Column(
                "source_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )
    if "source_last_seen_at" not in columns:
        op.add_column(
            table_name,
            sa.Column("source_last_seen_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "source_removed_at" not in columns:
        op.add_column(
            table_name,
            sa.Column("source_removed_at", sa.DateTime(timezone=True), nullable=True),
        )

    index_name = f"ix_{table_name}_source_active"
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)}
    if index_name not in indexes:
        op.create_index(index_name, table_name, ["source_active"])


def upgrade() -> None:
    _add_lifecycle_columns("attachments")
    _add_lifecycle_columns("tender_items")


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in ("tender_items", "attachments"):
        index_name = f"ix_{table_name}_source_active"
        indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)}
        if index_name in indexes:
            op.drop_index(index_name, table_name=table_name)
        columns = {column["name"] for column in sa.inspect(bind).get_columns(table_name)}
        for column_name in ("source_removed_at", "source_last_seen_at", "source_active"):
            if column_name in columns:
                op.drop_column(table_name, column_name)
