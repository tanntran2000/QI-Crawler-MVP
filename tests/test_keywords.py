from pathlib import Path

from qi_crawler.keywords import (
    classify_keyword,
    expand_keyword,
    learn_keyword,
    matches_any_keyword,
    normalize_keyword,
)


def test_white_sand_expands_to_english_and_construction_category() -> None:
    result = expand_keyword("cát trắng")

    assert "white sand" in result.product_terms
    assert result.category == "Vật liệu xây dựng"
    assert "VLXD" in result.category_terms


def test_5g_module_accepts_common_spelling_variants() -> None:
    result = expand_keyword("Mô đun 5G")

    assert "module 5G" in result.product_terms
    assert "modul 5G" in result.product_terms
    assert result.category == "Công nghệ thông tin"


def test_matching_is_accent_insensitive_and_accepts_any_expanded_term() -> None:
    assert normalize_keyword("Xi măng") == "xi mang"
    assert matches_any_keyword("Supply of WHITE SAND", ("cát trắng", "white sand"))
    assert matches_any_keyword("Mua sắm thiết bị CNTT", ("Công nghệ thông tin", "CNTT"))


def test_new_keyword_is_classified_from_industry_signals() -> None:
    result = classify_keyword("cáp mạng ngoài trời")

    assert result.category == "Công nghệ thông tin"
    assert result.confidence >= 0.6


def test_learning_updates_category_file(tmp_path: Path) -> None:
    groups = tmp_path / "groups.yaml"
    groups.write_text(
        """
categories:
  - name: Công nghệ thông tin
    aliases: [CNTT]
    signals: [mạng, network]
    products: []
""".strip(),
        encoding="utf-8",
    )

    result = learn_keyword(
        "cáp mạng ngoài trời",
        aliases=("outdoor network cable",),
        groups_path=groups,
    )
    expansion = expand_keyword("cáp mạng ngoài trời", groups_path=groups)

    assert result.status == "updated"
    assert result.category == "Công nghệ thông tin"
    assert "outdoor network cable" in expansion.product_terms


def test_unknown_keyword_goes_to_review_queue(tmp_path: Path) -> None:
    groups = tmp_path / "groups.yaml"
    groups.write_text("categories: []\n", encoding="utf-8")

    result = learn_keyword("sản phẩm hoàn toàn mới", groups_path=groups)

    assert result.status == "needs_review"
    assert "pending_keywords" in groups.read_text(encoding="utf-8")
