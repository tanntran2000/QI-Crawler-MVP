"""Archive only recognised legacy/test notices before removing them from the live set."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .db import Database
from .models import Notice

LEGACY_SOURCE_LABELS = frozenset({"contracts_finder", "contracts-finder", "example", "test"})
LEGACY_DOMAINS = ("contractsfinder.service.gov.uk", "example.com")


@dataclass(frozen=True)
class LegacyCleanupResult:
    backup_path: Path | None
    archive_path: Path | None
    archived_notices: int
    backfilled_coteccons: int


_COTECCONS_HOST = "ebidding.coteccons.vn"
_COTECCONS_DETAIL_PATH = re.compile(r"^/Index/ChiTiet/(?P<notice_id>\d+)/?$", re.IGNORECASE)


def _repair_known_coteccons_records(notices: list[Notice]) -> int:
    """Backfill identity for legacy Coteccons detail URLs without overwriting known sources."""
    repaired = 0
    for notice in notices:
        parsed_url = urlparse(notice.source_url)
        if parsed_url.hostname != _COTECCONS_HOST:
            continue
        match = _COTECCONS_DETAIL_PATH.fullmatch(parsed_url.path)
        if match is None:
            continue
        changed = False
        if not (notice.source_name or "").strip():
            notice.source_name = "coteccons"
            changed = True
        if not (notice.source_notice_id or "").strip():
            notice.source_notice_id = match["notice_id"]
            changed = True
        if changed:
            repaired += 1
    return repaired


def _is_legacy_notice(notice: Notice) -> bool:
    source_labels = {
        value.strip().casefold() for value in (notice.source_name, notice.source_kind) if value
    }
    hostname = (urlparse(notice.source_url).hostname or "").casefold()
    is_coteccons_homepage = (
        hostname == _COTECCONS_HOST
        and urlparse(notice.source_url).path in ("", "/")
        and not (notice.source_notice_id or "").strip()
    )
    return is_coteccons_homepage or bool(source_labels & LEGACY_SOURCE_LABELS) or any(
        hostname == domain or hostname.endswith(f".{domain}") for domain in LEGACY_DOMAINS
    )


def archive_legacy_notices(
    database: Database,
    *,
    archive_dir: Path = Path("data/archive"),
    backup_path: Path | None = None,
) -> LegacyCleanupResult:
    """Write a local JSON archive, then remove recognised non-production records."""
    with database.session() as session:
        notices = list(
            session.scalars(
                select(Notice)
                .options(selectinload(Notice.attachments), selectinload(Notice.tender_items))
                .order_by(Notice.id)
            ).all()
        )
        legacy = [notice for notice in notices if _is_legacy_notice(notice)]
        repaired = _repair_known_coteccons_records(notices)
        if not legacy:
            return LegacyCleanupResult(backup_path, None, 0, repaired)
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / (
            f"legacy_notices_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        payload = [
            {
                "notice": {
                    column.name: getattr(notice, column.name)
                    for column in Notice.__table__.columns
                },
                "attachments": [
                    {column.name: getattr(item, column.name) for column in item.__table__.columns}
                    for item in notice.attachments
                ],
                "tender_items": [
                    {column.name: getattr(item, column.name) for column in item.__table__.columns}
                    for item in notice.tender_items
                ],
            }
            for notice in legacy
        ]
        archive_path.write_text(
            json.dumps(payload, ensure_ascii=False, default=str, indent=2), encoding="utf-8"
        )
        for notice in legacy:
            session.delete(notice)
    return LegacyCleanupResult(backup_path, archive_path, len(legacy), repaired)
