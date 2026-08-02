from pathlib import Path

from qi_crawler.keywords import (
    classify_keyword,
    expand_keyword,
    learn_keyword,
    matches_any_keyword,
    normalize_keyword,
)


def test_white_sand_expands_to_english_and_construction_category() -> None:
    result = expand_keyword("c\u00e1t")

    assert "sand" in result.product_terms
    assert "white sand" in result.product_terms
    assert result.category == "Construction Materials"
    assert "VLXD" in result.category_terms


def test_5g_module_accepts_common_spelling_variants() -> None:
    result = expand_keyword("Mo dun 5G")

    assert "module 5G" in result.product_terms
    assert "modul 5G" in result.product_terms
    assert result.category == "Information Technology"


def test_matching_is_accent_insensitive_and_accepts_any_expanded_term() -> None:
    assert normalize_keyword("Xi m\u0103ng") == "xi mang"
    assert matches_any_keyword("Supply of WHITE SAND", ("cat trang", "white sand"))
    assert matches_any_keyword("Mua sam thiet bi CNTT", ("Cong nghe thong tin", "CNTT"))
    assert matches_any_keyword("Supply network switches and routers", ("switch",))


def test_windows_vietnamese_search_terms_keep_meaning() -> None:
    assert normalize_keyword("L\u00e3nh Binh Th\u0103ng") == "lanh binh thang"
    assert normalize_keyword("\u0110\u1ecba \u0111i\u1ec3m") == "dia diem"
    result = expand_keyword("C\u00e1p quang")
    assert "fiber optic cable" in result.product_terms
    assert result.category == "Information Technology"


def test_new_keyword_is_classified_from_industry_signals() -> None:
    result = classify_keyword("cap mang ngoai troi")

    assert result.category == "Information Technology"
    assert result.confidence >= 0.6


def test_learning_updates_category_file(tmp_path: Path) -> None:
    groups = tmp_path / "groups.yaml"
    groups.write_text(
        """
categories:
  - name: Cong nghe thong tin
    aliases: [CNTT]
    signals: [mang, network]
    products: []
""".strip(),
        encoding="utf-8",
    )

    result = learn_keyword(
        "cap mang ngoai troi",
        aliases=("outdoor network cable",),
        groups_path=groups,
    )
    expansion = expand_keyword("cap mang ngoai troi", groups_path=groups)

    assert result.status == "updated"
    assert result.category == "Cong nghe thong tin"
    assert "outdoor network cable" in expansion.product_terms


def test_unknown_keyword_goes_to_review_queue(tmp_path: Path) -> None:
    groups = tmp_path / "groups.yaml"
    groups.write_text("categories: []\n", encoding="utf-8")

    result = learn_keyword("san pham hoan toan moi", groups_path=groups)

    assert result.status == "needs_review"
    assert "pending_keywords" in groups.read_text(encoding="utf-8")
