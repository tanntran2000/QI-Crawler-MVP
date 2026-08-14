"""Add append-only native extraction ground truth review events.

Revision ID: 0008_add_ground_truth_reviews
Revises: 0007_add_native_document_extraction
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0008_add_ground_truth_reviews"
down_revision = "0007_add_native_document_extraction"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ground_truth_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "extraction_id",
            sa.Integer(),
            sa.ForeignKey("document_extractions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evidence_id",
            sa.Integer(),
            sa.ForeignKey("document_evidence.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("predicted_value", sa.Text(), nullable=True),
        sa.Column("predicted_status", sa.String(length=64), nullable=True),
        sa.Column("human_verdict", sa.String(length=16), nullable=False),
        sa.Column("corrected_value", sa.Text(), nullable=True),
        sa.Column("corrected_locator", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(length=64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("review_role", sa.String(length=16), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reviewer", sa.String(length=255), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("crawler_version", sa.String(length=32), nullable=False),
        sa.Column("extractor_version", sa.String(length=32), nullable=False),
        sa.Column("rule_version", sa.String(length=64), nullable=True),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name, columns in (
        ("ix_ground_truth_reviews_extraction_id", ["extraction_id"]),
        ("ix_ground_truth_reviews_evidence_id", ["evidence_id"]),
        ("ix_ground_truth_reviews_human_verdict", ["human_verdict"]),
        ("ix_ground_truth_reviews_error_type", ["error_type"]),
        ("ix_ground_truth_reviews_review_role", ["review_role"]),
        ("ix_ground_truth_reviews_review_status", ["review_status"]),
    ):
        op.create_index(name, "ground_truth_reviews", columns)


def downgrade() -> None:
    for name in (
        "ix_ground_truth_reviews_review_status",
        "ix_ground_truth_reviews_review_role",
        "ix_ground_truth_reviews_error_type",
        "ix_ground_truth_reviews_human_verdict",
        "ix_ground_truth_reviews_evidence_id",
        "ix_ground_truth_reviews_extraction_id",
    ):
        op.drop_index(name, table_name="ground_truth_reviews")
    op.drop_table("ground_truth_reviews")
