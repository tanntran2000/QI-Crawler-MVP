from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _init_git_repository(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", str(root)], check=True, capture_output=True)
    (root / "README.md").write_text("synthetic repository", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=QI Test",
            "-c",
            "user.email=qi@example.invalid",
            "commit",
            "-m",
            "baseline",
        ],
        check=True,
        capture_output=True,
    )


def _powershell_command() -> list[str]:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if executable is None:
        raise RuntimeError("PowerShell runtime is required: install pwsh or powershell.")
    command = [executable, "-NoProfile"]
    if sys.platform == "win32" and Path(executable).name.lower() == "powershell.exe":
        command.extend(["-ExecutionPolicy", "Bypass"])
    return command


def _run_cleanup(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            *_powershell_command(),
            "-File",
            str(ROOT / "scripts" / "clean_dev.ps1"),
            "-Root",
            str(root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_cleanup_script_uses_explicit_safe_targets() -> None:
    script = (ROOT / "scripts" / "clean_dev.ps1").read_text(encoding="utf-8")
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    targets = script.split("$allowedTargets = @(", 1)[1].split(")", 1)[0]

    assert "SupportsShouldProcess" in script
    assert "Get-ChildItem" not in script
    assert "takeown" not in script.lower()
    assert "icacls" not in script.lower()
    assert '".tmp"' in script
    assert "release_staging" not in targets
    assert "rev-parse --show-toplevel" in script
    assert "/.tmp/" in ignored
    assert "release_staging/" in ignored


def test_cleanup_only_removes_allowlisted_generated_directories(tmp_path: Path) -> None:
    _init_git_repository(tmp_path)
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".tmp").mkdir()
    evidence = tmp_path / "release_staging" / "evidence"
    published = tmp_path / "release_staging" / "published" / "candidate-v0.10.1"
    evidence.mkdir(parents=True)
    published.mkdir(parents=True)
    (evidence / "keep.txt").write_text("evidence", encoding="utf-8")
    (published / "keep.txt").write_text("immutable archive", encoding="utf-8")
    (tmp_path / "unknown.txt").write_text("keep", encoding="utf-8")
    (tmp_path / "evaluate_qi_crawler.py").write_text("keep", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "alembic" / "versions").mkdir(parents=True)

    result = _run_cleanup(tmp_path)

    assert result.returncode == 0
    assert not (tmp_path / ".pytest_cache").exists()
    assert not (tmp_path / ".tmp").exists()
    assert (tmp_path / "unknown.txt").exists()
    assert (tmp_path / "evaluate_qi_crawler.py").exists()
    assert (tmp_path / "src").exists()
    assert (tmp_path / "tests").exists()
    assert (tmp_path / "alembic" / "versions").exists()
    assert (evidence / "keep.txt").read_text(encoding="utf-8") == "evidence"
    assert (published / "keep.txt").read_text(encoding="utf-8") == "immutable archive"


def test_cleanup_skips_unsupported_target_without_deleting_it(tmp_path: Path) -> None:
    _init_git_repository(tmp_path)
    target = tmp_path / ".tmp"
    target.write_text("not a generated directory", encoding="utf-8")

    result = _run_cleanup(tmp_path)

    assert result.returncode == 0
    assert target.exists()
    assert "SKIP unsupported cleanup target" in result.stdout


def test_cleanup_requires_exact_git_root_and_rejects_non_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_git_repository(repo)
    nested = repo / "nested"
    nested.mkdir()
    (repo / ".tmp").mkdir()
    protected = repo / ".tmp" / "keep.txt"
    protected.write_text("keep", encoding="utf-8")

    nested_result = _run_cleanup(nested)
    assert nested_result.returncode != 0
    assert protected.read_text(encoding="utf-8") == "keep"

    operational = tmp_path / "QI-Crawler"
    operational.mkdir()
    (operational / ".tmp").mkdir()
    operational_sentinel = operational / ".tmp" / "keep.txt"
    operational_sentinel.write_text("operational data", encoding="utf-8")
    operational_result = _run_cleanup(operational)
    assert operational_result.returncode != 0
    assert operational_sentinel.read_text(encoding="utf-8") == "operational data"


def test_verify_script_checks_protected_deletions() -> None:
    script = (ROOT / "scripts" / "verify_dev.ps1").read_text(encoding="utf-8")

    assert "python -m pytest" in script
    assert "ruff check ." in script
    assert "git diff --check" in script
    assert "git diff --name-status" in script
    assert "src/|tests/|alembic/|packaging/|scripts/" in script
