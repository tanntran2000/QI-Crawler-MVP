"""Persist content-derived tender identity without altering original documents.

Revision ID: 0010_add_document_content_identity
Revises: 0009_add_manual_tender_workspace
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0010_add_document_content_identity"
down_revision = "0009_add_manual_tender_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("documents")}
    for column in (
        sa.Column("raw_notice_id", sa.String(length=255), nullable=True),
        sa.Column("base_notice_id", sa.String(length=255), nullable=True),
        sa.Column("notice_revision", sa.String(length=64), nullable=True),
        sa.Column("identity_source", sa.String(length=32), nullable=True),
        sa.Column("identity_evidence_locator", sa.Text(), nullable=True),
        sa.Column("identity_match_status", sa.String(length=64), nullable=True),
        sa.Column("identity_candidates_json", sa.Text(), nullable=True),
    ):
        if column.name not in columns:
            op.add_column("documents", column)
    indexes = {index["name"] for index in inspector.get_indexes("documents")}
    for name, column in (
        ("ix_documents_raw_notice_id", "raw_notice_id"),
        ("ix_documents_base_notice_id", "base_notice_id"),
        ("ix_documents_identity_match_status", "identity_match_status"),
    ):
        if name not in indexes:
            op.create_index(name, "documents", [column])


def downgrade() -> None:
    raise NotImplementedError("Document content identity migration is intentionally forward-only.")
