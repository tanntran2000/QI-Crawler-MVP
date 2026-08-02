from __future__ import annotations

from collections.abc import Iterable

FORMULA_PREFIXES = ("=", "+", "-", "@")


def safe_excel_value(value: object) -> object:
    """Prevent untrusted text from being interpreted as a spreadsheet formula."""
    if not isinstance(value, str):
        return value
    candidate = value.lstrip(" \t\r\n")
    if candidate.startswith(FORMULA_PREFIXES):
        return f"'{value}"
    return value


def safe_excel_row(values: Iterable[object]) -> list[object]:
    return [safe_excel_value(value) for value in values]
