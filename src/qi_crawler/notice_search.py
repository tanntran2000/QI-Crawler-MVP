"""Database-backed tender search with an optional SQLite FTS5 fast path."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select, text

from .db import Database
from .keywords import matches_any_keyword, normalize_keyword
from .models import Notice
from .source_filter import active_notice_filter


@dataclass(frozen=True)
class NoticeSearchResult:
    notices: list[Notice]
    used_fts5: bool


def _fts_query(terms: tuple[str, ...]) -> str:
    phrases = []
    for term in terms:
        normalized = normalize_keyword(term)
        if normalized:
            safe_phrase = normalized.replace('"', "")
            phrases.append(f'"{safe_phrase}"')
    return " OR ".join(dict.fromkeys(phrases))


def _fts_table_exists(database: Database) -> bool:
    with database.engine.connect() as connection:
        return bool(
            connection.scalar(
                text(
                    "SELECT 1 FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'notice_fts'"
                )
            )
        )


def _fts_search(
    database: Database,
    terms: tuple[str, ...],
    since: date | None,
    limit: int,
    active_names: tuple[str, ...] | None,
    active_domains: tuple[str, ...] | None,
) -> list[Notice]:
    query = _fts_query(terms)
    if not query:
        return []
    with database.session() as session:
        statement = (
            select(Notice)
            .where(
                Notice.id.in_(
                    text("SELECT notice_id FROM notice_fts WHERE notice_fts MATCH :query")
                )
            )
            .where(active_notice_filter(active_names, active_domains))
            .order_by(Notice.last_seen_at.desc())
            .limit(limit)
            .params(query=query)
        )
        if since:
            statement = statement.where(Notice.last_seen_at >= since)
        return list(session.scalars(statement).all())


def _fallback_search(
    database: Database,
    terms: tuple[str, ...],
    since: date | None,
    limit: int,
    active_names: tuple[str, ...] | None,
    active_domains: tuple[str, ...] | None,
) -> list[Notice]:
    """Portable fallback for SQLite builds without FTS5."""
    with database.session() as session:
        statement = (
            select(Notice)
            .where(active_notice_filter(active_names, active_domains))
            .order_by(Notice.last_seen_at.desc())
        )
        if since:
            statement = statement.where(Notice.last_seen_at >= since)
        notices = session.scalars(statement).all()
    matches = []
    for notice in notices:
        searchable = " ".join(
            value or ""
            for value in (notice.title, notice.package_description, notice.buyer, notice.raw_text)
        )
        if matches_any_keyword(searchable, terms):
            matches.append(notice)
        if len(matches) >= limit:
            break
    return matches


def search_notices(
    database: Database,
    terms: tuple[str, ...],
    since: date | None,
    limit: int,
    active_names: tuple[str, ...] | None = None,
    active_domains: tuple[str, ...] | None = None,
) -> NoticeSearchResult:
    """Search without modifying the keyword pool or loading all rows when FTS5 exists."""
    if database.fts5_available() and _fts_table_exists(database):
        return NoticeSearchResult(
            _fts_search(database, terms, since, limit, active_names, active_domains), used_fts5=True
        )
    return NoticeSearchResult(
        _fallback_search(database, terms, since, limit, active_names, active_domains), used_fts5=False
    )
