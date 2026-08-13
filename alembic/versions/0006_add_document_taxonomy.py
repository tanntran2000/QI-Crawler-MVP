"""Add tender document taxonomy metadata.

Revision ID: 0006_add_document_taxonomy
Revises: 0005_add_documents
Create Date: 2026-08-13
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0006_add_document_taxonomy"
down_revision = "0005_add_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("file_format", sa.String(length=16)))
    op.add_column("documents", sa.Column("template_code", sa.String(length=32)))
    op.add_column("documents", sa.Column("package_type", sa.String(length=64)))
    op.add_column("documents", sa.Column("selection_method", sa.Text()))
    op.add_column(
        "documents",
        sa.Column(
            "classification_status",
            sa.String(length=32),
            nullable=False,
            server_default="UNKNOWN",
        ),
    )
    op.execute(
        """
        UPDATE documents
        SET file_format = document_type,
            document_type = 'OTHER',
            classification_status = 'UNKNOWN'
        WHERE document_type IN ('PDF', 'DOCX', 'XLSX', 'ZIP')
        """
    )
    op.create_index("ix_documents_template_code", "documents", ["template_code"])
    op.create_index("ix_documents_package_type", "documents", ["package_type"])
    op.create_index(
        "ix_documents_classification_status",
        "documents",
        ["classification_status"],
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE documents
        SET document_type = COALESCE(file_format, document_type)
        WHERE classification_status = 'UNKNOWN'
          AND document_type = 'OTHER'
        """
    )
    op.drop_index("ix_documents_classification_status", table_name="documents")
    op.drop_index("ix_documents_package_type", table_name="documents")
    op.drop_index("ix_documents_template_code", table_name="documents")
    op.drop_column("documents", "classification_status")
    op.drop_column("documents", "selection_method")
    op.drop_column("documents", "package_type")
    op.drop_column("documents", "template_code")
    op.drop_column("documents", "file_format")
