"""Add source-specific notice identifiers.

Revision ID: 0002_add_multisource_identity
Revises: 0001_add_crawl_tasks
Create Date: 2026-08-12
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_add_multisource_identity"
down_revision = "0001_add_crawl_tasks"
branch_labels = None
depends_on = None


def _has_column(name: str) -> bool:
    return name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns("notices")}


def _has_index(name: str) -> bool:
    return name in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("notices")}


def upgrade() -> None:
    # Reviewed manually: do not use autogenerate for a deployed SQLite database.
    inspector = sa.inspect(op.get_bind())
    if "notices" not in inspector.get_table_names():
        return
    if not _has_column("source_notice_id"):
        op.add_column("notices", sa.Column("source_notice_id", sa.String(length=255)))
    if not _has_column("source_name"):
        op.add_column("notices", sa.Column("source_name", sa.String(length=255)))
    if not _has_index("ix_notices_source_notice_id"):
        op.create_index("ix_notices_source_notice_id", "notices", ["source_notice_id"])
    if not _has_index("ix_notices_source_name"):
        op.create_index("ix_notices_source_name", "notices", ["source_name"])


def downgrade() -> None:
    # SQLite supports DROP COLUMN on supported versions; batch mode keeps downgrade portable.
    inspector = sa.inspect(op.get_bind())
    if "notices" not in inspector.get_table_names():
        return
    with op.batch_alter_table("notices") as batch:
        batch.drop_index("ix_notices_source_name")
        batch.drop_index("ix_notices_source_notice_id")
        batch.drop_column("source_name")
        batch.drop_column("source_notice_id")
