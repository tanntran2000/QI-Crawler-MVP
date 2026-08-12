"""Config-driven adapters for tender websites.

Each new portal adds one adapter class and one entry under ``sources`` in the
YAML configuration. The crawler core only asks this registry for a supported
URL and a normalized ``ParsedNotice``.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from .config import AppConfig, SourceConfig
from .parser import ParsedNotice, extract_detail_links, parse_notice_html


@dataclass(frozen=True)
class SourceIdentity:
    source_name: str
    source_notice_id: str | None


@dataclass(frozen=True)
class DiscoveredTender:
    """A stable detail URL discovered from one source-list page."""

    url: str
    source_notice_id: str
    metadata_text: str = ""


class SourceAdapter(ABC):
    def __init__(self, source_name: str, source: SourceConfig):
        self.source_name = source_name
        self.source = source

    def supports(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return hostname == self.source.domain or hostname.endswith(f".{self.source.domain}")

    @abstractmethod
    def extract_identity(self, url: str, html: str) -> SourceIdentity:
        """Return the website-local stable identifier, if the URL/page provides one."""

    def discover(self, html: str, list_url: str) -> list[str]:
        return extract_detail_links(html, list_url, "a[href]", "a[href]", [self.source.domain])

    def discover_tenders(self, html: str, list_url: str) -> list[DiscoveredTender]:
        """Return normalized tender candidates; source-specific adapters override this."""
        return [
            DiscoveredTender(url=url, source_notice_id=self.extract_identity(url, html).source_notice_id or "")
            for url in self.discover(html, list_url)
        ]

    def pagination_links(self, html: str, list_url: str) -> list[str]:
        """List pages are source-specific; generic adapters do not paginate by default."""
        return []

    def parse_detail(self, html: str, url: str) -> ParsedNotice:
        parsed = parse_notice_html(html, url)
        identity = self.extract_identity(url, html)
        parsed.source_name = identity.source_name
        parsed.source_notice_id = identity.source_notice_id or parsed.source_notice_id
        return parsed


class EGPAdapter(SourceAdapter):
    def extract_identity(self, url: str, html: str) -> SourceIdentity:
        query = parse_qs(urlparse(url).query)
        source_id = next(
            (query[key][0] for key in ("notifyNo", "noticeId", "notice_id") if query.get(key)),
            None,
        )
        return SourceIdentity(self.source_name, source_id)


class CotecconsAdapter(SourceAdapter):
    _DETAIL_PATH = re.compile(r"^/Index/ChiTiet/(?P<notice_id>\d+)/?$", re.IGNORECASE)
    _PAGE_QUERY_KEYS = frozenset({"page", "p", "pageindex", "pagenumber"})

    def extract_identity(self, url: str, html: str) -> SourceIdentity:
        match = self._DETAIL_PATH.fullmatch(urlparse(url).path)
        source_id = match["notice_id"] if match else None
        return SourceIdentity(self.source_name, source_id)

    @staticmethod
    def _normalized_url(base_url: str, href: str) -> str | None:
        href = href.strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            return None
        parsed = urlparse(urljoin(base_url, href))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        return urlunparse(parsed._replace(fragment=""))

    def _same_domain(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return hostname == self.source.domain or hostname.endswith(f".{self.source.domain}")

    def discover_tenders(self, html: str, list_url: str) -> list[DiscoveredTender]:
        soup = BeautifulSoup(html, "html.parser")
        unique: dict[str, DiscoveredTender] = {}
        seen_ids: set[str] = set()
        for anchor in soup.select("a[href]"):
            url = self._normalized_url(list_url, str(anchor.get("href") or ""))
            if url is None or not self._same_domain(url):
                continue
            match = self._DETAIL_PATH.fullmatch(urlparse(url).path)
            if match is None:
                continue
            source_notice_id = match["notice_id"]
            if source_notice_id in seen_ids:
                continue
            seen_ids.add(source_notice_id)
            container = anchor.find_parent(["tr", "li", "article", "div"])
            metadata = (container or anchor).get_text(" ", strip=True)
            unique[url] = DiscoveredTender(url, source_notice_id, metadata)
        return list(unique.values())

    def discover(self, html: str, list_url: str) -> list[str]:
        return [item.url for item in self.discover_tenders(html, list_url)]

    def pagination_links(self, html: str, list_url: str) -> list[str]:
        """Return only same-domain Coteccons pagination targets, never detail links."""
        soup = BeautifulSoup(html, "html.parser")
        links: dict[str, None] = {}
        current_query = parse_qs(urlparse(list_url).query)
        current_page = next(
            (
                int(values[0])
                for key, values in current_query.items()
                if key.casefold() in self._PAGE_QUERY_KEYS and values and values[0].isdigit()
            ),
            1,
        )
        for anchor in soup.select("a[href]"):
            url = self._normalized_url(list_url, str(anchor.get("href") or ""))
            if url is None or not self._same_domain(url):
                continue
            parsed = urlparse(url)
            if self._DETAIL_PATH.fullmatch(parsed.path):
                continue
            attributes = " ".join(
                str(anchor.get(name) or "")
                for name in ("class", "id", "rel", "aria-label", "title")
            ).casefold()
            query_keys = {key.casefold() for key in parse_qs(parsed.query)}
            has_page_marker = (
                bool(query_keys & self._PAGE_QUERY_KEYS)
                or "pagination" in attributes
                or "page" in attributes
                or "next" in attributes
            )
            if has_page_marker:
                target_page = next(
                    (
                        int(values[0])
                        for key, values in parse_qs(parsed.query).items()
                        if key.casefold() in self._PAGE_QUERY_KEYS
                        and values
                        and values[0].isdigit()
                    ),
                    None,
                )
                if target_page is not None and target_page <= current_page:
                    continue
                links.setdefault(url, None)
        return list(links)


_ADAPTER_TYPES: dict[str, type[SourceAdapter]] = {
    "egp": EGPAdapter,
    "coteccons": CotecconsAdapter,
}


class SourceRegistry:
    def __init__(self, config: AppConfig):
        self._adapters = tuple(
            _ADAPTER_TYPES[source.adapter](name, source)
            for name, source in sorted(
                config.sources.items(), key=lambda item: item[1].priority
            )
            if source.enabled and source.adapter in _ADAPTER_TYPES
        )

    def adapter_for_url(self, url: str) -> SourceAdapter | None:
        return next((adapter for adapter in self._adapters if adapter.supports(url)), None)

    def require_adapter(self, url: str) -> SourceAdapter:
        adapter = self.adapter_for_url(url)
        if adapter is None:
            raise ValueError("URL khong thuoc nguon dang bat trong cau hinh sources.")
        return adapter
