import subprocess
import sys
from pathlib import Path

from qi_crawler import __version__
from qi_crawler.db import CURRENT_SCHEMA_REVISION

ROOT = Path(__file__).parent.parent


def test_approved_release_version_is_canonical_package_value() -> None:
    assert __version__ == "0.9.0"


def test_pyproject_derives_distribution_version_from_package() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'dynamic = ["version"]' in pyproject
    assert "[tool.setuptools.dynamic]" in pyproject
    assert 'version = {attr = "qi_crawler.__version__"}' in pyproject
    assert 'version = "0.7.1"' not in pyproject


def test_release_build_paths_use_canonical_version_and_manifest() -> None:
    build = (ROOT / "build_installer.ps1").read_text(encoding="utf-8")
    installer = (ROOT / "packaging" / "QI-Crawler.iss").read_text(encoding="utf-8")
    publish = (ROOT / "scripts" / "publish_windows_release.ps1").read_text(encoding="utf-8")

    assert "Get-CanonicalVersion" in build
    assert "/DAppVersion=$version" in build
    assert "release_manifest.json" in build
    assert "alembic_head" in build
    assert "Get-RuntimeSchemaRevision" in build
    assert "CURRENT_SCHEMA_REVISION" in build
    assert "runtimeSchema" in build
    assert "ExpectedAlembicHead" in build
    assert "portable_exe_sha256" in build
    assert "installer_sha256" in build
    assert "#error AppVersion" in installer
    assert '"0.7.1"' not in build
    assert '"0.7.1"' not in installer
    assert '"0.7.1"' not in publish
    assert "release_manifest.json" in publish
    assert "ExpectedAlembicHead" in publish
    assert "0013_add_candidate_review_events" not in publish


def test_gui_version_display_remains_package_driven() -> None:
    gui = (ROOT / "src" / "qi_crawler" / "gui.py").read_text(encoding="utf-8")
    assert "from . import __version__" in gui
    assert 'f"QI-CRAWLER v{__version__}"' in gui
    assert 'f"QI-Crawler v{__version__}"' in gui


def test_changelog_has_target_release_section() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## 0.9.0 - 2026-09-02" in changelog
    assert "## Unreleased\n\n## 0.9.0 - 2026-09-02" in changelog


def test_runtime_schema_matches_single_alembic_head() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    heads = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
    assert heads == [CURRENT_SCHEMA_REVISION]
