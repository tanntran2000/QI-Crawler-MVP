import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from qi_crawler import __version__

ROOT = Path(__file__).parent.parent
INSTALLER = ROOT / "packaging" / "QI-Crawler.iss"
BUILD_SCRIPT = ROOT / "build_installer.ps1"
BUILD_WINDOWS = ROOT / "build_windows.ps1"
PUBLISH_SCRIPT = ROOT / "scripts" / "publish_windows_release.ps1"
VERSION = __version__


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

    def make_candidate(name: str, payload: bytes) -> Path:
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
                    "alembic_head=0014_add_source_type_review_events",
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
                    "alembic_head": "0014_add_source_type_review_events",
                    "release_channel": "team_bid_verified",
                    "portable_exe_sha256": exe_hash,
                    "installer_sha256": installer_hash,
                }
            ),
            encoding="utf-8",
        )
        return candidate

    def run_publish(candidate: Path) -> subprocess.CompletedProcess[str]:
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
    assert manifest["alembic_head"] == "0014_add_source_type_review_events"
    assert manifest["release_channel"] == "team_bid_verified"

    incomplete = tmp_path / "candidate-incomplete"
    (incomplete / "QI-Crawler").mkdir(parents=True)
    (incomplete / f"QI-Crawler-Setup-v{VERSION}.exe").write_bytes(b"bad")
    failed = run_publish(incomplete)
    assert failed.returncode != 0
    assert current_exe.read_bytes() == b"two"
