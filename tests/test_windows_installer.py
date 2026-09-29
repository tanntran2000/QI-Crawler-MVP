import ast
import ctypes
import hashlib
import json
import os
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
    assert 'find_spec("pyside6")' in script.lower()
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
    assert "if ($smokeExitCode -ne 0)" in gate
    assert gate.index("$smokeProcess.ExitCode") < gate.index("$smokeExitCode -ne 0")
    assert "Kill()" in gate
    assert "if (-not $smokeProcess.WaitForExit(120000))" in gate
    assert "throw" in gate
    assert "QI_CRAWLER_DATA_DIR" in gate


def test_installer_is_per_user_and_preserves_bid_data() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert "#ifndef AppVersion" in script
    assert "#error AppVersion" in script
    assert "OutputBaseFilename=QI-Crawler-Setup-v{#AppVersion}" in script
    assert "DefaultDirName={localappdata}\\Programs\\QI-Crawler" in script
    assert "PrivilegesRequired=lowest" in script
    assert 'Source: "..\\dist\\QI-Crawler\\*"' in script
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
    assert "release_staging" in script
    assert "published" in script
    assert "Current" not in script
    assert "Previous" not in script
    assert "Crawler tool" not in script
    assert "BUILD_INFO.txt" in script
    assert "release_manifest.json" in script
    assert "release_artifact_receipt.json" in script
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


def test_publish_archives_immutable_candidate_and_rejects_external_or_duplicate_target(
    tmp_path: Path,
) -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell is required for the Windows publish behavior test")

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    (repo / "README.md").write_text("clean", encoding="utf-8")
    (repo / ".gitignore").write_text("release_staging/\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "README.md", ".gitignore"], check=True)
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

    publish_root = repo / "release_staging" / "published"

    def make_candidate(name: str, payload: bytes, schema_head: str = EXPECTED_SCHEMA_HEAD) -> Path:
        candidate = repo / "release_staging" / "candidate"
        if candidate.exists():
            shutil.rmtree(candidate)
        bundle = candidate / "QI-Crawler"
        bundle.mkdir(parents=True)
        (bundle / "QI-Crawler.exe").write_bytes(payload)
        installer = candidate / f"QI-Crawler-Setup-v{VERSION}.exe"
        installer.write_bytes(payload + b"-installer")
        exe_hash = hashlib.sha256(payload).hexdigest().upper()
        installer_hash = hashlib.sha256(installer.read_bytes()).hexdigest().upper()
        (bundle / "VERSION.txt").write_text(
            f"QI-Crawler\nVersion: {VERSION}\nChannel: INTERNAL CANDIDATE\n",
            encoding="utf-8",
        )
        (bundle / "WHAT_IS_NEW.txt").write_text("candidate changes\n", encoding="utf-8")
        (bundle / "CAPABILITIES.txt").write_text("NOT_YET_RUNTIME_VERIFIED\n", encoding="utf-8")
        (bundle / "BUILD_INFO.txt").write_text(
            "\n".join(
                [
                    "metadata_schema_version=qi-crawler-installed-release-v1",
                    "product=QI-Crawler",
                    f"version={VERSION}",
                    "source_git_sha="
                    + subprocess.check_output(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
                    ).strip(),
                    "source_branch=main",
                    "build_timestamp_utc=2026-08-23T00:00:00Z",
                    f"alembic_head={schema_head}",
                    "release_channel=INTERNAL_CANDIDATE",
                    f"portable_exe_sha256={exe_hash}",
                ]
            ),
            encoding="utf-8",
        )
        (bundle / "release_manifest.json").write_text(
            json.dumps(
                {
                    "metadata_schema_version": "qi-crawler-installed-release-v1",
                    "product": "QI-Crawler",
                    "version": VERSION,
                    "source_git_sha": subprocess.check_output(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
                    ).strip(),
                    "source_branch": "main",
                    "build_timestamp_utc": "2026-08-23T00:00:00Z",
                    "alembic_head": schema_head,
                    "release_channel": "INTERNAL_CANDIDATE",
                    "portable_exe_sha256": exe_hash,
                }
            ),
            encoding="utf-8",
        )
        (candidate / "release_artifact_receipt.json").write_text(
            json.dumps(
                {
                    "receipt_schema_version": "qi-crawler-release-artifact-v1",
                    "product": "QI-Crawler",
                    "version": VERSION,
                    "source_git_sha": subprocess.check_output(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
                    ).strip(),
                    "source_branch": "main",
                    "build_timestamp_utc": "2026-08-23T00:00:00Z",
                    "alembic_head": schema_head,
                    "portable_exe_sha256": exe_hash,
                    "installer_sha256": installer_hash,
                }
            ),
            encoding="utf-8",
        )
        return candidate

    def run_publish(
        candidate: Path,
        expected_head: str | None = EXPECTED_SCHEMA_HEAD,
        target: Path = publish_root,
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
            str(target),
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

    outside_root = tmp_path / "outside-published" / "archive"
    outside = run_publish(make_candidate("candidate-outside", b"outside"), target=outside_root)
    assert outside.returncode != 0
    assert not outside_root.parent.exists()

    valid_candidate = make_candidate("candidate-external-root", b"external")
    external_candidate = tmp_path / "external-candidate"
    shutil.copytree(valid_candidate, external_candidate)
    rejected_candidate = run_publish(external_candidate)
    assert rejected_candidate.returncode != 0
    assert not publish_root.exists()
    expected_source_sha = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()

    wrong_source_candidate = make_candidate("candidate-wrong-source", b"wrong-source")
    wrong_source_sha = "f" * 40
    wrong_source_manifest = wrong_source_candidate / "QI-Crawler" / "release_manifest.json"
    wrong_source_receipt = wrong_source_candidate / "release_artifact_receipt.json"
    manifest_fields = json.loads(wrong_source_manifest.read_text(encoding="utf-8"))
    receipt_fields = json.loads(wrong_source_receipt.read_text(encoding="utf-8"))
    manifest_fields["source_git_sha"] = wrong_source_sha
    receipt_fields["source_git_sha"] = wrong_source_sha
    wrong_source_manifest.write_text(json.dumps(manifest_fields), encoding="utf-8")
    wrong_source_receipt.write_text(json.dumps(receipt_fields), encoding="utf-8")
    build_info = wrong_source_candidate / "QI-Crawler" / "BUILD_INFO.txt"
    build_info.write_text(
        build_info.read_text(encoding="utf-8").replace(
            "source_git_sha=" + expected_source_sha,
            "source_git_sha=" + wrong_source_sha,
        ),
        encoding="utf-8",
    )
    wrong_source = run_publish(wrong_source_candidate)
    assert wrong_source.returncode != 0
    assert "exact clean main HEAD" in wrong_source.stderr
    assert not publish_root.exists()

    valid_candidate = make_candidate("candidate-one", b"one")
    (valid_candidate / "data-root" / "unmanaged").mkdir(parents=True)
    (valid_candidate / "data-root" / "unmanaged" / "data.db").write_bytes(b"do-not-publish")
    first = run_publish(valid_candidate)
    assert first.returncode == 0, first.stderr
    archives = list(publish_root.iterdir())
    assert len(archives) == 1
    archive = archives[0]
    assert archive.name == f"v{VERSION}-{expected_source_sha[:12]}-20260823T0000000000000Z"
    archived_exe = archive / "QI-Crawler" / "QI-Crawler.exe"
    enumerated_paths = list(archive.rglob("*"))
    staging_entries = [path.name for path in publish_root.iterdir() if path.name.startswith(".stage-")]
    stat_error = None
    try:
        archived_exe.stat()
    except OSError as exc:
        stat_error = repr(exc)
    direct_bytes = None
    open_error = None
    try:
        with archived_exe.open("rb") as stream:
            direct_bytes = stream.read()
    except OSError as exc:
        open_error = repr(exc)
    assert archived_exe.is_file(), (
        f"selected_archive={archive}; selected_file={archived_exe}; "
        f"archive_entries={[path.relative_to(archive).as_posix() for path in enumerated_paths]}; "
        f"staging_entries={staging_entries}; stat_error={stat_error}; open_error={open_error}; "
        f"process_exit={first.returncode}; stdout={first.stdout}; stderr={first.stderr}"
    )
    assert stat_error is None
    assert open_error is None
    assert direct_bytes == b"one"
    assert not staging_entries
    assert all(len(str(path)) <= 240 for path in [archive, *enumerated_paths])
    assert not (archive / "data-root").exists()

    second = run_publish(make_candidate("candidate-two", b"two"))
    assert second.returncode != 0
    assert archived_exe.read_bytes() == b"one"
    assert list(publish_root.iterdir()) == [archive]
    assert not (publish_root / "Current").exists()
    assert not (publish_root / "Previous").exists()
    info = (archive / "QI-Crawler" / "BUILD_INFO.txt").read_text(encoding="utf-8")
    assert "product=QI-Crawler" in info
    assert f"version={VERSION}" in info
    assert ("portable_exe_sha256=" + hashlib.sha256(b"one").hexdigest().upper()) in info
    manifest = json.loads(
        (archive / "QI-Crawler" / "release_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["product"] == "QI-Crawler"
    assert manifest["version"] == VERSION
    assert manifest["alembic_head"] == EXPECTED_SCHEMA_HEAD
    assert manifest["release_channel"] == "INTERNAL_CANDIDATE"
    assert "installer_sha256" not in manifest
    receipt = json.loads(
        (archive / "release_artifact_receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["installer_sha256"] == hashlib.sha256(b"one-installer").hexdigest().upper()

    incomplete = repo / "release_staging" / "candidate"
    if incomplete.exists():
        shutil.rmtree(incomplete)
    (incomplete / "QI-Crawler").mkdir(parents=True)
    (incomplete / f"QI-Crawler-Setup-v{VERSION}.exe").write_bytes(b"bad")
    failed = run_publish(incomplete)
    assert failed.returncode != 0
    assert archived_exe.read_bytes() == b"one"

    wrong_head = run_publish(
        make_candidate("candidate-wrong-head", b"wrong", schema_head="wrong-head")
    )
    assert wrong_head.returncode != 0
    assert archived_exe.read_bytes() == b"one"

    build_info_only_mismatch = make_candidate(
        "candidate-build-info-only-mismatch", b"build-info-mismatch"
    )
    build_info_path = build_info_only_mismatch / "QI-Crawler" / "BUILD_INFO.txt"
    build_info_path.write_text(
        build_info_path.read_text(encoding="utf-8").replace(
            f"alembic_head={EXPECTED_SCHEMA_HEAD}",
            "alembic_head=wrong-build-info-head",
        ),
        encoding="utf-8",
    )
    build_info_only_failed = run_publish(build_info_only_mismatch)
    assert build_info_only_failed.returncode != 0
    assert (
        json.loads(
            (build_info_only_mismatch / "QI-Crawler" / "release_manifest.json").read_text(
                encoding="utf-8"
            )
        )["alembic_head"]
        == EXPECTED_SCHEMA_HEAD
    )
    assert "alembic_head=wrong-build-info-head" in build_info_path.read_text(encoding="utf-8")
    assert archived_exe.read_bytes() == b"one"

    missing_expected_head = run_publish(
        make_candidate("candidate-missing-expected-head", b"missing"), expected_head=None
    )
    assert missing_expected_head.returncode != 0
    assert archived_exe.read_bytes() == b"one"


def _provenance_candidate(tmp_path: Path) -> tuple[Path, Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    (repo / "README.md").write_text("clean", encoding="utf-8")
    (repo / ".gitignore").write_text("release_staging/\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "README.md", ".gitignore"], check=True)
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
    source_sha = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    candidate = repo / "release_staging" / "candidate"
    bundle = candidate / "QI-Crawler"
    bundle.mkdir(parents=True)
    exe = bundle / "QI-Crawler.exe"
    exe.write_bytes(b"portable")
    installer = candidate / f"QI-Crawler-Setup-v{VERSION}.exe"
    installer.write_bytes(b"installer")
    exe_hash = hashlib.sha256(exe.read_bytes()).hexdigest().upper()
    installer_hash = hashlib.sha256(installer.read_bytes()).hexdigest().upper()
    (bundle / "VERSION.txt").write_text(
        f"QI-Crawler\nVersion: {VERSION}\nChannel: INTERNAL CANDIDATE\n", encoding="utf-8"
    )
    (bundle / "WHAT_IS_NEW.txt").write_text("candidate changes\n", encoding="utf-8")
    (bundle / "CAPABILITIES.txt").write_text(
        "NOT_YET_RUNTIME_VERIFIED\n", encoding="utf-8"
    )
    shared = {
        "product": "QI-Crawler",
        "version": VERSION,
        "source_git_sha": source_sha,
        "source_branch": "main",
        "build_timestamp_utc": "2026-08-23T00:00:00Z",
        "alembic_head": EXPECTED_SCHEMA_HEAD,
        "portable_exe_sha256": exe_hash,
    }
    manifest = {
        "metadata_schema_version": "qi-crawler-installed-release-v1",
        **shared,
        "release_channel": "INTERNAL_CANDIDATE",
    }
    receipt = {
        "receipt_schema_version": "qi-crawler-release-artifact-v1",
        **shared,
        "installer_sha256": installer_hash,
    }
    build_info = {
        "metadata_schema_version": manifest["metadata_schema_version"],
        **shared,
        "release_channel": manifest["release_channel"],
    }
    (bundle / "release_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (candidate / "release_artifact_receipt.json").write_text(
        json.dumps(receipt), encoding="utf-8"
    )
    (bundle / "BUILD_INFO.txt").write_text(
        "\n".join(f"{key}={value}" for key, value in build_info.items()) + "\n",
        encoding="utf-8",
    )
    return repo, candidate, source_sha


def _run_provenance_publish(
    shell: str, repo: Path, candidate: Path, publish_root: Path
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
        "-ExpectedAlembicHead",
        EXPECTED_SCHEMA_HEAD,
    ]
    if sys.platform == "win32" and Path(shell).name.lower() == "powershell.exe":
        args[1:1] = ["-ExecutionPolicy", "Bypass"]
    return subprocess.run(args, capture_output=True, text=True, check=False)


def test_publish_rejects_long_candidate_descendant_before_creating_publish_root(
    tmp_path: Path,
) -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell is required for the Windows publish behavior test")
    repo, candidate, source_sha = _provenance_candidate(tmp_path)
    archive_name = f"v{VERSION}-{source_sha[:12]}-20260823T0000000000000Z"
    candidate_payload_root = candidate / "QI-Crawler"
    projected_payload_root = (
        repo / "release_staging" / "published" / archive_name / "QI-Crawler"
    )
    directory_prefix = "nested-"
    filename = "payload.bin"
    directory_name_length = (
        240
        - len(str(candidate_payload_root))
        - 1
        - len(directory_prefix)
        - 1
        - len(filename)
    )
    assert directory_name_length > 0
    relative = Path(directory_prefix + "a" * directory_name_length) / filename
    long_file = candidate_payload_root / relative
    projected = projected_payload_root / relative
    long_file.parent.mkdir(parents=True)
    long_file.write_bytes(b"bounded-path-test")

    assert len(str(long_file)) == 240
    assert len(str(projected)) > 240

    publish_root = repo / "release_staging" / "published"
    result = _run_provenance_publish(shell, repo, candidate, publish_root)
    assert result.returncode != 0
    assert "exceeds 240 characters" in result.stderr
    assert not publish_root.exists()


def test_publish_rejects_candidate_reparse_descendant_before_publication(
    tmp_path: Path,
) -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell is required for the Windows publish behavior test")
    repo, candidate, _source_sha = _provenance_candidate(tmp_path)
    target = tmp_path / "reparse-target"
    target.mkdir()
    reparse_path = candidate / "QI-Crawler" / "linked-assets"
    try:
        os.symlink(target, reparse_path, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable on this host: {exc}")

    publish_root = repo / "release_staging" / "published"
    result = _run_provenance_publish(shell, repo, candidate, publish_root)
    assert result.returncode != 0
    assert "reparse point" in result.stderr
    assert not publish_root.exists()


def test_publish_removes_only_its_stage_after_copy_failure(tmp_path: Path) -> None:
    if sys.platform != "win32":
        pytest.skip("exclusive Windows file handles are required for this copy-failure seam")
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell is required for the Windows publish behavior test")
    repo, candidate, _source_sha = _provenance_candidate(tmp_path)
    blocked_source = candidate / "QI-Crawler" / "zz-copy-blocked.bin"
    blocked_source.write_bytes(b"locked during copy")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    kernel32.CreateFileW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.CreateFileW(
        str(blocked_source),
        0x80000000,  # GENERIC_READ
        0,  # no sharing: Copy-Item must fail when it reaches this extra file
        None,
        3,  # OPEN_EXISTING
        0x80,  # FILE_ATTRIBUTE_NORMAL
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        pytest.skip(f"could not hold the synthetic source file exclusively: {ctypes.get_last_error()}")
    publish_root = repo / "release_staging" / "published"
    try:
        result = _run_provenance_publish(shell, repo, candidate, publish_root)
    finally:
        kernel32.CloseHandle(handle)

    assert result.returncode != 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    entries = list(publish_root.iterdir()) if publish_root.exists() else []
    assert not [path for path in entries if path.name.startswith(".stage-")], (
        f"invocation-owned stage remained after copy failure: {entries}; "
        f"stdout={result.stdout}; stderr={result.stderr}"
    )
    assert not [path for path in entries if path.is_dir()]


@pytest.mark.parametrize(
    "case",
    [
        "mixed_source_sha",
        "mixed_source_branch",
        "mixed_timestamp",
        "mixed_alembic",
        "mixed_portable_hash",
        "mixed_product",
        "mixed_version",
        "missing_source_git_sha",
        "empty_source_branch",
        "invalid_git_sha",
        "malformed_timestamp",
        "missing_alembic_head",
        "invalid_portable_hash",
        "missing_installer_hash",
        "invalid_installer_hash",
        "unsupported_manifest_schema",
        "unsupported_receipt_schema",
        "duplicate_build_info_key",
        "missing_build_info_source_sha",
        "empty_build_info_branch",
        "malformed_build_info_line",
        "build_info_source_sha_mismatch",
        "build_info_alembic_mismatch",
        "build_info_portable_hash_mismatch",
    ],
)
def test_publish_rejects_incomplete_malformed_or_mixed_provenance(
    tmp_path: Path, case: str
) -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell is required for the Windows publish behavior test")
    repo, candidate, _source_sha = _provenance_candidate(tmp_path)
    bundle = candidate / "QI-Crawler"
    manifest_path = bundle / "release_manifest.json"
    receipt_path = candidate / "release_artifact_receipt.json"
    build_info_path = bundle / "BUILD_INFO.txt"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    info_lines = build_info_path.read_text(encoding="utf-8").splitlines()

    if case.startswith("mixed_"):
        field = {
            "mixed_source_sha": "source_git_sha",
            "mixed_source_branch": "source_branch",
            "mixed_timestamp": "build_timestamp_utc",
            "mixed_alembic": "alembic_head",
            "mixed_portable_hash": "portable_exe_sha256",
            "mixed_product": "product",
            "mixed_version": "version",
        }[case]
        receipt[field] = {
            "source_git_sha": "f" * 40,
            "source_branch": "other-branch",
            "build_timestamp_utc": "2026-08-24T00:00:00Z",
            "alembic_head": "other_revision",
            "portable_exe_sha256": "f" * 64,
            "product": "Other-Product",
            "version": "9.9.9",
        }[field]
    elif case == "missing_source_git_sha":
        manifest.pop("source_git_sha")
    elif case == "empty_source_branch":
        manifest["source_branch"] = ""
    elif case == "invalid_git_sha":
        manifest["source_git_sha"] = "not-a-git-sha"
    elif case == "malformed_timestamp":
        manifest["build_timestamp_utc"] = "not-a-timestamp"
    elif case == "missing_alembic_head":
        receipt.pop("alembic_head")
    elif case == "invalid_portable_hash":
        manifest["portable_exe_sha256"] = "xyz"
    elif case == "missing_installer_hash":
        receipt.pop("installer_sha256")
    elif case == "invalid_installer_hash":
        receipt["installer_sha256"] = "xyz"
    elif case == "unsupported_manifest_schema":
        manifest["metadata_schema_version"] = "unsupported"
    elif case == "unsupported_receipt_schema":
        receipt["receipt_schema_version"] = "unsupported"
    elif case == "duplicate_build_info_key":
        info_lines.append("source_git_sha=" + _source_sha)
    elif case == "missing_build_info_source_sha":
        info_lines = [line for line in info_lines if not line.startswith("source_git_sha=")]
    elif case == "empty_build_info_branch":
        info_lines = [
            "source_branch=" if line.startswith("source_branch=") else line for line in info_lines
        ]
    elif case == "malformed_build_info_line":
        info_lines.append("malformed-without-equals")
    elif case == "build_info_source_sha_mismatch":
        info_lines = [
            "source_git_sha=" + "f" * 40 if line.startswith("source_git_sha=") else line
            for line in info_lines
        ]
    elif case == "build_info_alembic_mismatch":
        info_lines = [
            "alembic_head=other_revision" if line.startswith("alembic_head=") else line
            for line in info_lines
        ]
    elif case == "build_info_portable_hash_mismatch":
        info_lines = [
            "portable_exe_sha256=" + "f" * 64
            if line.startswith("portable_exe_sha256=")
            else line
            for line in info_lines
        ]

    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    build_info_path.write_text("\n".join(info_lines) + "\n", encoding="utf-8")
    publish_root = repo / "release_staging" / "published"

    result = _run_provenance_publish(shell, repo, candidate, publish_root)

    assert result.returncode != 0, f"case={case}\nstdout={result.stdout}\nstderr={result.stderr}"
    assert not (publish_root / "Current").exists()
