"""Human-declared tender workspaces for Team Bid supplied HSMT files."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import or_, select

from .db import Database
from .models import Notice, utcnow

MANUAL_TEAM_BID = "MANUAL_TEAM_BID"
HUMAN_DECLARED = "HUMAN_DECLARED"
HUMAN_SHORTLISTED = "HUMAN_SHORTLISTED"
NOT_SHORTLISTED = "NOT_SHORTLISTED"
BUSINESS_PRIORITIES = frozenset({"LOW", "NORMAL", "HIGH", "CRITICAL"})


class ManualTenderWorkspaceError(ValueError):
    """A human workspace cannot safely be created from the supplied identity."""


@dataclass(frozen=True)
class ManualTenderWorkspace:
    tender_id: int
    tender_code: str
    title: str
    source_origin: str
    identity_status: str
    screening_status: str
    business_priority: str


class ManualTenderWorkspaceService:
    """Create a stored human-declared tender without fabricating a source URL."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.database.require_current_schema()

    def create_workspace(
        self,
        tender_code: str,
        *,
        package_name: str | None = None,
        shortlisted: bool = False,
        business_priority: str = "NORMAL",
        reviewed_by: str | None = None,
        manual_note: str | None = None,
    ) -> ManualTenderWorkspace:
        code = _required_text("tender_code", tender_code)
        priority = _required_text("business_priority", business_priority).upper()
        if priority not in BUSINESS_PRIORITIES:
            raise ManualTenderWorkspaceError("business_priority is invalid.")
        with self.database.session() as session:
            existing = session.scalar(
                select(Notice)
                .where(or_(Notice.notice_code == code, Notice.source_notice_id == code))
                .limit(1)
            )
            if existing is not None:
                raise ManualTenderWorkspaceError(
                    "Tender code already exists; manual and web identities require human review."
                )
            notice = Notice(
                source_url=None,
                url_hash=sha256(f"{MANUAL_TEAM_BID}:{code}".encode()).hexdigest(),
                source_kind="manual",
                source_origin=MANUAL_TEAM_BID,
                source_name="team_bid",
                notice_code=code,
                title=_optional_text(package_name) or code,
                identity_status=HUMAN_DECLARED,
                screening_status=HUMAN_SHORTLISTED if shortlisted else NOT_SHORTLISTED,
                business_priority=priority,
                reviewed_by=_optional_text(reviewed_by),
                reviewed_at=utcnow() if _optional_text(reviewed_by) else None,
                manual_note=_optional_text(manual_note),
            )
            session.add(notice)
            session.flush()
            return ManualTenderWorkspace(
                tender_id=notice.id,
                tender_code=code,
                title=notice.title or code,
                source_origin=notice.source_origin,
                identity_status=notice.identity_status,
                screening_status=notice.screening_status or NOT_SHORTLISTED,
                business_priority=notice.business_priority,
            )


def _required_text(name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ManualTenderWorkspaceError(f"{name} is required.")
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None
