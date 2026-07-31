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
    title: Mapped[str | None] = mapped_column(Text)
    buyer: Mapped[str | None] = mapped_column(Text)
    investor: Mapped[str | None] = mapped_column(Text)
    package_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(16))
    published_at: Mapped[str | None] = mapped_column(String(64))
    closing_at: Mapped[str | None] = mapped_column(String(64))
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
