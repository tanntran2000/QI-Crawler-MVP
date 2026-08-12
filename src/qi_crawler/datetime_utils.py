"""Shared, UTC-safe parsing for tender dates from web pages and spreadsheets."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, date, datetime


def _fold_for_match(value: str) -> str:
    value = value.replace("Đ", "D").replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").lower()


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def has_explicit_time(value: datetime | date | str | None) -> bool:
    """Return whether a source value actually supplied an hour and minute.

    Date-only tender notices are stored as midnight internally for comparison,
    but callers must not present that technical midnight as a real deadline.
    """
    if isinstance(value, datetime):
        return True
    if isinstance(value, date) or value is None:
        return False
    text = " ".join(str(value).replace("\xa0", " ").split())
    if not text:
        return False
    return bool(
        re.search(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", text)
        or re.search(r"\b\d{1,2}\s*gio\s*\d{1,2}\b", _fold_for_match(text))
        or re.search(r"T\d{1,2}", text, re.IGNORECASE)
    )


def parse_datetime_utc(value: datetime | date | str | None) -> datetime | None:
    """Parse common e-GP, Vietnamese and ISO timestamps into an aware UTC datetime.

    A naive timestamp is treated as UTC because the crawler stores source timestamps
    without an explicit timezone. Callers therefore never compare naive and aware values.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _as_utc(value)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=UTC)

    text = " ".join(str(value).replace("\xa0", " ").split())
    if not text:
        return None
    try:
        return _as_utc(datetime.fromisoformat(text))
    except ValueError:
        pass

    vietnamese = re.search(
        r"(?P<hour>\d{1,2})\s*gio\s*(?P<minute>\d{1,2})\s*ngay\s*"
        r"(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})",
        _fold_for_match(text),
    )
    if vietnamese:
        parts = {key: int(item) for key, item in vietnamese.groupdict().items()}
        return datetime(
            parts["year"],
            parts["month"],
            parts["day"],
            parts["hour"],
            parts["minute"],
            tzinfo=UTC,
        )

    for format_string in (
        "%H:%M %d/%m/%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y - %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text, format_string).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None
