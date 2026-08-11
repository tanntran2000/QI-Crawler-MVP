import asyncio
import re
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from qi_crawler import __version__, cli
from qi_crawler.cli import app
from qi_crawler.importer import ImportSummary

runner = CliRunner()
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _plain_terminal_text(value: str) -> str:
    """Remove Rich terminal formatting before asserting user-visible text."""
    return ANSI_ESCAPE.sub("", value)


def test_short_help_option_shows_commands_and_examples() -> None:
    result = runner.invoke(app, ["-help"])
    output = _plain_terminal_text(result.output)

    assert result.exit_code == 0
    assert "QI-Crawler" in output
    assert "tim-goi" in output
    assert "dang-nhap" in output
    assert "tim-tren-web" in output
    assert "nhap-ton-kho" in output
    assert "nhap-boq" in output
    assert "xuat-tbmt" in output
    assert "crawl" not in output
    assert "xep-hang" not in output
    assert "them-nguon" not in output
    assert "danh-gia" not in output
    assert "init-db" not in output
    assert "import-inventory" not in output
    assert "CHANGELOG.md" in output
    assert "HUONG_DAN_SU_DUNG.md" in output
    assert "QI-Crawler -adv" in output


def test_help_command_shows_commands_and_examples() -> None:
    result = runner.invoke(app, ["help"])

    assert result.exit_code == 0
    assert "xuat-tbmt" in result.output
    assert "TEN-LENH" in result.output
    assert "-help" in result.output


def test_advanced_help_lists_hidden_technical_commands() -> None:
    result = runner.invoke(app, ["-adv"])

    assert result.exit_code == 0
    assert "LENH NANG CAO" in result.output
    assert "init-db" in result.output
    assert "warehouse-status" in result.output
    assert "collect-contracts-finder" in result.output
    assert "them-nguon" in result.output
    assert "xep-hang" in result.output
    assert "CHANGELOG" not in result.output
    assert "Co gi moi" not in result.output


def test_release_version_is_synchronized_across_user_documents() -> None:
    root = Path(__file__).resolve().parents[1]

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    guide = (root / "HUONG_DAN_SU_DUNG.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert f"## {__version__}" in changelog
    assert f"Co gi moi trong {__version__}" in guide
    assert f"Co gi moi trong {__version__}" in readme


def test_import_file_creates_and_closes_service_in_one_event_loop(
    monkeypatch, tmp_path: Path
) -> None:
    input_file = tmp_path / "notices.csv"
    input_file.write_text("title\nExample\n", encoding="utf-8")
    events: list[str] = []

    class FakeService:
        def __init__(self, _config) -> None:
            self.loop = asyncio.get_running_loop()
            events.append("created")

        async def close(self) -> None:
            assert asyncio.get_running_loop() is self.loop
            events.append("closed")

    def fake_import(service: FakeService, path: Path) -> ImportSummary:
        assert service.loop is asyncio.get_running_loop()
        assert path == input_file
        events.append("imported")
        return ImportSummary(rows_found=1, inserted=1)

    monkeypatch.setattr(cli, "_config", lambda _path: SimpleNamespace())
    monkeypatch.setattr(cli, "CrawlerService", FakeService)
    monkeypatch.setattr(cli, "import_data_file", fake_import)

    result = runner.invoke(app, ["import-file", str(input_file)])

    assert result.exit_code == 0
    assert events == ["created", "imported", "closed"]
