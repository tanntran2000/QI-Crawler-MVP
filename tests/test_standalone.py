from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

from qi_crawler.standalone import prepare_standalone_runtime, resource_path, resource_root


def test_required_packaging_resources_exist() -> None:
    assert resource_path("templates", "TBMT_template_v1.xlsx").is_file()
    assert resource_path("alembic", "versions").is_dir()
    assert resource_path("config.example.yaml").is_file()
    assert resource_path("keyword-groups.yaml").is_file()


def test_frozen_bundle_uses_its_executable_sidecar_runtime(
    tmp_path: Path, monkeypatch
) -> None:
    executable = tmp_path / "QI-Crawler.exe"
    executable.touch()
    runtime = tmp_path / "runtime"
    runtime.mkdir()

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "stale-runtime"), raising=False)

    assert resource_root() == runtime


def test_standalone_user_data_is_separate_and_not_overwritten(tmp_path: Path) -> None:
    original_cwd = Path.cwd()
    user_root = tmp_path / "QI-Crawler-User"
    try:
        paths = prepare_standalone_runtime(user_root, require_browser=False)
        assert paths.config_path.is_file()
        assert paths.database_dir.is_dir()
        assert paths.reports_dir.is_dir()
        assert paths.logs_dir.is_dir()
        assert paths.sessions_dir.is_dir()
        assert paths.documents_dir.is_dir()
        assert paths.documents_dir == paths.data_dir / "documents"
        assert paths.user_root != paths.resource_root

        config = yaml.safe_load(paths.config_path.read_text(encoding="utf-8"))
        assert str(paths.database_path.as_posix()) in config["storage"]["database_url"]
        assert config["storage"]["document_dir"] == str(paths.documents_dir)
        paths.config_path.write_text("custom: keep-me\n", encoding="utf-8")
        (paths.user_root / "keyword-groups.yaml").write_text(
            "custom: keep-me\n", encoding="utf-8"
        )

        prepare_standalone_runtime(user_root, require_browser=False)

        assert paths.config_path.read_text(encoding="utf-8") == "custom: keep-me\n"
        assert (
            paths.user_root / "keyword-groups.yaml"
        ).read_text(encoding="utf-8") == "custom: keep-me\n"
    finally:
        os.chdir(original_cwd)


def test_windows_build_files_define_onedir_gui_bundle() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = (root / "packaging" / "QI-Crawler.spec").read_text(encoding="utf-8")
    build_script = (root / "build_windows.ps1").read_text(encoding="utf-8")

    assert 'name="QI-Crawler"' in spec
    assert "console=False" in spec
    assert 'contents_directory="runtime"' in spec
    assert '(str(ROOT / "templates"), "templates")' in spec
    assert '(str(ROOT / "alembic"), "alembic")' in spec
    assert '(str(BROWSER_ROOT), "browsers")' in spec
    assert "PyInstaller --noconfirm --clean" in build_script
    assert "dist\\QI-Crawler\\QI-Crawler.exe" in build_script
