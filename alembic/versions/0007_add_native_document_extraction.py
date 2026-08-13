"""Add auditable native document extraction evidence.

Revision ID: 0007_add_native_document_extraction
Revises: 0006_add_document_taxonomy
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0007_add_native_document_extraction"
down_revision = "0006_add_document_taxonomy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "document_extractions" not in tables:
        op.create_table(
            "document_extractions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "document_id",
                sa.Integer(),
                sa.ForeignKey("documents.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("extractor_version", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "document_id", "extractor_version", name="uq_document_extraction_version"
            ),
        )
        op.create_index("ix_document_extractions_document_id", "document_extractions", ["document_id"])
        op.create_index("ix_document_extractions_status", "document_extractions", ["status"])
    if "document_evidence" not in tables:
        op.create_table(
            "document_evidence",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "extraction_id",
                sa.Integer(),
                sa.ForeignKey("document_extractions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("ordinal", sa.Integer(), nullable=False),
            sa.Column("source_locator", sa.Text(), nullable=False),
            sa.Column("page_number", sa.Integer(), nullable=True),
            sa.Column("sheet_name", sa.String(length=255), nullable=True),
            sa.Column("section_heading", sa.Text(), nullable=True),
            sa.Column("content_type", sa.String(length=32), nullable=False),
            sa.Column("text", sa.Text(), nullable=True),
            sa.Column("table_json", sa.Text(), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("extraction_id", "ordinal", name="uq_document_evidence_ordinal"),
        )
        op.create_index("ix_document_evidence_extraction_id", "document_evidence", ["extraction_id"])


def downgrade() -> None:
    op.drop_index("ix_document_evidence_extraction_id", table_name="document_evidence")
    op.drop_table("document_evidence")
    op.drop_index("ix_document_extractions_status", table_name="document_extractions")
    op.drop_index("ix_document_extractions_document_id", table_name="document_extractions")
    op.drop_table("document_extractions")
