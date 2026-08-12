from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qi_crawler import cli
from qi_crawler.cli import app
from qi_crawler.compliance import AccessDenied

runner = CliRunner()
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
LIST_URL = "https://ebidding.coteccons.vn/Index"


def _plain(value: str) -> str:
    return ANSI_ESCAPE.sub("", value)


def test_menu_starts_and_exits() -> None:
    result = runner.invoke(app, ["menu"], input="0\n")
    output = _plain(result.output)

    assert result.exit_code == 0
    assert "QI-CRAWLER" in output
    assert "1. Quet danh sach goi thau" in output
    assert "6. Mo thu muc ket qua" in output
    assert "Da thoat QI-Crawler" in output


def test_invalid_menu_choice_is_handled() -> None:
    result = runner.invoke(app, ["menu"], input="9\n0\n")

    assert result.exit_code == 0
    assert "Lua chon khong hop le" in _plain(result.output)


def test_menu_scan_uses_default_three_pages_and_empty_keyword(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_scan(**kwargs) -> None:
        calls.append(kwargs)

    class CrawlerMustNotBeCreatedByMenu:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("menu must call the existing scan command")

    monkeypatch.setattr(cli, "scan", fake_scan)
    monkeypatch.setattr(cli, "CrawlerService", CrawlerMustNotBeCreatedByMenu)

    result = runner.invoke(app, ["menu"], input=f"1\n{LIST_URL}\n\n\n0\n")

    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0]["list_url"] == LIST_URL
    assert calls[0]["max_pages"] == 3
    assert calls[0]["tu_khoa"] is None
    assert calls[0]["resume"] is False


def test_menu_scan_accepts_comma_separated_keywords(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(cli, "scan", lambda **kwargs: calls.append(kwargs))

    result = runner.invoke(
        app,
        ["menu"],
        input=f"1\n{LIST_URL}\n5\nchong tham,son\n0\n",
    )

    assert result.exit_code == 0
    assert calls[0]["max_pages"] == 5
    assert calls[0]["tu_khoa"] == "chong tham,son"


def test_menu_search_reuses_tim_goi_without_learning(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(cli, "tim_goi", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(
        cli,
        "learn_keyword",
        lambda *_args, **_kwargs: pytest.fail("menu search must not learn keywords"),
    )

    result = runner.invoke(app, ["menu"], input="2\nchong tham\n0\n")

    assert result.exit_code == 0
    assert calls == [
        {
            "tu_khoa": "chong tham",
            "tu_ngay": None,
            "so_luong": 20,
            "config": None,
        }
    ]


def test_menu_shows_friendly_human_required_message(monkeypatch) -> None:
    def blocked_scan(**_kwargs) -> None:
        raise AccessDenied("HTTP 403")

    monkeypatch.setattr(cli, "scan", blocked_scan)
    result = runner.invoke(app, ["menu"], input=f"1\n{LIST_URL}\n\n\n0\n")
    output = _plain(result.output)

    assert result.exit_code == 0
    assert "HUMAN_REQUIRED" in output
    assert "Can nguoi dung xu ly" in output
    assert "CAPTCHA" in output
    assert "Du lieu khong bi ghi sai" in output
    assert "co the chay lai" in output


def test_menu_can_open_exported_excel_safely(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "TBMT.xlsx"
    opened: list[Path] = []
    monkeypatch.setattr(cli, "xuat_tbmt", lambda **_kwargs: output)
    monkeypatch.setattr(cli, "_open_windows_path", lambda path: opened.append(path) or True)

    result = runner.invoke(app, ["menu"], input="3\ny\n0\n")

    assert result.exit_code == 0
    assert "Mo file Excel ngay?" in _plain(result.output)
    assert opened == [output]


def test_windows_launcher_exists_and_runs_menu() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = root / "QI-Crawler.bat"

    assert launcher.is_file()
    content = launcher.read_text(encoding="utf-8")
    assert "%~dp0" in content
    assert ".venv\\Scripts\\activate.bat" in content
    assert ".venv\\Scripts\\QI-Crawler.exe" in content
    assert "QI-Crawler menu" in content
    assert "pause" in content.lower()


@pytest.mark.parametrize(
    "command",
    ["scan", "tim-goi", "xuat-tbmt", "crawl", "dang-nhap"],
)
def test_existing_bid_team_commands_still_have_help(command: str) -> None:
    result = runner.invoke(app, [command, "-help"])

    assert result.exit_code == 0
    assert command in _plain(result.output)
