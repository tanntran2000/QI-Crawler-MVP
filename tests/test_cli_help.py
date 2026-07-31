from typer.testing import CliRunner

from qi_crawler.cli import app

runner = CliRunner()


def test_short_help_option_shows_commands_and_examples() -> None:
    result = runner.invoke(app, ["-help"])

    assert result.exit_code == 0
    assert "tim-goi" in result.output
    assert 'QI-Crawler tim-goi --tu-khoa "xi măng"' in result.output


def test_help_command_shows_commands_and_examples() -> None:
    result = runner.invoke(app, ["help"])

    assert result.exit_code == 0
    assert "xuat-bao-cao" in result.output
    assert "QI-Crawler TEN-LENH -help" in result.output
