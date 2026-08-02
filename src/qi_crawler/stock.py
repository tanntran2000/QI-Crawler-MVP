from __future__ import annotations

import re
from dataclasses import dataclass

from .keywords import normalize_keyword
from .models import InventoryItem, TenderItem


@dataclass(frozen=True)
class StockCheck:
    tender_item_id: int
    inventory_sku: str | None
    required_quantity: float | None
    available_quantity: float | None
    shortage_quantity: float | None
    status: str
    match_confidence: float
    note: str


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", normalize_keyword(value)))


def _inventory_terms(item: InventoryItem) -> list[str]:
    aliases = re.split(r"[,;|]", item.aliases or "")
    return [item.product_name, item.sku, *(value.strip() for value in aliases if value.strip())]


def _match_score(required_name: str, stock: InventoryItem) -> float:
    required = _tokens(required_name)
    if not required:
        return 0.0
    best = 0.0
    for term in _inventory_terms(stock):
        candidate = _tokens(term)
        if not candidate:
            continue
        intersection = len(required & candidate)
        union = len(required | candidate)
        best = max(best, intersection / union if union else 0.0)
        if required.issubset(candidate) or candidate.issubset(required):
            best = max(best, 0.9)
    return round(best, 3)


UNIT_ALIASES = {
    "piece": "piece",
    "pieces": "piece",
    "pcs": "piece",
    "pc": "piece",
    "unit": "piece",
    "units": "piece",
    "cai": "piece",
    "bo": "set",
    "set": "set",
    "sets": "set",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ton": "tonne",
    "tons": "tonne",
    "tonne": "tonne",
    "tonnes": "tonne",
    "m": "metre",
    "meter": "metre",
    "meters": "metre",
    "metre": "metre",
    "metres": "metre",
}


def _unit(value: str | None) -> str:
    normalized = normalize_keyword(value or "")
    return UNIT_ALIASES.get(normalized, normalized)


def check_stock(item: TenderItem, inventory: list[InventoryItem]) -> StockCheck:
    candidates = sorted(
        ((_match_score(item.product_name, stock), stock) for stock in inventory if stock.verified),
        key=lambda pair: pair[0],
        reverse=True,
    )
    if not candidates or candidates[0][0] < 0.5:
        return StockCheck(
            item.id,
            None,
            item.quantity,
            None,
            None,
            "NOT_IN_VERIFIED_STOCK",
            candidates[0][0] if candidates else 0.0,
            "No sufficiently similar verified inventory item",
        )
    confidence, stock = candidates[0]
    if item.quantity is None:
        return StockCheck(
            item.id,
            stock.sku,
            None,
            stock.quantity_available,
            None,
            "REVIEW_REQUIRED_QUANTITY",
            confidence,
            "Tender quantity is missing or could not be extracted",
        )
    required_unit = _unit(item.unit)
    stock_unit = _unit(stock.unit)
    if required_unit and stock_unit and required_unit != stock_unit:
        return StockCheck(
            item.id,
            stock.sku,
            item.quantity,
            stock.quantity_available,
            None,
            "REVIEW_UNIT_MISMATCH",
            confidence,
            f"Tender unit '{item.unit}' differs from stock unit '{stock.unit}'",
        )
    shortage = max(item.quantity - stock.quantity_available, 0.0)
    status = "MEETS_STOCK" if shortage == 0 else "STOCK_SHORTAGE"
    note = "Available stock covers required quantity" if shortage == 0 else "Additional procurement is required"
    return StockCheck(
        item.id,
        stock.sku,
        item.quantity,
        stock.quantity_available,
        shortage,
        status,
        confidence,
        note,
    )
