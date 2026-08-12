import asyncio
import re
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from qi_crawler import __version__, cli
from qi_crawler.cli import app
from qi_crawler.config import AppConfig
from qi_crawler.importer import ImportSummary
from qi_crawler.models import Notice

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
    assert 'QI-Crawler crawl "URL_GOI_THAU"' in output
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
    assert "db-upgrade" in result.output
    assert "warehouse-status" in result.output
    assert "collect-contracts-finder" not in result.output
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


def test_tim_goi_does_not_call_network(monkeypatch, tmp_path: Path) -> None:
    config = AppConfig.model_validate(
        {
            "sources": {
                "coteccons": {
                    "enabled": True,
                    "priority": 1,
                    "domain": "ebidding.coteccons.vn",
                    "adapter": "coteccons",
                }
            }
        }
    )
    config.storage.database_url = f"sqlite:///{tmp_path / 'local-search.db'}"
    database = cli.Database(config.storage.database_url)
    database.create_all()
    with database.session() as session:
        session.add(
            Notice(
                source_url="https://ebidding.coteccons.vn/Index/ChiTiet/2607301",
                url_hash="a" * 64,
                source_name="coteccons",
                source_notice_id="2607301",
                title="Goi thau thi cong chong tham",
            )
        )

    class NetworkMustNotRun:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("tim-goi must not create a network crawler")

    monkeypatch.setattr(cli, "_config", lambda _path: config)
    monkeypatch.setattr(cli, "CrawlerService", NetworkMustNotRun)
    groups_path = Path("keyword-groups.yaml")
    before = groups_path.read_bytes()
    monkeypatch.setattr(
        cli,
        "expand_keyword",
        lambda keyword: cli.KeywordExpansion(keyword, (keyword,)),
    )
    monkeypatch.setattr(cli, "learn_keyword", lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("search must not learn a keyword")
    ))

    result = runner.invoke(app, ["tim-goi", "-k", "chong tham"])

    assert result.exit_code == 0
    assert "khong ket noi website" in _plain_terminal_text(result.output).lower()
    assert "2607301" in result.output
    assert groups_path.read_bytes() == before


def test_tim_tren_web_does_not_modify_keyword_pool(monkeypatch) -> None:
    groups_path = Path("keyword-groups.yaml")
    before = groups_path.read_bytes()

    class FakeService:
        async def close(self) -> None:
            return None

    async def collect(*_args, **kwargs):
        assert kwargs["keyword"] == ("chong tham",)
        return SimpleNamespace(scanned=1, matched=1, inserted=1, updated=0)

    monkeypatch.setattr(cli, "_config", lambda _path: SimpleNamespace())
    monkeypatch.setattr(cli, "load_source", lambda _name: SimpleNamespace())
    monkeypatch.setattr(cli, "CrawlerService", lambda _config: FakeService())
    monkeypatch.setattr(cli, "collect_authenticated_source", collect)
    monkeypatch.setattr(
        cli,
        "expand_keyword",
        lambda keyword: cli.KeywordExpansion(keyword, (keyword,)),
    )
    monkeypatch.setattr(cli, "learn_keyword", lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("search must not learn a keyword")
    ))

    result = runner.invoke(app, ["tim-tren-web", "--ten", "egp", "-k", "chong tham"])

    assert result.exit_code == 0
    assert "Da xem 1 muc" in result.output
    assert groups_path.read_bytes() == before


def test_first_run_database_message_is_short_and_actionable(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.undo()
    config_path = tmp_path / "first-run.yaml"
    config_path.write_text(
        f"storage:\n  database_url: sqlite:///{tmp_path / 'first-run.db'}\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["bat-dau", "--config", str(config_path)])

    assert result.exit_code != 0
    assert "Hay chay QI-Crawler db-upgrade" in result.output
    assert "Traceback" not in result.output
