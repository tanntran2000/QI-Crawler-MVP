"""Persist derived HSMT facts with native-evidence lineage.

Revision ID: 0011_add_hsmt_facts
Revises: 0010_add_document_content_identity
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0011_add_hsmt_facts"
down_revision = "0010_add_document_content_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "hsmt_facts" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "hsmt_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tender_id", sa.Integer(), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="SET NULL")),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("document_evidence.id", ondelete="SET NULL")),
        sa.Column("fact_group", sa.String(length=64), nullable=False),
        sa.Column("fact_key", sa.String(length=64), nullable=False),
        sa.Column("normalized_value", sa.Text()),
        sa.Column("raw_evidence_text", sa.Text()),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("source_locator", sa.Text()),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fingerprint", name="uq_hsmt_fact_fingerprint"),
    )
    for name, column in (("ix_hsmt_facts_tender_id", "tender_id"), ("ix_hsmt_facts_group", "fact_group"), ("ix_hsmt_facts_key", "fact_key"), ("ix_hsmt_facts_status", "status")):
        op.create_index(name, "hsmt_facts", [column])


def downgrade() -> None:
    raise NotImplementedError("HSMT fact migration is intentionally forward-only.")
