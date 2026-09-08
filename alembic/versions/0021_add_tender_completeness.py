"""Persist core HSMT coverage and publication expectation reconciliation."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0021_add_tender_completeness"
down_revision = "0020_add_tender_operational_revision_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    required = {"tender_releases", "tender_document_memberships"}
    if not required.issubset(tables):
        raise RuntimeError("tender releases and memberships are required before completeness")

    if "tender_core_coverage" not in tables:
        op.create_table(
            "tender_core_coverage",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "release_id",
                sa.Integer(),
                sa.ForeignKey("tender_releases.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "membership_id",
                sa.Integer(),
                sa.ForeignKey("tender_document_memberships.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("role_code", sa.String(length=64), nullable=False),
            sa.Column("state", sa.String(length=32), nullable=False),
            sa.Column("content_locator", sa.Text(), nullable=False),
            sa.Column("evidence", sa.Text(), nullable=False),
            sa.Column("actor", sa.String(length=255), nullable=False),
            sa.Column("dependency_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_tender_core_coverage_release_role",
            "tender_core_coverage",
            ["release_id", "role_code"],
        )
        op.create_index(
            "ix_tender_core_coverage_membership",
            "tender_core_coverage",
            ["membership_id"],
        )

    if "tender_publication_expectation_sets" not in tables:
        op.create_table(
            "tender_publication_expectation_sets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "release_id",
                sa.Integer(),
                sa.ForeignKey("tender_releases.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("basis", sa.String(length=32), nullable=False),
            sa.Column("authority", sa.String(length=255), nullable=False),
            sa.Column("evidence", sa.Text(), nullable=False),
            sa.Column("actor", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_tender_publication_expectation_sets_release_id",
            "tender_publication_expectation_sets",
            ["release_id"],
        )
        op.create_index(
            "ix_tender_publication_expectation_sets_basis",
            "tender_publication_expectation_sets",
            ["basis"],
        )

    if "tender_publication_expectation_items" not in tables:
        op.create_table(
            "tender_publication_expectation_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "expectation_set_id",
                sa.Integer(),
                sa.ForeignKey("tender_publication_expectation_sets.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("logical_key", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("state", sa.String(length=32), nullable=False),
            sa.Column(
                "matched_membership_id",
                sa.Integer(),
                sa.ForeignKey("tender_document_memberships.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("evidence", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "expectation_set_id",
                "logical_key",
                name="uq_tender_publication_expectation_item",
            ),
        )
        op.create_index(
            "ix_tender_publication_expectation_items_expectation_set_id",
            "tender_publication_expectation_items",
            ["expectation_set_id"],
        )
        op.create_index(
            "ix_tender_publication_expectation_items_logical_key",
            "tender_publication_expectation_items",
            ["logical_key"],
        )
        op.create_index(
            "ix_tender_publication_expectation_items_state",
            "tender_publication_expectation_items",
            ["state"],
        )
        op.create_index(
            "ix_tender_publication_expectation_items_matched_membership_id",
            "tender_publication_expectation_items",
            ["matched_membership_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "tender_publication_expectation_items" in tables:
        op.drop_table("tender_publication_expectation_items")
    if "tender_publication_expectation_sets" in tables:
        op.drop_table("tender_publication_expectation_sets")
    if "tender_core_coverage" in tables:
        op.drop_table("tender_core_coverage")
