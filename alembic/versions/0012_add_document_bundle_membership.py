"""Persist bundle membership separately from document content identity.

Revision ID: 0012_add_document_bundle_membership
Revises: 0011_add_hsmt_facts
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0012_add_document_bundle_membership"
down_revision = "0011_add_hsmt_facts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("documents")}
    for column in (
        sa.Column("bundle_base_notice_id", sa.String(length=255), nullable=True),
        sa.Column("bundle_revision", sa.String(length=64), nullable=True),
        sa.Column("bundle_membership_status", sa.String(length=64), nullable=True),
        sa.Column("bundle_membership_source", sa.String(length=32), nullable=True),
        sa.Column("bundle_membership_evidence", sa.Text(), nullable=True),
    ):
        if column.name not in columns:
            op.add_column("documents", column)
    indexes = {index["name"] for index in inspector.get_indexes("documents")}
    for name, column in (
        ("ix_documents_bundle_base_notice_id", "bundle_base_notice_id"),
        ("ix_documents_bundle_membership_status", "bundle_membership_status"),
    ):
        if name not in indexes:
            op.create_index(name, "documents", [column])


def downgrade() -> None:
    raise NotImplementedError("Document bundle membership migration is intentionally forward-only.")
