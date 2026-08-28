"""Add domain-first TenderCase, release, and document membership records.

Revision ID: 0016_add_tender_cases
Revises: 0015_add_opportunity_review_events
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0016_add_tender_cases"
down_revision = "0015_add_opportunity_review_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "tender_cases" not in tables:
        op.create_table(
            "tender_cases",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("case_key", sa.String(length=255), nullable=False),
            sa.Column("plan_id_raw", sa.String(length=255)),
            sa.Column("plan_base_id", sa.String(length=255)),
            sa.Column("plan_revision", sa.String(length=64)),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="PROVISIONAL"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("case_key", name="uq_tender_case_key"),
        )
    if "tender_releases" not in tables:
        op.create_table(
            "tender_releases",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("case_id", sa.Integer(), sa.ForeignKey("tender_cases.id", ondelete="CASCADE"), nullable=False),
            sa.Column("notice_id", sa.Integer(), sa.ForeignKey("notices.id", ondelete="SET NULL")),
            sa.Column("raw_id", sa.String(length=255), nullable=False),
            sa.Column("base_id", sa.String(length=255), nullable=False),
            sa.Column("revision", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("case_id", "base_id", "revision", name="uq_tender_release_exact"),
        )
    if "tender_document_memberships" not in tables:
        op.create_table(
            "tender_document_memberships",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("release_id", sa.Integer(), sa.ForeignKey("tender_releases.id", ondelete="CASCADE"), nullable=False),
            sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("authority_class", sa.String(length=32), nullable=False),
            sa.Column("evidence", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "release_id", "document_id", "authority_class",
                name="uq_tender_document_membership",
            ),
        )
    index_specs = (
        ("ix_tender_cases_case_key", "tender_cases", ["case_key"]),
        ("ix_tender_cases_plan_base_id", "tender_cases", ["plan_base_id"]),
        ("ix_tender_cases_status", "tender_cases", ["status"]),
        ("ix_tender_releases_case_id", "tender_releases", ["case_id"]),
        ("ix_tender_releases_notice_id", "tender_releases", ["notice_id"]),
        ("ix_tender_releases_base_id", "tender_releases", ["base_id"]),
        ("ix_tender_releases_revision", "tender_releases", ["revision"]),
        ("ix_tender_document_memberships_release_id", "tender_document_memberships", ["release_id"]),
        ("ix_tender_document_memberships_document_id", "tender_document_memberships", ["document_id"]),
        ("ix_tender_document_memberships_authority_class", "tender_document_memberships", ["authority_class"]),
    )
    existing = {
        (table_name, index["name"])
        for table_name in ("tender_cases", "tender_releases", "tender_document_memberships")
        for index in sa.inspect(bind).get_indexes(table_name)
    }
    for name, table_name, columns in index_specs:
        if (table_name, name) not in existing:
            op.create_index(name, table_name, columns)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table_name in (
        "tender_document_memberships",
        "tender_releases",
        "tender_cases",
    ):
        if table_name in inspector.get_table_names():
            op.drop_table(table_name)
