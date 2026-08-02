from pathlib import Path

from typer.testing import CliRunner

from qi_crawler import __version__
from qi_crawler.cli import app

runner = CliRunner()


def test_short_help_option_shows_commands_and_examples() -> None:
    result = runner.invoke(app, ["-help"])

    assert result.exit_code == 0
    assert "QI-Crawler" in result.output
    assert "tim-goi" in result.output
    assert "nhap-ton-kho" in result.output
    assert "nhap-boq" in result.output
    assert "xep-hang" in result.output
    assert "danh-gia" not in result.output
    assert "init-db" not in result.output
    assert "import-inventory" not in result.output
    assert f"PHIEN BAN {__version__}" in result.output
    assert "CHANGELOG.md" in result.output
    assert "HUONG_DAN_SU_DUNG.md" in result.output
    assert "Web UI" in result.output


def test_help_command_shows_commands_and_examples() -> None:
    result = runner.invoke(app, ["help"])

    assert result.exit_code == 0
    assert "xuat-bao-cao" in result.output
    assert "TEN-LENH" in result.output
    assert "-help" in result.output


def test_advanced_help_lists_hidden_technical_commands() -> None:
    result = runner.invoke(app, ["-adv"])

    assert result.exit_code == 0
    assert "LENH NANG CAO" in result.output
    assert "init-db" in result.output
    assert "warehouse-status" in result.output
    assert "collect-contracts-finder" in result.output
    assert f"PHIEN BAN {__version__}" in result.output
    assert "AND/OR/NOT" in result.output
    assert "formula injection" in result.output
    assert "Roadmap UI" in result.output


def test_release_version_is_synchronized_across_user_documents() -> None:
    root = Path(__file__).resolve().parents[1]

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    guide = (root / "HUONG_DAN_SU_DUNG.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert f"## {__version__}" in changelog
    assert f"Co gi moi trong {__version__}" in guide
    assert f"Co gi moi trong {__version__}" in readme
