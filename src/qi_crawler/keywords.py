from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_KEYWORD_GROUPS = Path("keyword-groups.yaml")


@dataclass(frozen=True)
class KeywordExpansion:
    original: str
    product_terms: tuple[str, ...]
    category: str | None = None
    category_terms: tuple[str, ...] = ()

    @property
    def search_terms(self) -> tuple[str, ...]:
        # Category terms explain and group the result. Searching a whole category
        # would create false positives (for example steel when looking for white sand).
        return self.product_terms


@dataclass(frozen=True)
class KeywordLearningResult:
    keyword: str
    category: str | None
    confidence: float
    status: str
    matched_signals: tuple[str, ...] = ()


def normalize_keyword(value: str) -> str:
    value = value.replace("\u0111", "d").replace("\u0110", "D")
    value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = f" {normalize_keyword(text)} "
    normalized_phrase = normalize_keyword(phrase)
    return bool(normalized_phrase) and f" {normalized_phrase} " in normalized_text


def _unique_terms(values: tuple[str, ...]) -> tuple[str, ...]:
    unique: dict[str, str] = {}
    for value in values:
        if value:
            unique.setdefault(normalize_keyword(value), value)
    return tuple(unique.values())


def expand_keyword(
    keyword: str, groups_path: Path = DEFAULT_KEYWORD_GROUPS
) -> KeywordExpansion:
    raw_keyword = keyword.strip()
    if not raw_keyword:
        raise ValueError("Tu khoa khong duoc de trong")
    original = normalize_keyword(raw_keyword)
    if not groups_path.exists():
        return KeywordExpansion(original=original, product_terms=(original,))

    raw = yaml.safe_load(groups_path.read_text(encoding="utf-8")) or {}
    for category in raw.get("categories") or []:
        category_name = str(category.get("name") or "").strip()
        category_aliases = tuple(
            str(item).strip() for item in category.get("aliases") or [] if str(item).strip()
        )
        category_terms = tuple(filter(None, (category_name, *category_aliases)))
        for product in category.get("products") or []:
            product_name = str(product.get("name") or "").strip()
            aliases = tuple(
                str(item).strip() for item in product.get("aliases") or [] if str(item).strip()
            )
            product_terms = _unique_terms((original, product_name, *aliases))
            if any(_contains_phrase(original, term) for term in (product_name, *aliases)):
                return KeywordExpansion(
                    original=original,
                    product_terms=product_terms,
                    category=category_name or None,
                    category_terms=category_terms,
                )
        if any(_contains_phrase(original, term) for term in category_terms):
            return KeywordExpansion(
                original=original,
                product_terms=(original,),
                category=category_name or None,
                category_terms=category_terms,
            )
    return KeywordExpansion(original=original, product_terms=(original,))


def matches_any_keyword(text: str, terms: tuple[str, ...] | list[str]) -> bool:
    text_tokens = set(re.findall(r"[\w]+", normalize_keyword(text)))
    for term in terms:
        term_tokens = set(re.findall(r"[\w]+", normalize_keyword(term)))
        if term_tokens and term_tokens.issubset(text_tokens):
            return True
    return False


def classify_keyword(
    keyword: str,
    aliases: tuple[str, ...] = (),
    description: str = "",
    groups_path: Path = DEFAULT_KEYWORD_GROUPS,
) -> KeywordLearningResult:
    if not groups_path.exists():
        return KeywordLearningResult(keyword, None, 0.0, "needs_review")
    raw = yaml.safe_load(groups_path.read_text(encoding="utf-8")) or {}
    context = " ".join((keyword, *aliases, description))
    candidates: list[tuple[int, str, tuple[str, ...]]] = []
    for category in raw.get("categories") or []:
        name = str(category.get("name") or "").strip()
        signals = [str(item).strip() for item in category.get("signals") or []]
        signals.extend(str(item).strip() for item in category.get("aliases") or [])
        for product in category.get("products") or []:
            signals.append(str(product.get("name") or "").strip())
            signals.extend(str(item).strip() for item in product.get("aliases") or [])
        matched = tuple(
            signal for signal in _unique_terms(tuple(signals)) if matches_any_keyword(context, [signal])
        )
        if matched and name:
            candidates.append((len(matched), name, matched))
    candidates.sort(reverse=True)
    if not candidates:
        return KeywordLearningResult(keyword, None, 0.0, "needs_review")
    best_score, best_name, best_signals = candidates[0]
    if len(candidates) > 1 and candidates[1][0] == best_score:
        return KeywordLearningResult(keyword, None, 0.5, "needs_review", best_signals)
    confidence = min(0.95, 0.55 + 0.15 * best_score)
    return KeywordLearningResult(keyword, best_name, confidence, "classified", best_signals)


def learn_keyword(
    keyword: str,
    aliases: tuple[str, ...] = (),
    description: str = "",
    category_name: str | None = None,
    groups_path: Path = DEFAULT_KEYWORD_GROUPS,
) -> KeywordLearningResult:
    raw = (
        yaml.safe_load(groups_path.read_text(encoding="utf-8")) or {}
        if groups_path.exists()
        else {"categories": []}
    )
    categories = raw.setdefault("categories", [])
    result = classify_keyword(keyword, aliases, description, groups_path)
    selected_name = category_name or result.category
    selected = next(
        (
            category
            for category in categories
            if normalize_keyword(str(category.get("name") or ""))
            == normalize_keyword(selected_name or "")
        ),
        None,
    )
    if selected is None:
        pending = raw.setdefault("pending_keywords", [])
        if not any(
            normalize_keyword(str(item.get("name") or "")) == normalize_keyword(keyword)
            for item in pending
        ):
            pending.append(
                {
                    "name": keyword,
                    "aliases": list(aliases),
                    "description": description or None,
                    "reason": "Chua du tin hieu de xac dinh nhom nganh",
                }
            )
        status = "needs_review"
    else:
        products = selected.setdefault("products", [])
        existing = next(
            (
                product
                for product in products
                if normalize_keyword(str(product.get("name") or "")) == normalize_keyword(keyword)
            ),
            None,
        )
        if existing is None:
            products.append({"name": keyword, "aliases": list(_unique_terms(aliases))})
        else:
            current = tuple(str(item) for item in existing.get("aliases") or [])
            existing["aliases"] = list(_unique_terms((*current, *aliases)))
        status = "updated"
    groups_path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return KeywordLearningResult(
        keyword=keyword,
        category=str(selected.get("name")) if selected else None,
        confidence=1.0 if category_name and selected else result.confidence,
        status=status,
        matched_signals=result.matched_signals,
    )
