"""Add immutable document intake records.

Revision ID: 0005_add_documents
Revises: 0004_add_notice_fts5
Create Date: 2026-08-13
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_add_documents"
down_revision = "0004_add_notice_fts5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tender_id",
            sa.Integer(),
            sa.ForeignKey("notices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("document_source", sa.String(length=32), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("zip_supported_entries", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("sha256", name="uq_document_sha256"),
        sa.UniqueConstraint("tender_id", "version", name="uq_document_tender_version"),
    )
    op.create_index("ix_documents_tender_id", "documents", ["tender_id"])
    op.create_index("ix_documents_document_source", "documents", ["document_source"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_sha256", "documents", ["sha256"])
    op.create_index("ix_documents_status", "documents", ["status"])


def downgrade() -> None:
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_sha256", table_name="documents")
    op.drop_index("ix_documents_document_type", table_name="documents")
    op.drop_index("ix_documents_document_source", table_name="documents")
    op.drop_index("ix_documents_tender_id", table_name="documents")
    op.drop_table("documents")
