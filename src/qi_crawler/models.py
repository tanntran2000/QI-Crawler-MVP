from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


class Notice(Base):
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    source_kind: Mapped[str] = mapped_column(String(32), default="web")
    notice_code: Mapped[str | None] = mapped_column(String(255), index=True)
    source_notice_id: Mapped[str | None] = mapped_column(String(255), index=True)
    source_name: Mapped[str | None] = mapped_column(String(255), index=True)
    plan_code: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    buyer: Mapped[str | None] = mapped_column(Text)
    procuring_entity_address: Mapped[str | None] = mapped_column(Text)
    buyer_tax_code: Mapped[str | None] = mapped_column(String(32), index=True)
    investor: Mapped[str | None] = mapped_column(Text)
    investor_tax_code: Mapped[str | None] = mapped_column(String(32), index=True)
    project_name: Mapped[str | None] = mapped_column(Text)
    package_description: Mapped[str | None] = mapped_column(Text)
    package_price: Mapped[float | None] = mapped_column(Float)
    estimated_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(16))
    published_at: Mapped[str | None] = mapped_column(String(64))
    closing_at: Mapped[str | None] = mapped_column(String(64))
    location: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(Text)
    selection_method: Mapped[str | None] = mapped_column(Text)
    selection_form: Mapped[str | None] = mapped_column(Text)
    notice_version: Mapped[str | None] = mapped_column(String(128), index=True)
    notice_type: Mapped[str] = mapped_column(String(32), default="tbmt", index=True)
    funding_source: Mapped[str | None] = mapped_column(Text)
    contract_type: Mapped[str | None] = mapped_column(String(64))
    bid_type: Mapped[str | None] = mapped_column(String(64))
    document_issue_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    document_price: Mapped[float | None] = mapped_column(Float)
    bid_security_amount: Mapped[float | None] = mapped_column(Float)
    bid_security_method: Mapped[str | None] = mapped_column(Text)
    issue_location: Mapped[str | None] = mapped_column(Text)
    published_at_dt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    closing_at_dt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    bid_open_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contract_duration: Mapped[str | None] = mapped_column(Text)
    crawl_run_id: Mapped[int | None] = mapped_column(Integer, index=True)
    crawl_status: Mapped[str] = mapped_column(String(32), default="ok", index=True)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    ai_sector: Mapped[str | None] = mapped_column(Text)
    ai_sector_code: Mapped[str | None] = mapped_column(String(32))
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    raw_text: Mapped[str | None] = mapped_column(Text)
    raw_html_path: Mapped[str | None] = mapped_column(Text)
    data_quality_status: Mapped[str] = mapped_column(String(32), default="valid")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    attachments: Mapped[list[Attachment]] = relationship(
        back_populates="notice", cascade="all, delete-orphan"
    )
    tender_items: Mapped[list[TenderItem]] = relationship(
        back_populates="notice", cascade="all, delete-orphan"
    )
    bid_results: Mapped[list[BidResult]] = relationship(
        back_populates="notice", cascade="all, delete-orphan"
    )
    bid_openings: Mapped[list[BidOpening]] = relationship(
        back_populates="notice", cascade="all, delete-orphan"
    )


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = (UniqueConstraint("notice_id", "source_url", name="uq_attachment_notice_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[int] = mapped_column(ForeignKey("notices.id", ondelete="CASCADE"), index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str | None] = mapped_column(Text)
    local_path: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    content_type: Mapped[str | None] = mapped_column(String(255))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    download_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    download_method: Mapped[str | None] = mapped_column(String(32))
    download_attempts: Mapped[int] = mapped_column(Integer, default=0)
    download_error: Mapped[str | None] = mapped_column(Text)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    notice: Mapped[Notice] = relationship(back_populates="attachments")


class TenderItem(Base):
    """A requested product/line item with auditable quantity extraction."""

    __tablename__ = "tender_items"
    __table_args__ = (
        UniqueConstraint("notice_id", "item_code", name="uq_tender_item_notice_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[int] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), index=True
    )
    item_code: Mapped[str] = mapped_column(String(255))
    product_name: Mapped[str] = mapped_column(Text)
    specification: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float | None] = mapped_column(Float)
    minimum_quantity: Mapped[float | None] = mapped_column(Float)
    maximum_quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(64))
    source_document: Mapped[str | None] = mapped_column(Text)
    source_location: Mapped[str | None] = mapped_column(Text)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    needs_human_review: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    notice: Mapped[Notice] = relationship(back_populates="tender_items")


class InventoryItem(Base):
    """A current QI stock balance imported from an approved inventory file."""

    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    product_name: Mapped[str] = mapped_column(Text)
    aliases: Mapped[str | None] = mapped_column(Text)
    quantity_available: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str | None] = mapped_column(String(64))
    warehouse: Mapped[str | None] = mapped_column(Text)
    source_file: Mapped[str | None] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(default=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="running")
    pages_ok: Mapped[int] = mapped_column(Integer, default=0)
    pages_failed: Mapped[int] = mapped_column(Integer, default=0)
    records_found: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class CrawlTask(Base):
    """Per-URL crawl checkpoint; CrawlRun remains the run-level summary."""

    __tablename__ = "crawl_tasks"
    __table_args__ = (UniqueConstraint("crawl_run_id", "url", name="uq_crawl_task_run_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_run_id: Mapped[int] = mapped_column(
        ForeignKey("crawl_runs.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    page_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompanyEvidence(Base):
    """A verifiable capability, certificate, project or product owned by the bidder."""

    __tablename__ = "company_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    evidence_type: Mapped[str] = mapped_column(String(64), default="other", index=True)
    description: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text)
    source_path: Mapped[str | None] = mapped_column(Text)
    valid_until: Mapped[str | None] = mapped_column(String(64))
    verified: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BidRequirement(Base):
    """An auditable requirement extracted from an E-HSMT or related document."""

    __tablename__ = "bid_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[int | None] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), index=True
    )
    requirement_code: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(64), default="technical", index=True)
    source_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text)
    mandatory: Mapped[bool] = mapped_column(default=True, index=True)
    requirement_type: Mapped[str] = mapped_column(String(32), default="mandatory", index=True)
    source_reference: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ComplianceAssessment(Base):
    """Traceable match between one requirement and optional company evidence."""

    __tablename__ = "compliance_assessments"
    __table_args__ = (
        UniqueConstraint("requirement_id", "evidence_id", name="uq_requirement_evidence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("bid_requirements.id", ondelete="CASCADE"), index=True
    )
    evidence_id: Mapped[int | None] = mapped_column(
        ForeignKey("company_evidence.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    matched_keywords: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    requires_human_confirmation: Mapped[bool] = mapped_column(default=True)
    variance_type: Mapped[str] = mapped_column(String(32), default="none", index=True)
    variance_impact: Mapped[str | None] = mapped_column(Text)
    reviewer_decision: Mapped[str | None] = mapped_column(String(32), index=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(255))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BidPrediction(Base):
    """A versioned, explainable estimate; never a guarantee of procurement outcome."""

    __tablename__ = "bid_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[int | None] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), index=True
    )
    model_version: Mapped[str] = mapped_column(String(64))
    readiness_score: Mapped[float] = mapped_column(Float)
    estimated_win_percent: Mapped[float] = mapped_column(Float)
    confidence_percent: Mapped[float] = mapped_column(Float)
    gate_status: Mapped[str] = mapped_column(String(32), default="HOLD", index=True)
    mandatory_coverage_percent: Mapped[float] = mapped_column(Float)
    evidence_coverage_percent: Mapped[float] = mapped_column(Float)
    risk_factors: Mapped[str] = mapped_column(Text)
    assumptions: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SelectionPlan(Base):
    """Ke hoach lua chon nha thau (KHLCNT) crawled from e-GP."""

    __tablename__ = "selection_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    project_name: Mapped[str | None] = mapped_column(Text)
    investor: Mapped[str | None] = mapped_column(Text)
    investor_tax_code: Mapped[str | None] = mapped_column(String(32), index=True)
    buyer: Mapped[str | None] = mapped_column(Text)
    buyer_tax_code: Mapped[str | None] = mapped_column(String(32), index=True)
    total_investment: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(16))
    funding_source: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(Text)
    approval_date: Mapped[str | None] = mapped_column(String(64))
    expected_start: Mapped[str | None] = mapped_column(String(64))
    expected_end: Mapped[str | None] = mapped_column(String(64))
    package_count: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    raw_text: Mapped[str | None] = mapped_column(Text)
    raw_html_path: Mapped[str | None] = mapped_column(Text)
    data_quality_status: Mapped[str] = mapped_column(String(32), default="valid")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class BidResult(Base):
    """Ket qua lua chon nha thau (KQLCNT) for a specific notice/package."""

    __tablename__ = "bid_results"
    __table_args__ = (
        UniqueConstraint("notice_id", "contractor_name", name="uq_bid_result_notice_contractor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[int] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), index=True
    )
    notice_code: Mapped[str | None] = mapped_column(String(255), index=True)
    plan_code: Mapped[str | None] = mapped_column(String(255), index=True)
    result_code: Mapped[str | None] = mapped_column(String(255), index=True)
    contractor_name: Mapped[str] = mapped_column(Text)
    contractor_tax_code: Mapped[str | None] = mapped_column(String(32), index=True)
    is_winner: Mapped[bool] = mapped_column(default=False, index=True)
    bid_price: Mapped[float | None] = mapped_column(Float)
    winning_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(16))
    discount_rate: Mapped[float | None] = mapped_column(Float)
    contract_duration: Mapped[str | None] = mapped_column(Text)
    evaluation_score: Mapped[float | None] = mapped_column(Float)
    ranking: Mapped[int | None] = mapped_column(Integer)
    result_date: Mapped[str | None] = mapped_column(String(64))
    source_url: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    notice: Mapped[Notice] = relationship(back_populates="bid_results")


class BidOpening(Base):
    """Ket qua mo thau (KQMT) recording who participated in a bid opening."""

    __tablename__ = "bid_openings"
    __table_args__ = (
        UniqueConstraint("notice_id", "contractor_name", name="uq_bid_opening_notice_contractor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[int] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), index=True
    )
    notice_code: Mapped[str | None] = mapped_column(String(255), index=True)
    contractor_name: Mapped[str] = mapped_column(Text)
    contractor_tax_code: Mapped[str | None] = mapped_column(String(32), index=True)
    bid_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(16))
    bid_security_amount: Mapped[float | None] = mapped_column(Float)
    technical_score: Mapped[float | None] = mapped_column(Float)
    opening_date: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(64))
    source_url: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    notice: Mapped[Notice] = relationship(back_populates="bid_openings")


class Contractor(Base):
    """Ho so nha thau (contractor profile) built from KQLCNT/KQMT data."""

    __tablename__ = "contractors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tax_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    province: Mapped[str | None] = mapped_column(Text, index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    representative: Mapped[str | None] = mapped_column(Text)
    business_type: Mapped[str | None] = mapped_column(String(128))
    main_sectors: Mapped[str | None] = mapped_column(Text)
    total_wins: Mapped[int] = mapped_column(Integer, default=0)
    total_bids: Mapped[int] = mapped_column(Integer, default=0)
    total_win_value: Mapped[float] = mapped_column(Float, default=0.0)
    win_rate: Mapped[float | None] = mapped_column(Float)
    avg_discount_rate: Mapped[float | None] = mapped_column(Float)
    source_url: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class InvestorProfile(Base):
    """Ho so chu dau tu / ben moi thau built from TBMT/KHLCNT data."""

    __tablename__ = "investor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tax_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    province: Mapped[str | None] = mapped_column(Text, index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    organization_type: Mapped[str | None] = mapped_column(String(128))
    total_packages: Mapped[int] = mapped_column(Integer, default=0)
    total_package_value: Mapped[float] = mapped_column(Float, default=0.0)
    main_sectors: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
