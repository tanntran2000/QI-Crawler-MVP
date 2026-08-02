from typer.testing import CliRunner

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
