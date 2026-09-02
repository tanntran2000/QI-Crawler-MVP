import ast
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from qi_crawler import __version__
from qi_crawler.db import CURRENT_SCHEMA_REVISION

ROOT = Path(__file__).parent.parent
INSTALLER = ROOT / "packaging" / "QI-Crawler.iss"
BUILD_SCRIPT = ROOT / "build_installer.ps1"
BUILD_WINDOWS = ROOT / "build_windows.ps1"
PUBLISH_SCRIPT = ROOT / "scripts" / "publish_windows_release.ps1"
VERSION = __version__
EXPECTED_SCHEMA_HEAD = CURRENT_SCHEMA_REVISION

def _load_spec_helpers() -> dict[str, object]:
    """Load only pure helper functions from the PyInstaller spec."""
    tree = ast.parse((ROOT / "packaging" / "QI-Crawler.spec").read_text(encoding="utf-8"))
    helper_nodes = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in {"_is_within", "filter_foreign_unversioned_icu_binaries"}
    ]
    namespace: dict[str, object] = {"Path": Path}
    exec(  # noqa: S102
        compile(ast.Module(body=helper_nodes, type_ignores=[]), "QI-Crawler.spec", "exec"),
        namespace,
    )
    return namespace


def test_spec_filters_foreign_unversioned_icu_by_source_ownership(tmp_path: Path) -> None:
    """Foreign ICU binaries must not shadow PySide6-owned runtime dependencies."""
    script = (ROOT / "packaging" / "QI-Crawler.spec").read_text(encoding="utf-8")
    for dll_name in ("icuuc.dll", "icuin.dll", "icudt.dll"):
        assert dll_name in script.lower()
    assert "find_spec(\"pyside6\")" in script.lower()
    assert "c:\\users\\admin" not in script.lower()
    assert "codex-runtimes" not in script.lower()
    assert "poppler" not in script.lower()

    helpers = _load_spec_helpers()
    filter_binaries = helpers["filter_foreign_unversioned_icu_binaries"]
    pyside_root = tmp_path / "site-packages" / "PySide6"
    foreign_root = tmp_path / "native" / "poppler"
    binaries = [
        ("icuuc.dll", str(foreign_root / "icuuc.dll"), "BINARY"),
        ("icuin.dll", str(foreign_root / "icuin.dll"), "BINARY"),
        ("icudt78.dll", str(foreign_root / "icudt78.dll"), "BINARY"),
        ("Qt6Core.dll", str(foreign_root / "Qt6Core.dll"), "BINARY"),
        ("icuuc.dll", str(pyside_root / "icuuc.dll"), "BINARY"),
    ]
    filtered = filter_binaries(binaries, pyside_root)  # type: ignore[operator]
    assert ("Qt6Core.dll", str(foreign_root / "Qt6Core.dll"), "BINARY") in filtered
    assert ("icuuc.dll", str(pyside_root / "icuuc.dll"), "BINARY") in filtered
    assert all(
        Path(item[0]).name.lower() not in {"icuuc.dll", "icuin.dll", "icudt78.dll"}
        or Path(item[1]).is_relative_to(pyside_root)
        for item in filtered
    )


def test_frozen_smoke_gate_waits_for_process_and_fails_closed() -> None:
    """The candidate must be created only after a real child-process result."""
    script = BUILD_SCRIPT.read_text(encoding="utf-8")
    smoke_start = script.index("$smokeProcess = Start-Process")
    candidate_start = script.index(
        "New-Item -ItemType Directory -Path (Join-Path $candidateRoot", smoke_start
    )
    gate = script[smoke_start:candidate_start]
    assert "Start-Process" in gate
    assert "-PassThru" in gate
    assert "WaitForExit(120000)" in gate
    assert ".ExitCode" in gate
    assert "Kill()" in gate
    assert "throw" in gate
    assert "QI_CRAWLER_DATA_DIR" in gate


def test_installer_is_per_user_and_preserves_bid_data() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert "#ifndef AppVersion" in script
    assert "#error AppVersion" in script
    assert "OutputBaseFilename=QI-Crawler-Setup-v{#AppVersion}" in script
    assert "DefaultDirName={localappdata}\\Programs\\QI-Crawler" in script
    assert "PrivilegesRequired=lowest" in script
    assert "Source: \"..\\dist\\QI-Crawler\\*\"" in script
    assert "{autoprograms}\\QI-Crawler" in script
    assert "{autodesktop}\\QI-Crawler" in script
    assert "[UninstallDelete]" not in script
    assert "{userappdata}" not in script
    assert "{localappdata}\\QI-Crawler" not in script


def test_installer_build_is_reproducible_from_safe_onedir_bundle() -> None:
    script = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert "build_windows.ps1" in script
    assert "QI-Crawler.iss" in script
    assert "ISCC.exe" in script
    assert "QI_CRAWLER_ISCC" in script
    assert "Inno Setup 7" in script
    assert "$iscc = @($isccCandidates)[0]" in script
    assert "QI-Crawler-Setup-v$version.exe" in script
    assert "dist\\QI-Crawler\\QI-Crawler.exe" in script
    assert "[switch]$Publish" in script
    assert "--smoke-test-documents" in script
    assert "release_staging\\candidate" in script


def test_windows_build_cleans_only_allowlisted_generated_bundle() -> None:
    script = BUILD_WINDOWS.read_text(encoding="utf-8")

    assert "dist\\QI-Crawler" in script
    assert '"build", "dist\\QI-Crawler"' in script
    assert "Remove-Item" in script
    assert "Test-TrackedPath" in script
    assert "Crawler tool" not in script


def test_publish_is_explicit_and_has_safe_contract() -> None:
    script = PUBLISH_SCRIPT.read_text(encoding="utf-8")

    assert "[switch]$Publish" in script
    assert "if (-not $Publish)" in script
    assert "Current" in script
    assert "Previous" in script
    assert "BUILD_INFO.txt" in script
    assert "release_manifest.json" in script
    assert "Get-FileHash" in script
    assert "branch --show-current" in script
    assert "status --porcelain" in script


def test_publish_script_does_not_touch_root_without_publish(tmp_path: Path) -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell is required for the Windows publish smoke test")

    publish_root = tmp_path / "Crawler tool"
    publish_root.mkdir()
    sentinel = publish_root / "Current" / "sentinel.txt"
    sentinel.parent.mkdir()
    sentinel.write_text("keep", encoding="utf-8")
    candidate = tmp_path / "candidate"
    (candidate / "QI-Crawler").mkdir(parents=True)
    (candidate / "QI-Crawler" / "QI-Crawler.exe").write_bytes(b"exe")
    (candidate / f"QI-Crawler-Setup-v{VERSION}.exe").write_bytes(b"installer")

    args = [
        shell,
        "-NoProfile",
        "-File",
        str(PUBLISH_SCRIPT),
        "-RepoRoot",
        str(ROOT),
        "-PublishRoot",
        str(publish_root),
        "-CandidateRoot",
        str(candidate),
        "-Version",
        VERSION,
    ]
    if sys.platform == "win32" and Path(shell).name.lower() == "powershell.exe":
        args[1:1] = ["-ExecutionPolicy", "Bypass"]
    result = subprocess.run(args, capture_output=True, text=True, check=False)

    assert result.returncode == 0
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not (publish_root / "Current" / "QI-Crawler.exe").exists()


def test_publish_rotates_previous_and_rejects_incomplete_candidate(tmp_path: Path) -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell is required for the Windows publish behavior test")

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    (repo / "README.md").write_text("clean", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
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

    publish_root = tmp_path / "Crawler tool"

    def make_candidate(
        name: str, payload: bytes, schema_head: str = EXPECTED_SCHEMA_HEAD
    ) -> Path:
        candidate = tmp_path / name
        bundle = candidate / "QI-Crawler"
        bundle.mkdir(parents=True)
        (bundle / "QI-Crawler.exe").write_bytes(payload)
        installer = candidate / f"QI-Crawler-Setup-v{VERSION}.exe"
        installer.write_bytes(payload + b"-installer")
        exe_hash = hashlib.sha256(payload).hexdigest().upper()
        installer_hash = hashlib.sha256(installer.read_bytes()).hexdigest().upper()
        (candidate / "BUILD_INFO.txt").write_text(
            "\n".join(
                [
                    "product=QI-Crawler",
                    f"version={VERSION}",
                    "commit_sha="
                    + subprocess.check_output(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
                    ).strip(),
                    "source_branch=main",
                    "build_timestamp_utc=2026-08-23T00:00:00Z",
                    f"alembic_head={schema_head}",
                    f"portable_exe_sha256={exe_hash}",
                    f"installer_sha256={installer_hash}",
                ]
            ),
            encoding="utf-8",
        )
        (candidate / "release_manifest.json").write_text(
            json.dumps(
                {
                    "product": "QI-Crawler",
                    "version": VERSION,
                    "commit_sha": subprocess.check_output(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
                    ).strip(),
                    "build_timestamp_utc": "2026-08-23T00:00:00Z",
                    "alembic_head": schema_head,
                    "release_channel": "team_bid_verified",
                    "portable_exe_sha256": exe_hash,
                    "installer_sha256": installer_hash,
                }
            ),
            encoding="utf-8",
        )
        return candidate

    def run_publish(
        candidate: Path, expected_head: str | None = EXPECTED_SCHEMA_HEAD
    ) -> subprocess.CompletedProcess[str]:
        args = [
            shell,
            "-NoProfile",
            "-File",
            str(PUBLISH_SCRIPT),
            "-Publish",
            "-RepoRoot",
            str(repo),
            "-PublishRoot",
            str(publish_root),
            "-CandidateRoot",
            str(candidate),
            "-Version",
            VERSION,
        ]
        if expected_head is not None:
            args.extend(["-ExpectedAlembicHead", expected_head])
        if sys.platform == "win32" and Path(shell).name.lower() == "powershell.exe":
            args[1:1] = ["-ExecutionPolicy", "Bypass"]
        return subprocess.run(args, capture_output=True, text=True, check=False)

    first = run_publish(make_candidate("candidate-one", b"one"))
    assert first.returncode == 0, first.stderr
    current_exe = publish_root / "Current" / "QI-Crawler" / "QI-Crawler.exe"
    assert current_exe.read_bytes() == b"one"

    second = run_publish(make_candidate("candidate-two", b"two"))
    assert second.returncode == 0, second.stderr
    assert current_exe.read_bytes() == b"two"
    assert (
        publish_root / "Previous" / "QI-Crawler" / "QI-Crawler.exe"
    ).read_bytes() == b"one"
    info = (publish_root / "Current" / "BUILD_INFO.txt").read_text(encoding="utf-8")
    assert "product=QI-Crawler" in info
    assert f"version={VERSION}" in info
    assert (
        "portable_exe_sha256="
        + hashlib.sha256(b"two").hexdigest().upper()
    ) in info
    assert (
        "installer_sha256="
        + hashlib.sha256(b"two-installer").hexdigest().upper()
    ) in info
    manifest = json.loads(
        (publish_root / "Current" / "release_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["product"] == "QI-Crawler"
    assert manifest["version"] == VERSION
    assert manifest["alembic_head"] == EXPECTED_SCHEMA_HEAD
    assert manifest["release_channel"] == "team_bid_verified"

    incomplete = tmp_path / "candidate-incomplete"
    (incomplete / "QI-Crawler").mkdir(parents=True)
    (incomplete / f"QI-Crawler-Setup-v{VERSION}.exe").write_bytes(b"bad")
    failed = run_publish(incomplete)
    assert failed.returncode != 0
    assert current_exe.read_bytes() == b"two"

    wrong_head = run_publish(
        make_candidate("candidate-wrong-head", b"wrong", schema_head="wrong-head")
    )
    assert wrong_head.returncode != 0
    assert current_exe.read_bytes() == b"two"

    build_info_only_mismatch = make_candidate(
        "candidate-build-info-only-mismatch", b"build-info-mismatch"
    )
    build_info_path = build_info_only_mismatch / "BUILD_INFO.txt"
    build_info_path.write_text(
        build_info_path.read_text(encoding="utf-8").replace(
            f"alembic_head={EXPECTED_SCHEMA_HEAD}",
            "alembic_head=wrong-build-info-head",
        ),
        encoding="utf-8",
    )
    build_info_only_failed = run_publish(build_info_only_mismatch)
    assert build_info_only_failed.returncode != 0
    assert json.loads(
        (build_info_only_mismatch / "release_manifest.json").read_text(encoding="utf-8")
    )["alembic_head"] == EXPECTED_SCHEMA_HEAD
    assert (
        "alembic_head=wrong-build-info-head"
        in build_info_path.read_text(encoding="utf-8")
    )
    assert current_exe.read_bytes() == b"two"

    missing_expected_head = run_publish(
        make_candidate("candidate-missing-expected-head", b"missing"), expected_head=None
    )
    assert missing_expected_head.returncode != 0
    assert current_exe.read_bytes() == b"two"
