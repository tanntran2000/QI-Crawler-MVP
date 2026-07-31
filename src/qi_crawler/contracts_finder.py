from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

from .crawler import CrawlerService
from .keywords import matches_any_keyword
from .parser import ParsedAttachment, ParsedNotice

API_URL = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"


@dataclass
class ContractsFinderSummary:
    fetched: int = 0
    matched: int = 0
    inserted: int = 0
    updated: int = 0
    expired_skipped: int = 0


def _safe_document_name(document: dict, index: int) -> str:
    description = str(document.get("description") or document.get("documentType") or "document")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", description).strip("._") or f"document_{index}"
    format_value = str(document.get("format") or "").lower()
    extension = {
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/zip": ".zip",
    }.get(format_value, "")
    return stem if Path(stem).suffix else f"{stem}{extension}"


def release_to_notice(release: dict) -> ParsedNotice | None:
    tender = release.get("tender") or {}
    title = str(tender.get("title") or "").strip()
    if not title:
        return None
    documents = tender.get("documents") or []
    notice_url = next(
        (
            str(item.get("url"))
            for item in documents
            if item.get("documentType") == "tenderNotice" and item.get("url")
        ),
        "",
    )
    if not notice_url:
        release_id = str(release.get("id") or "").split("-")[0]
        notice_url = f"https://www.contractsfinder.service.gov.uk/Notice/{release_id}"
    attachments = [
        ParsedAttachment(
            source_url=str(item["url"]),
            file_name=_safe_document_name(item, index),
        )
        for index, item in enumerate(documents, start=1)
        if item.get("url") and item.get("documentType") != "tenderNotice"
    ]
    value = tender.get("value") or {}
    buyer = release.get("buyer") or {}
    description = str(tender.get("description") or "").strip()
    return ParsedNotice(
        source_url=notice_url,
        notice_code=str(release.get("ocid") or tender.get("id") or "") or None,
        title=title,
        buyer=str(buyer.get("name") or "").strip() or None,
        investor=None,
        package_price=float(value["amount"]) if value.get("amount") is not None else None,
        currency=str(value.get("currency") or "").strip() or None,
        published_at=str(tender.get("datePublished") or release.get("date") or "") or None,
        closing_at=str((tender.get("tenderPeriod") or {}).get("endDate") or "") or None,
        attachments=attachments,
        raw_text="\n".join(filter(None, [title, description, str(buyer.get("name") or "")])),
    )


def release_matches(release: dict, keyword: str | tuple[str, ...] | None) -> bool:
    if not keyword:
        return True
    tender = release.get("tender") or {}
    buyer = release.get("buyer") or {}
    haystack = " ".join(
        [str(tender.get("title") or ""), str(tender.get("description") or ""), str(buyer.get("name") or "")]
    )
    terms = (keyword,) if isinstance(keyword, str) else keyword
    return matches_any_keyword(haystack, terms)


async def collect_contracts_finder(
    service: CrawlerService,
    keyword: str | tuple[str, ...] | None = None,
    published_from: date | None = None,
    limit: int = 20,
    max_pages: int = 10,
    only_open: bool = True,
) -> ContractsFinderSummary:
    if "www.contractsfinder.service.gov.uk" not in service.config.allowed_domains:
        raise ValueError(
            "Cần thêm www.contractsfinder.service.gov.uk vào allowed_domains trong config.yaml"
        )
    start = published_from or (datetime.now(UTC).date() - timedelta(days=30))
    summary = ContractsFinderSummary()
    for page in range(1, max_pages + 1):
        query = urlencode(
            {
                "publishedFrom": start.isoformat(),
                "stages": "tender",
                "orderBy": "publishedDate",
                "order": "DESC",
                "size": 100,
                "page": page,
            }
        )
        response = await service.http.fetch(f"{API_URL}?{query}")
        payload = json.loads(response.text)
        releases = payload.get("releases") or []
        if not releases:
            break
        summary.fetched += len(releases)
        for release in releases:
            if not release_matches(release, keyword):
                continue
            parsed = release_to_notice(release)
            if parsed is None:
                continue
            if only_open and parsed.closing_at:
                try:
                    closing = datetime.fromisoformat(parsed.closing_at)
                    if closing.astimezone(UTC) <= datetime.now(UTC):
                        summary.expired_skipped += 1
                        continue
                except ValueError:
                    # Unknown date formats remain candidates for human review.
                    pass
            _, created, changed = service.upsert_parsed_notice(
                parsed, source_kind="contracts_finder"
            )
            summary.matched += 1
            summary.inserted += int(created)
            summary.updated += int(not created and changed)
            if summary.matched >= limit:
                return summary
    return summary
