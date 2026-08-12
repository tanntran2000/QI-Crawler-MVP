"""Complete the additive core schema without rewriting historical revisions.

Revision ID: 0003_complete_core_schema
Revises: 0002_add_multisource_identity
Create Date: 2026-08-12

This revision is deliberately hand-reviewed.  It creates a complete blank
database and adds only missing tables/columns to an existing SQLite database.
It never calls ``Base.metadata.create_all()``.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_complete_core_schema"
down_revision = "0002_add_multisource_identity"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def _ensure_table(
    table_name: str,
    *columns_and_constraints: sa.Column | sa.Constraint,
    indexes: tuple[tuple[str, tuple[str, ...], bool], ...] = (),
) -> None:
    """Create a missing table, or add missing additive columns to an old one."""
    if table_name not in _table_names():
        op.create_table(table_name, *columns_and_constraints)
    else:
        existing = _column_names(table_name)
        for item in columns_and_constraints:
            if isinstance(item, sa.Column) and item.name not in existing:
                # Existing rows require defaults for new non-null columns.
                column = sa.Column(
                    item.name,
                    item.type,
                    nullable=item.nullable,
                    server_default=item.server_default,
                )
                if not column.nullable and column.server_default is None:
                    column.nullable = True
                op.add_column(table_name, column)
    existing_indexes = _index_names(table_name)
    for index_name, column_names, unique in indexes:
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, list(column_names), unique=unique)


def upgrade() -> None:
    # Parents are created before new child tables.  ``crawl_tasks`` may already
    # exist because revision 0001 was released before the complete baseline.
    _ensure_table(
        "crawl_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(255)),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("pages_ok", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("notes", sa.Text()),
        indexes=(("ix_crawl_runs_status", ("status",), False),),
    )
    _ensure_table(
        "notices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("url_hash", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("source_kind", sa.String(32), nullable=False, server_default="web"),
        sa.Column("notice_code", sa.String(255)),
        sa.Column("source_notice_id", sa.String(255)),
        sa.Column("source_name", sa.String(255)),
        sa.Column("plan_code", sa.String(255)),
        sa.Column("title", sa.Text()),
        sa.Column("buyer", sa.Text()),
        sa.Column("procuring_entity_address", sa.Text()),
        sa.Column("buyer_tax_code", sa.String(32)),
        sa.Column("investor", sa.Text()),
        sa.Column("investor_tax_code", sa.String(32)),
        sa.Column("project_name", sa.Text()),
        sa.Column("package_description", sa.Text()),
        sa.Column("package_price", sa.Float()),
        sa.Column("estimated_price", sa.Float()),
        sa.Column("currency", sa.String(16)),
        sa.Column("published_at", sa.String(64)),
        sa.Column("closing_at", sa.String(64)),
        sa.Column("location", sa.Text()),
        sa.Column("sector", sa.Text()),
        sa.Column("selection_method", sa.Text()),
        sa.Column("selection_form", sa.Text()),
        sa.Column("notice_version", sa.String(128)),
        sa.Column("notice_type", sa.String(32), nullable=False, server_default="tbmt"),
        sa.Column("funding_source", sa.Text()),
        sa.Column("contract_type", sa.String(64)),
        sa.Column("bid_type", sa.String(64)),
        sa.Column("document_issue_at", sa.DateTime(timezone=True)),
        sa.Column("document_price", sa.Float()),
        sa.Column("bid_security_amount", sa.Float()),
        sa.Column("bid_security_method", sa.Text()),
        sa.Column("issue_location", sa.Text()),
        sa.Column("published_at_dt", sa.DateTime(timezone=True)),
        sa.Column("closing_at_dt", sa.DateTime(timezone=True)),
        sa.Column("bid_open_at", sa.DateTime(timezone=True)),
        sa.Column("contract_duration", sa.Text()),
        sa.Column("crawl_run_id", sa.Integer()),
        sa.Column("crawl_status", sa.String(32), nullable=False, server_default="ok"),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("ai_sector", sa.Text()),
        sa.Column("ai_sector_code", sa.String(32)),
        sa.Column("ai_confidence", sa.Float()),
        sa.Column("raw_text", sa.Text()),
        sa.Column("raw_html_path", sa.Text()),
        sa.Column("data_quality_status", sa.String(32), nullable=False, server_default="valid"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("url_hash", name="uq_notices_url_hash"),
        indexes=(
            ("ix_notices_url_hash", ("url_hash",), True),
            ("ix_notices_content_hash", ("content_hash",), False),
            ("ix_notices_notice_code", ("notice_code",), False),
            ("ix_notices_source_notice_id", ("source_notice_id",), False),
            ("ix_notices_source_name", ("source_name",), False),
            ("ix_notices_plan_code", ("plan_code",), False),
            ("ix_notices_buyer_tax_code", ("buyer_tax_code",), False),
            ("ix_notices_investor_tax_code", ("investor_tax_code",), False),
            ("ix_notices_notice_version", ("notice_version",), False),
            ("ix_notices_notice_type", ("notice_type",), False),
            ("ix_notices_published_at_dt", ("published_at_dt",), False),
            ("ix_notices_closing_at_dt", ("closing_at_dt",), False),
            ("ix_notices_crawl_run_id", ("crawl_run_id",), False),
            ("ix_notices_crawl_status", ("crawl_status",), False),
            ("ix_notices_review_status", ("review_status",), False),
        ),
    )
    _ensure_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("notice_id", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("file_name", sa.Text()),
        sa.Column("local_path", sa.Text()),
        sa.Column("sha256", sa.String(64)),
        sa.Column("content_type", sa.String(255)),
        sa.Column("size_bytes", sa.Integer()),
        sa.Column("download_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("download_method", sa.String(32)),
        sa.Column("download_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("download_error", sa.Text()),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("downloaded_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["notice_id"], ["notices.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("notice_id", "source_url", name="uq_attachment_notice_url"),
        indexes=(
            ("ix_attachments_notice_id", ("notice_id",), False),
            ("ix_attachments_sha256", ("sha256",), False),
            ("ix_attachments_download_status", ("download_status",), False),
        ),
    )
    _ensure_table(
        "tender_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("notice_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(255), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("specification", sa.Text()),
        sa.Column("quantity", sa.Float()),
        sa.Column("minimum_quantity", sa.Float()),
        sa.Column("maximum_quantity", sa.Float()),
        sa.Column("unit", sa.String(64)),
        sa.Column("source_document", sa.Text()),
        sa.Column("source_location", sa.Text()),
        sa.Column("extraction_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("needs_human_review", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["notice_id"], ["notices.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("notice_id", "item_code", name="uq_tender_item_notice_code"),
        indexes=(("ix_tender_items_notice_id", ("notice_id",), False), ("ix_tender_items_needs_human_review", ("needs_human_review",), False)),
    )
    _ensure_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(255), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("aliases", sa.Text()),
        sa.Column("quantity_available", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(64)),
        sa.Column("warehouse", sa.Text()),
        sa.Column("source_file", sa.Text()),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("sku", name="uq_inventory_items_sku"),
        indexes=(("ix_inventory_items_sku", ("sku",), True), ("ix_inventory_items_verified", ("verified",), False)),
    )
    _ensure_table(
        "crawl_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("crawl_run_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["crawl_run_id"], ["crawl_runs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("crawl_run_id", "url", name="uq_crawl_task_run_url"),
        indexes=(("ix_crawl_tasks_crawl_run_id", ("crawl_run_id",), False), ("ix_crawl_tasks_status", ("status",), False)),
    )
    _ensure_table(
        "company_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evidence_code", sa.String(255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("evidence_type", sa.String(64), nullable=False, server_default="other"),
        sa.Column("description", sa.Text()), sa.Column("keywords", sa.Text()), sa.Column("source_path", sa.Text()),
        sa.Column("valid_until", sa.String(64)), sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("evidence_code", name="uq_company_evidence_code"),
        indexes=(("ix_company_evidence_evidence_code", ("evidence_code",), True), ("ix_company_evidence_evidence_type", ("evidence_type",), False), ("ix_company_evidence_verified", ("verified",), False)),
    )
    _ensure_table(
        "bid_requirements",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("notice_id", sa.Integer()),
        sa.Column("requirement_code", sa.String(255), nullable=False), sa.Column("category", sa.String(64), nullable=False, server_default="technical"),
        sa.Column("source_text", sa.Text(), nullable=False), sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("keywords", sa.Text()), sa.Column("mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("requirement_type", sa.String(32), nullable=False, server_default="mandatory"), sa.Column("source_reference", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["notice_id"], ["notices.id"], ondelete="CASCADE"),
        indexes=(("ix_bid_requirements_notice_id", ("notice_id",), False), ("ix_bid_requirements_requirement_code", ("requirement_code",), False), ("ix_bid_requirements_category", ("category",), False), ("ix_bid_requirements_mandatory", ("mandatory",), False), ("ix_bid_requirements_requirement_type", ("requirement_type",), False)),
    )
    _ensure_table(
        "compliance_assessments",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("requirement_id", sa.Integer(), nullable=False), sa.Column("evidence_id", sa.Integer()),
        sa.Column("status", sa.String(32), nullable=False), sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("matched_keywords", sa.Text()), sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("requires_human_confirmation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("variance_type", sa.String(32), nullable=False, server_default="none"), sa.Column("variance_impact", sa.Text()),
        sa.Column("reviewer_decision", sa.String(32)), sa.Column("confirmed_by", sa.String(255)), sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requirement_id"], ["bid_requirements.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["evidence_id"], ["company_evidence.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("requirement_id", "evidence_id", name="uq_requirement_evidence"),
        indexes=(("ix_compliance_assessments_requirement_id", ("requirement_id",), False), ("ix_compliance_assessments_evidence_id", ("evidence_id",), False), ("ix_compliance_assessments_status", ("status",), False), ("ix_compliance_assessments_variance_type", ("variance_type",), False), ("ix_compliance_assessments_reviewer_decision", ("reviewer_decision",), False)),
    )
    _ensure_table(
        "bid_predictions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("notice_id", sa.Integer()), sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False), sa.Column("estimated_win_percent", sa.Float(), nullable=False), sa.Column("confidence_percent", sa.Float(), nullable=False),
        sa.Column("gate_status", sa.String(32), nullable=False, server_default="HOLD"), sa.Column("mandatory_coverage_percent", sa.Float(), nullable=False), sa.Column("evidence_coverage_percent", sa.Float(), nullable=False),
        sa.Column("risk_factors", sa.Text(), nullable=False), sa.Column("assumptions", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["notice_id"], ["notices.id"], ondelete="CASCADE"),
        indexes=(("ix_bid_predictions_notice_id", ("notice_id",), False), ("ix_bid_predictions_gate_status", ("gate_status",), False)),
    )
    _ensure_table(
        "selection_plans",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("plan_code", sa.String(255), nullable=False), sa.Column("source_url", sa.Text(), nullable=False), sa.Column("url_hash", sa.String(64), nullable=False), sa.Column("content_hash", sa.String(64)),
        sa.Column("project_name", sa.Text()), sa.Column("investor", sa.Text()), sa.Column("investor_tax_code", sa.String(32)), sa.Column("buyer", sa.Text()), sa.Column("buyer_tax_code", sa.String(32)), sa.Column("total_investment", sa.Float()), sa.Column("currency", sa.String(16)), sa.Column("funding_source", sa.Text()), sa.Column("location", sa.Text()), sa.Column("sector", sa.Text()), sa.Column("approval_date", sa.String(64)), sa.Column("expected_start", sa.String(64)), sa.Column("expected_end", sa.String(64)), sa.Column("package_count", sa.Integer()), sa.Column("status", sa.String(32), nullable=False, server_default="active"), sa.Column("raw_text", sa.Text()), sa.Column("raw_html_path", sa.Text()), sa.Column("data_quality_status", sa.String(32), nullable=False, server_default="valid"), sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False), sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("plan_code", name="uq_selection_plans_plan_code"), sa.UniqueConstraint("url_hash", name="uq_selection_plans_url_hash"),
        indexes=(("ix_selection_plans_plan_code", ("plan_code",), True), ("ix_selection_plans_url_hash", ("url_hash",), True), ("ix_selection_plans_content_hash", ("content_hash",), False), ("ix_selection_plans_investor_tax_code", ("investor_tax_code",), False), ("ix_selection_plans_buyer_tax_code", ("buyer_tax_code",), False), ("ix_selection_plans_status", ("status",), False)),
    )
    _ensure_table(
        "bid_results",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("notice_id", sa.Integer(), nullable=False), sa.Column("notice_code", sa.String(255)), sa.Column("plan_code", sa.String(255)), sa.Column("result_code", sa.String(255)), sa.Column("contractor_name", sa.Text(), nullable=False), sa.Column("contractor_tax_code", sa.String(32)), sa.Column("is_winner", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("bid_price", sa.Float()), sa.Column("winning_price", sa.Float()), sa.Column("currency", sa.String(16)), sa.Column("discount_rate", sa.Float()), sa.Column("contract_duration", sa.Text()), sa.Column("evaluation_score", sa.Float()), sa.Column("ranking", sa.Integer()), sa.Column("result_date", sa.String(64)), sa.Column("source_url", sa.Text()), sa.Column("raw_text", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["notice_id"], ["notices.id"], ondelete="CASCADE"), sa.UniqueConstraint("notice_id", "contractor_name", name="uq_bid_result_notice_contractor"),
        indexes=(("ix_bid_results_notice_id", ("notice_id",), False), ("ix_bid_results_notice_code", ("notice_code",), False), ("ix_bid_results_plan_code", ("plan_code",), False), ("ix_bid_results_result_code", ("result_code",), False), ("ix_bid_results_contractor_tax_code", ("contractor_tax_code",), False), ("ix_bid_results_is_winner", ("is_winner",), False)),
    )
    _ensure_table(
        "bid_openings",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("notice_id", sa.Integer(), nullable=False), sa.Column("notice_code", sa.String(255)), sa.Column("contractor_name", sa.Text(), nullable=False), sa.Column("contractor_tax_code", sa.String(32)), sa.Column("bid_price", sa.Float()), sa.Column("currency", sa.String(16)), sa.Column("bid_security_amount", sa.Float()), sa.Column("technical_score", sa.Float()), sa.Column("opening_date", sa.String(64)), sa.Column("status", sa.String(64)), sa.Column("source_url", sa.Text()), sa.Column("raw_text", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["notice_id"], ["notices.id"], ondelete="CASCADE"), sa.UniqueConstraint("notice_id", "contractor_name", name="uq_bid_opening_notice_contractor"),
        indexes=(("ix_bid_openings_notice_id", ("notice_id",), False), ("ix_bid_openings_notice_code", ("notice_code",), False), ("ix_bid_openings_contractor_tax_code", ("contractor_tax_code",), False)),
    )
    _ensure_table(
        "contractors",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tax_code", sa.String(32), nullable=False), sa.Column("name", sa.Text(), nullable=False), sa.Column("short_name", sa.Text()), sa.Column("address", sa.Text()), sa.Column("province", sa.Text()), sa.Column("phone", sa.String(64)), sa.Column("email", sa.String(255)), sa.Column("representative", sa.Text()), sa.Column("business_type", sa.String(128)), sa.Column("main_sectors", sa.Text()), sa.Column("total_wins", sa.Integer(), nullable=False, server_default="0"), sa.Column("total_bids", sa.Integer(), nullable=False, server_default="0"), sa.Column("total_win_value", sa.Float(), nullable=False, server_default="0"), sa.Column("win_rate", sa.Float()), sa.Column("avg_discount_rate", sa.Float()), sa.Column("source_url", sa.Text()), sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False), sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tax_code", name="uq_contractors_tax_code"), indexes=(("ix_contractors_tax_code", ("tax_code",), True), ("ix_contractors_province", ("province",), False)),
    )
    _ensure_table(
        "investor_profiles",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tax_code", sa.String(32), nullable=False), sa.Column("name", sa.Text(), nullable=False), sa.Column("short_name", sa.Text()), sa.Column("address", sa.Text()), sa.Column("province", sa.Text()), sa.Column("phone", sa.String(64)), sa.Column("email", sa.String(255)), sa.Column("organization_type", sa.String(128)), sa.Column("total_packages", sa.Integer(), nullable=False, server_default="0"), sa.Column("total_package_value", sa.Float(), nullable=False, server_default="0"), sa.Column("main_sectors", sa.Text()), sa.Column("source_url", sa.Text()), sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False), sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tax_code", name="uq_investor_profiles_tax_code"), indexes=(("ix_investor_profiles_tax_code", ("tax_code",), True), ("ix_investor_profiles_province", ("province",), False)),
    )


def downgrade() -> None:
    # This is an additive safety migration.  Reversing it could remove user data,
    # so restoration must be performed from a verified backup instead.
    raise NotImplementedError("0003_complete_core_schema is intentionally non-destructive")
