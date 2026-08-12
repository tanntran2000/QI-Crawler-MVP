"""Keep user-facing search and exports limited to enabled tender sources."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import and_, false, func, or_
from sqlalchemy.sql.elements import ColumnElement

from .config import AppConfig
from .models import Notice


def active_source_names(config: AppConfig) -> frozenset[str]:
    return frozenset(name for name, source in config.sources.items() if source.enabled)


def active_source_domains(config: AppConfig) -> tuple[str, ...]:
    return tuple(source.domain for source in config.sources.values() if source.enabled)


def active_notice_filter(
    source_names: Iterable[str] | None, source_domains: Iterable[str] | None
) -> ColumnElement[bool]:
    """Apply an explicit source policy, with a strict URL-host legacy fallback."""
    if source_names is None and source_domains is None:
        # Low-level callers without a configuration policy retain their
        # historical behaviour.  User-facing CLI commands always pass an
        # explicit policy, including an empty one when all sources are off.
        return Notice.id.is_not(None)
    names = tuple(source_names or ())
    domains = tuple(
        domain.casefold().strip().rstrip(".") for domain in (source_domains or ()) if domain
    )
    clauses = []
    if names:
        clauses.append(Notice.source_name.in_(names))
    source_name_missing = or_(Notice.source_name.is_(None), func.trim(Notice.source_name) == "")
    for domain in domains:
        # This matches the URL scheme and host boundary, never a domain merely
        # mentioned in another website's path or query string.
        source_url = func.lower(Notice.source_url)
        clauses.append(
            and_(
                source_name_missing,
                or_(
                    source_url == f"https://{domain}",
                    source_url.like(f"https://{domain}/%"),
                    source_url.like(f"https://{domain}?%"),
                    source_url == f"http://{domain}",
                    source_url.like(f"http://{domain}/%"),
                    source_url.like(f"http://{domain}?%"),
                ),
            )
        )
    if not clauses:
        return false()
    return or_(*clauses)
