from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
GUARD = REPO / "tools" / "release" / "a3_f5_guard.ps1"
JOB_HELPER = REPO / "tools" / "release" / "a3_job_object.ps1"
PROBE = REPO / "tools" / "release" / "a3_probe_windows.ps1"

WINDOWS_REALF5_PROBE_ONLY = pytest.mark.skipif(
    sys.platform != "win32" or shutil.which("powershell.exe") is None,
    reason="Windows RealF5 probe contract",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@WINDOWS_REALF5_PROBE_ONLY
@pytest.mark.parametrize("checkpoint", [True, False])
def test_dispatch_checkpoint_does_not_resolve_release_artifacts(
    tmp_path: Path, checkpoint: bool,
) -> None:
    """Execute the real initialization block with historical staging unavailable."""
    source = PROBE.read_text(encoding="utf-8")
    initialization = source.split("$evidence = if", 1)[1].split("function Write-Json", 1)[0]
    script = (
        "$ErrorActionPreference='Stop'; $f5OnlyTestCheckpoint="
        + ("$true; " if checkpoint else "$false; ")
        + "$repo=(Get-Location).Path; $EvidenceRoot='evidence'; $f5OnlySandbox=$repo; "
        "function Resolve-Path { param($LiteralPath) "
        "if ($LiteralPath -like '*release_staging*') { throw 'RELEASE_ARTIFACT_ACCESS_FORBIDDEN' }; "
        "@{Path=$LiteralPath} }; "
        "function Get-Sha256 { throw 'RELEASE_ARTIFACT_ACCESS_FORBIDDEN' }; "
        "$evidence = if" + initialization + "; 'DISPATCH_INIT=PASS'"
    )
    result = subprocess.run(
        [_powershell(), "-NoProfile", "-NonInteractive", "-Command", script],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    if checkpoint:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "DISPATCH_INIT=PASS" in result.stdout
    else:
        assert result.returncode != 0
        assert "RELEASE_ARTIFACT_ACCESS_FORBIDDEN" in result.stdout + result.stderr


def _powershell() -> str:
    for candidate in ("powershell.exe", "powershell", "pwsh.exe", "pwsh"):
        executable = shutil.which(candidate)
        if executable is not None:
            return executable
    pytest.skip("PowerShell is required for the Windows F5 guard")


def _sandbox(tmp_path: Path) -> tuple[Path, Path]:
    sandbox = tmp_path / "sandbox"
    runtime = sandbox / "runtime"
    runtime.mkdir(parents=True)
    marker = runtime / "runtime-marker.bin"
    marker.write_bytes(b"runtime")
    return sandbox, marker


def _canonical_layout(sandbox: Path) -> None:
    (sandbox / "install" / "QI-Crawler").mkdir(parents=True)
    (sandbox / "data").mkdir()
    (sandbox / "transaction").mkdir()
    (sandbox / "install" / "QI-Crawler" / "QI-Crawler.exe").write_bytes(b"fixture")


def _manifest(
    tmp_path: Path,
    sandbox: Path,
    input_path: Path,
    runtime_files: tuple[Path, ...] = (),
) -> Path:
    runtime = sandbox / "runtime"
    marker = runtime / "runtime-marker.bin"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip()
    git_status = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).splitlines()
    manifest = {
        "schema": "AO-04-C3-F5-TRIAL-INPUT-V1",
        "head": head,
        "branch": branch,
        "git_status": git_status,
        "sandbox_path": str(sandbox.resolve()),
        "runtime_root": str(runtime.resolve()),
        "runtime_build_identity": "fixture-runtime",
        "runtime_manifest": [
            {
                "relative_path": file.relative_to(runtime).as_posix(),
                "size_bytes": file.stat().st_size if file.exists() else 7,
                "sha256": _sha(file) if file.exists() else hashlib.sha256(b"runtime").hexdigest(),
                "tracked": "NO",
                "reparse_point": "NO",
                "read_status": "PASS",
            }
            for file in (marker, *runtime_files)
        ],
        "execution_inputs": [
            {
                "path": str(input_path.resolve()),
                "classification": "EXECUTION_INPUT",
                "size_bytes": input_path.stat().st_size,
                "sha256": _sha(input_path),
                "tracked": "NO",
                "reparse_point": "NO",
                "read_status": "PASS",
            }
        ],
        "generated_inputs": [],
        "environment_allowlist": {"AO_GUARD_TEST": "1"},
    }
    path = tmp_path / "trial-input-manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def _bind_preexecution_contract(tmp_path: Path, sandbox: Path, manifest: Path) -> Path:
    contract_path = tmp_path / "F5_PREEXECUTION_CONTRACT.json"
    existing = json.loads(manifest.read_text(encoding="utf-8"))
    if contract_path.exists() and any(
        item.get("path") == str(contract_path.resolve())
        for item in existing.get("execution_inputs", [])
    ):
        return contract_path
    contract = {
        "schema": "AO-04-C3-F5-PREEXECUTION-CONTRACT-V1",
        "contract_status": "VALID",
        "sandbox_path": str(sandbox.resolve()),
        "sandbox_resource_id": hashlib.sha256(
            str(sandbox.resolve()).rstrip("\\").lower().replace("\\", "/").encode("utf-8")
        ).hexdigest(),
        "volume_root": str(Path(sandbox.anchor)),
        "canonical_route_identity": {
            "function": "Invoke-F5CanonicalRoute",
            "mode": "F5Only",
            "execution_mode": "RealF5",
        },
        "guard_identity": {"path": str(GUARD.resolve()), "sha256": _sha(GUARD)},
        "probe_identity": {"path": str(PROBE.resolve()), "sha256": _sha(PROBE)},
        "runtime_identity": {
            "runtime_root": str((sandbox / "runtime").resolve()),
            "build_identity": "fixture-runtime",
            "file_count": 1,
            "logical_bytes": 7,
        },
        "required_layout": [
            {
                "id": "runtime",
                "relative_path": "runtime",
                "classification": "PREEXISTING_IMMUTABLE_INPUT",
                "kind": "directory",
                "must_exist_before_dispatch": True,
                "may_be_created_during_f5": False,
                "expected_max_bytes": 7,
                "bound_source": "fixture runtime manifest",
                "recovery_requirement": "preserve",
            },
            {
                "id": "install",
                "relative_path": "install",
                "classification": "PREEXISTING_IMMUTABLE_INPUT",
                "kind": "directory",
                "must_exist_before_dispatch": True,
                "may_be_created_during_f5": False,
                "expected_max_bytes": 7,
                "bound_source": "fixture install",
                "recovery_requirement": "preserve",
            },
            {
                "id": "data",
                "relative_path": "data",
                "classification": "PREEXISTING_MUTABLE_FIXTURE",
                "kind": "directory",
                "must_exist_before_dispatch": True,
                "may_be_created_during_f5": False,
                "expected_max_bytes": 0,
                "bound_source": "fixture data",
                "recovery_requirement": "snapshot",
            },
            {
                "id": "transaction",
                "relative_path": "transaction",
                "classification": "PREEXISTING_MUTABLE_FIXTURE",
                "kind": "directory",
                "must_exist_before_dispatch": True,
                "may_be_created_during_f5": False,
                "expected_max_bytes": 1024,
                "bound_source": "fixture transaction",
                "recovery_requirement": "journal",
            },
        ],
        "capacity_operations": [
            {
                "operation_id": "TX_STATE",
                "stage": "P1_P2",
                "target_volume": str(Path(sandbox.anchor)),
                "max_write_bytes": 512,
                "temporary_overhead_bytes": 256,
                "peak_bytes": 768,
                "remaining_worst_case_after": 4096,
                "bound_source": "fixture transaction bound",
                "fail_closed_if_unknown": True,
            }
        ],
        "next_operation_peak_bytes": 768,
        "remaining_peak_bytes": 4096,
        "recovery_reserve_bytes": 2147483648,
        "safety_reserve_bytes": 4294967296,
        "max_runtime_copies": 0,
        "max_new_sandboxes": 0,
        "max_automatic_retries": 0,
        "max_concurrent_trials": 1,
        "created_utc": "2026-09-12T00:00:00Z",
    }
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    data = existing
    data["execution_inputs"].append(
        {
            "path": str(contract_path.resolve()),
            "classification": "EXECUTION_INPUT",
            "size_bytes": contract_path.stat().st_size,
            "sha256": _sha(contract_path),
            "tracked": "NO",
            "reparse_point": "NO",
            "read_status": "PASS",
        }
    )
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return contract_path


def _command(
    tmp_path: Path,
    sandbox: Path,
    manifest: Path,
    *extra: str,
    sandbox_argument: str | None = None,
    run_id: str = "test-run",
    evidence_root: Path | None = None,
    state_root: Path | None = None,
    global_lock_path: Path | None = None,
    test_material_write_path: Path | None = None,
) -> list[str]:
    command = [
        _powershell(),
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(GUARD),
        "-Mode",
        "F5Only",
        "-ExistingSandboxPath",
        sandbox_argument or str(sandbox),
        "-RunId",
        run_id,
        "-InputManifestPath",
        str(manifest),
        "-EvidenceRoot",
        str(evidence_root or (tmp_path / "evidence")),
        "-DryRun",
        *extra,
    ]
    if state_root is not None:
        command.extend(["-TestStateRoot", str(state_root)])
    if global_lock_path is not None:
        command.extend(["-TestGlobalLockPath", str(global_lock_path)])
    if test_material_write_path is not None:
        command.extend(["-TestMaterialWritePath", str(test_material_write_path)])
    return command


def _run(
    tmp_path: Path,
    sandbox: Path,
    manifest: Path,
    *extra: str,
    sandbox_argument: str | None = None,
    run_id: str = "test-run",
    evidence_root: Path | None = None,
    state_root: Path | None = None,
    global_lock_path: Path | None = None,
    test_material_write_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    global_lock_path = global_lock_path or (tmp_path / "global.lock")
    environment = os.environ.copy()
    if state_root is not None or global_lock_path is not None or test_material_write_path is not None:
        environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    return subprocess.run(
        _command(
            tmp_path,
            sandbox,
            manifest,
            *extra,
            sandbox_argument=sandbox_argument,
            run_id=run_id,
            evidence_root=evidence_root,
            state_root=state_root,
            global_lock_path=global_lock_path,
            test_material_write_path=test_material_write_path,
        ),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )


def _run_without_dry_run(
    tmp_path: Path, sandbox: Path, manifest: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    global_lock_path = tmp_path / "global.lock"
    command = [
        part
        for part in _command(
            tmp_path,
            sandbox,
            manifest,
            *extra,
            global_lock_path=global_lock_path,
        )
        if part != "-DryRun"
    ]
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    return subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )


def _capacity_probe_command(path: str) -> list[str]:
    return [
        _powershell(),
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(GUARD),
        "-Mode",
        "F5Only",
        "-ExistingSandboxPath",
        str(REPO),
        "-RunId",
        "capacity-probe",
        "-InputManifestPath",
        str(GUARD),
        "-CapacityProbeOnly",
        "-CapacityProbePath",
        path,
    ]


def _run_guarded_real(
    tmp_path: Path,
    sandbox: Path,
    manifest: Path,
    *,
    run_id: str = "real-test",
    state_root: Path | None = None,
    evidence_root: Path | None = None,
    context_path: Path | None = None,
    dispatch_hold_seconds: int = 0,
) -> subprocess.CompletedProcess[str]:
    state_root = state_root or (tmp_path / "state")
    evidence_root = evidence_root or (tmp_path / "evidence")
    contract_path = _bind_preexecution_contract(tmp_path, sandbox, manifest)
    global_lock_path = tmp_path / "global.lock"
    command = [
        _powershell(),
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(GUARD),
        "-Mode",
        "F5Only",
        "-ExecutionMode",
        "RealF5",
        "-TestDispatchBoundary",
        "-ExistingSandboxPath",
        str(sandbox),
        "-RunId",
        run_id,
        "-InputManifestPath",
        str(manifest),
        "-PreexecutionContractPath",
        str(contract_path),
        "-EvidenceRoot",
        str(evidence_root),
        "-FreeNowBytes",
        "10000000000",
        "-NextOperationPeakBytes",
        "768",
        "-RemainingPeakAfterOperationBytes",
        "4096",
        "-RecoveryReserveBytes",
        "2147483648",
        "-SafetyReserveBytes",
        "4294967296",
        "-TestStateRoot",
        str(state_root),
        "-TestGlobalLockPath",
        str(global_lock_path),
    ]
    if context_path is not None:
        command.extend(["-ExecutionContextPath", str(context_path)])
    if dispatch_hold_seconds:
        command.extend(["-DispatchHoldSeconds", str(dispatch_hold_seconds)])
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    return subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )


def _guarded_real_command(
    tmp_path: Path,
    sandbox: Path,
    manifest: Path,
    *,
    run_id: str,
    state_root: Path,
    evidence_root: Path,
    dispatch_hold_seconds: int = 0,
) -> list[str]:
    contract_path = _bind_preexecution_contract(tmp_path, sandbox, manifest)
    command = [
        _powershell(),
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(GUARD),
        "-Mode",
        "F5Only",
        "-ExecutionMode",
        "RealF5",
        "-TestDispatchBoundary",
        "-ExistingSandboxPath",
        str(sandbox),
        "-RunId",
        run_id,
        "-InputManifestPath",
        str(manifest),
        "-PreexecutionContractPath",
        str(contract_path),
        "-EvidenceRoot",
        str(evidence_root),
        "-FreeNowBytes",
        "10000000000",
        "-NextOperationPeakBytes",
        "768",
        "-RemainingPeakAfterOperationBytes",
        "4096",
        "-RecoveryReserveBytes",
        "2147483648",
        "-SafetyReserveBytes",
        "4294967296",
        "-TestStateRoot",
        str(state_root),
        "-TestGlobalLockPath",
        str(tmp_path / "global.lock"),
    ]
    if dispatch_hold_seconds:
        command.extend(["-DispatchHoldSeconds", str(dispatch_hold_seconds)])
    return command


def _probe_real_command(
    sandbox: Path,
    manifest: Path,
    context: Path,
    state_root: Path,
    evidence_root: Path,
    *,
    run_id: str = "real-test",
) -> list[str]:
    return [
        _powershell(),
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(PROBE),
        "-Mode",
        "F5Only",
        "-ExecutionMode",
        "RealF5",
        "-TestDispatchBoundary",
        "-ExecutionContextPath",
        str(context),
        "-ExistingSandboxPath",
        str(sandbox),
        "-RunId",
        run_id,
        "-InputManifestPath",
        str(manifest),
        "-EvidenceRoot",
        str(evidence_root),
        "-TestStateRoot",
        str(state_root),
    ]


def _lifecycle_state_file(state_root: Path) -> Path:
    matches = list(state_root.rglob("lifecycle_state.json"))
    assert len(matches) == 1, matches
    return matches[0]


def _wait_for_running_lifecycle(
    state_root: Path,
    *,
    run_id: str,
    sandbox: Path,
    timeout_seconds: float = 10.0,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    expected_sandbox = os.path.normcase(str(sandbox.resolve()))
    last_state: dict[str, object] | None = None
    while time.monotonic() < deadline:
        matches = list(state_root.rglob("lifecycle_state.json"))
        if len(matches) == 1:
            try:
                candidate = json.loads(matches[0].read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                candidate = None
            if isinstance(candidate, dict):
                last_state = candidate
                canonical_sandbox = candidate.get("canonical_sandbox_path")
                if (
                    candidate.get("last_run_id") == run_id
                    and candidate.get("execution_state") == "RUNNING"
                    and isinstance(canonical_sandbox, str)
                    and os.path.normcase(str(Path(canonical_sandbox).resolve()))
                    == expected_sandbox
                ):
                    return candidate
        time.sleep(0.05)
    pytest.fail(
        "timed out waiting for the holder lifecycle to reach RUNNING: "
        f"run_id={run_id!r}, last_state={last_state!r}"
    )


def _replace_lifecycle_state(state_root: Path, **changes: object) -> None:
    path = _lifecycle_state_file(state_root)
    state = json.loads(path.read_text(encoding="utf-8"))
    state.update(changes)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def test_valid_dry_run_selects_f5_only_without_runtime_copy(tmp_path: Path) -> None:
    sandbox, marker = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("Write-Output guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "F5_ONLY_ROUTE_SELECTED" in result.stdout
    assert "NEW_RUNTIME_COPY=0" in result.stdout
    assert marker.read_bytes() == b"runtime"


def test_nested_descendant_runtime_identity_is_accepted(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    nested = sandbox / "runtime" / "a" / "b.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("nested\n", encoding="utf-8")
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path, (nested,))

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "F5_ONLY_ROUTE_SELECTED" in result.stdout


def test_trailing_separator_on_root_is_accepted(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    result = _run(
        tmp_path,
        sandbox,
        manifest,
        sandbox_argument=f"{sandbox}{os.sep}",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_sibling_prefix_sandbox_identity_fails_closed(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["sandbox_path"] = f"{sandbox}-other"
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode != 0
    assert "EXISTING_SANDBOX_INVALID" in result.stdout + result.stderr


def test_different_root_runtime_identity_fails_closed(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["runtime_root"] = str((tmp_path / "outside-runtime").resolve())
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode != 0
    assert "RUNTIME_MANIFEST_INVALID" in result.stdout + result.stderr


def test_missing_sandbox_fails_closed(tmp_path: Path) -> None:
    sandbox = tmp_path / "missing-sandbox"
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode != 0
    assert "EXISTING_SANDBOX_INVALID" in result.stdout + result.stderr


def test_manifest_drift_refuses_to_run(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("before\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    input_path.write_text("after\n", encoding="utf-8")

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode != 0
    assert "EXECUTION_INPUT_DRIFT" in result.stdout + result.stderr


def test_runtime_manifest_drift_refuses_to_run(tmp_path: Path) -> None:
    sandbox, marker = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    marker.write_bytes(b"changed")

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode != 0
    assert "RUNTIME_IDENTITY_MISMATCH" in result.stdout + result.stderr


def test_unbound_execution_input_fails_closed(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["execution_inputs"][0]["classification"] = "EVIDENCE_ONLY"
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode != 0
    assert "UNBOUND_EXECUTION_INPUT" in result.stdout + result.stderr


def test_secret_environment_allowlist_fails_closed(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["environment_allowlist"] = {"API_TOKEN": "must-not-be-bound"}
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    result = _run(tmp_path, sandbox, manifest)

    assert result.returncode != 0
    assert "ENV_SECRET_UNSAFE" in result.stdout + result.stderr


def test_incomplete_trial_blocks_sandbox_reuse(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    first = _run(
        tmp_path,
        sandbox,
        manifest,
        "-SimulateStorageFailure",
        run_id="old",
        state_root=tmp_path / "state",
    )
    assert first.returncode != 0
    result = _run(tmp_path, sandbox, manifest, run_id="new", state_root=tmp_path / "state")

    assert result.returncode != 0
    assert "PREVIOUS_TRIAL_INCOMPLETE" in result.stdout + result.stderr


def test_incomplete_state_cannot_change_evidence_root_or_run_id(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    first = _run(
        tmp_path,
        sandbox,
        manifest,
        "-SimulateStorageFailure",
        run_id="run-a",
        evidence_root=tmp_path / "evidence-a",
        state_root=tmp_path / "state",
    )
    assert first.returncode != 0
    assert "INCOMPLETE_STORAGE_FAILURE" in first.stdout + first.stderr

    second = _run(
        tmp_path,
        sandbox,
        manifest,
        run_id="run-b",
        evidence_root=tmp_path / "evidence-b",
        state_root=tmp_path / "state",
    )
    assert second.returncode != 0
    assert "PREVIOUS_TRIAL_INCOMPLETE" in second.stdout + second.stderr


def test_stale_running_state_blocks_reuse(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"

    first = _run(tmp_path, sandbox, manifest, state_root=state_root)
    assert first.returncode == 0, first.stdout + first.stderr
    _replace_lifecycle_state(state_root, execution_state="RUNNING", last_run_id="stale-running")

    result = _run(tmp_path, sandbox, manifest, run_id="new-run", state_root=state_root)

    assert result.returncode != 0
    assert "PREVIOUS_TRIAL_INCOMPLETE" in result.stdout + result.stderr


def test_stale_post_kill_state_blocks_reuse(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"

    first = _run(tmp_path, sandbox, manifest, state_root=state_root)
    assert first.returncode == 0, first.stdout + first.stderr
    _replace_lifecycle_state(state_root, execution_state="POST_KILL_VERIFICATION", last_run_id="stale-post-kill")

    result = _run(tmp_path, sandbox, manifest, run_id="new-run", state_root=state_root)

    assert result.returncode != 0
    assert "PREVIOUS_TRIAL_INCOMPLETE" in result.stdout + result.stderr


def test_corrupt_lifecycle_state_fails_closed(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"

    first = _run(tmp_path, sandbox, manifest, state_root=state_root)
    assert first.returncode == 0, first.stdout + first.stderr
    _lifecycle_state_file(state_root).write_text("{not-json\n", encoding="utf-8")

    result = _run(tmp_path, sandbox, manifest, run_id="new-run", state_root=state_root)

    assert result.returncode != 0
    assert "STATE_CORRUPT" in result.stdout + result.stderr


def test_different_sandbox_resource_is_isolated(tmp_path: Path) -> None:
    sandbox_a, _ = _sandbox(tmp_path / "a")
    sandbox_b, _ = _sandbox(tmp_path / "b")
    input_a = tmp_path / "a" / "controller.ps1"
    input_b = tmp_path / "b" / "controller.ps1"
    input_a.write_text("guard-a\n", encoding="utf-8")
    input_b.write_text("guard-b\n", encoding="utf-8")
    manifest_a = _manifest(tmp_path / "a", sandbox_a, input_a)
    manifest_b = _manifest(tmp_path / "b", sandbox_b, input_b)
    state_root = tmp_path / "shared-state"

    failed = _run(
        tmp_path / "a",
        sandbox_a,
        manifest_a,
        "-SimulateStorageFailure",
        state_root=state_root,
    )
    assert failed.returncode != 0

    independent = _run(tmp_path / "b", sandbox_b, manifest_b, state_root=state_root)

    assert independent.returncode == 0, independent.stdout + independent.stderr


def test_completed_state_allows_new_run_id_and_evidence_root(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"

    first = _run(
        tmp_path,
        sandbox,
        manifest,
        run_id="completed-a",
        evidence_root=tmp_path / "evidence-a",
        state_root=state_root,
    )
    assert first.returncode == 0, first.stdout + first.stderr

    second = _run(
        tmp_path,
        sandbox,
        manifest,
        run_id="completed-b",
        evidence_root=tmp_path / "evidence-b",
        state_root=state_root,
    )

    assert second.returncode == 0, second.stdout + second.stderr


def test_same_run_id_is_rejected_after_completion(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"

    first = _run(tmp_path, sandbox, manifest, run_id="same-run", state_root=state_root)
    assert first.returncode == 0, first.stdout + first.stderr
    second = _run(tmp_path, sandbox, manifest, run_id="same-run", state_root=state_root)

    assert second.returncode != 0
    assert "RUN_ID_REUSE" in second.stdout + second.stderr


def test_real_filesystem_failure_persists_incomplete_state_and_blocks_retry(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"
    blocked_target = tmp_path / "material-target"
    blocked_target.mkdir()

    failed = _run(
        tmp_path,
        sandbox,
        manifest,
        run_id="fs-failure",
        state_root=state_root,
        test_material_write_path=blocked_target,
    )
    assert failed.returncode != 0
    assert "INCOMPLETE_STORAGE_FAILURE" in failed.stdout + failed.stderr
    state = json.loads(_lifecycle_state_file(state_root).read_text(encoding="utf-8"))
    assert state["execution_state"] == "INCOMPLETE_STORAGE_FAILURE"
    assert blocked_target.is_dir()

    retry = _run(tmp_path, sandbox, manifest, run_id="retry", state_root=state_root)

    assert retry.returncode != 0
    assert "PREVIOUS_TRIAL_INCOMPLETE" in retry.stdout + retry.stderr


def test_capacity_gate_refuses_before_material_write(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    result = _run(
        tmp_path,
        sandbox,
        manifest,
        "-FreeNowBytes",
        "100",
        "-NextOperationPeakBytes",
        "10",
        "-RemainingPeakAfterOperationBytes",
        "20",
        "-RecoveryReserveBytes",
        "30",
        "-SafetyReserveBytes",
        "4294967296",
    )

    assert result.returncode != 0
    assert "CAPACITY_INSUFFICIENT" in result.stdout + result.stderr


def test_capacity_zero_is_a_valid_numeric_measurement(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    result = _run(tmp_path, sandbox, manifest, "-FreeNowBytes", "0")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "CAPACITY_GATE=PASS" in result.stdout
    assert "CAPACITY_FREE_NOW_BYTES=0" in result.stdout


def test_capacity_invalid_source_fails_closed(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    result = subprocess.run(
        _capacity_probe_command("not-an-absolute-filesystem-path"),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode != 0
    assert "CAPACITY_MEASUREMENT_ERROR" in result.stdout + result.stderr


@pytest.mark.skipif(
    shutil.which("powershell.exe") is None and shutil.which("powershell") is None,
    reason="Windows PowerShell is required",
)
def test_nested_powershell_capacity_measurement_uses_same_volume_authority(
    tmp_path: Path,
) -> None:
    wrapper = tmp_path / "outer-capacity-probe.ps1"
    wrapper.write_text(
        """param([string]$GuardPath, [string]$ProbePath)
$ErrorActionPreference = 'Stop'
$outer = & $GuardPath -Mode F5Only -ExistingSandboxPath $ProbePath -RunId outer-capacity -InputManifestPath $GuardPath -CapacityProbeOnly -CapacityProbePath $ProbePath
$outer | ForEach-Object { 'OUTER:' + $_ }
$nested = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $GuardPath -Mode F5Only -ExistingSandboxPath $ProbePath -RunId nested-capacity -InputManifestPath $GuardPath -CapacityProbeOnly -CapacityProbePath $ProbePath
$nested | ForEach-Object { 'NESTED:' + $_ }
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
""",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    result = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(wrapper),
            str(GUARD),
            str(REPO),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    outer_free = next(line for line in lines if line.startswith("OUTER:CAPACITY_FREE_NOW_BYTES="))
    nested_free = next(line for line in lines if line.startswith("NESTED:CAPACITY_FREE_NOW_BYTES="))
    outer_root = next(line for line in lines if line.startswith("OUTER:CAPACITY_VOLUME_ROOT="))
    nested_root = next(line for line in lines if line.startswith("NESTED:CAPACITY_VOLUME_ROOT="))
    assert int(outer_free.split("=", 1)[1]) > 0
    assert int(nested_free.split("=", 1)[1]) > 0
    assert outer_root.split("=", 1)[1] == nested_root.split("=", 1)[1]
    assert "OUTER:CAPACITY_MEASUREMENT_STATUS=PASS" in lines
    assert "NESTED:CAPACITY_MEASUREMENT_STATUS=PASS" in lines


def test_simulated_storage_failure_terminalizes_without_retry(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    result = _run(
        tmp_path,
        sandbox,
        manifest,
        "-SimulateStorageFailure",
        state_root=tmp_path / "state",
    )

    assert result.returncode != 0
    assert "INCOMPLETE_STORAGE_FAILURE" in result.stdout + result.stderr
    state_files = list((tmp_path / "state").rglob("lifecycle_state.json"))
    assert len(state_files) == 1
    state = json.loads(state_files[0].read_text(encoding="utf-8"))
    assert state["execution_state"] == "INCOMPLETE_STORAGE_FAILURE"


def test_real_route_is_refused_by_guard_work_order(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    result = _run_without_dry_run(
        tmp_path,
        sandbox,
        manifest,
        "-NextOperationPeakBytes",
        "1",
        "-RemainingPeakAfterOperationBytes",
        "1",
    )

    assert result.returncode != 0
    assert "REAL_F5_REQUIRES_AO_04_C3_F5_01" in result.stdout + result.stderr


def test_second_trial_is_blocked_by_exclusive_lock(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    global_lock_path = tmp_path / "global.lock"
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    first = subprocess.Popen(
        _command(
            tmp_path,
            sandbox,
            manifest,
            "-HoldLockSeconds",
            "3",
            global_lock_path=global_lock_path,
        ),
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    try:
        time.sleep(0.7)
        second = _run(tmp_path, sandbox, manifest)
        assert second.returncode != 0
        assert "CONCURRENT_TRIAL_BLOCKED" in second.stdout + second.stderr
    finally:
        first_stdout, first_stderr = first.communicate(timeout=10)
        assert first.returncode == 0, first_stdout + first_stderr


def test_probe_f5_only_dry_run_never_enters_generic_setup(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    result = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PROBE),
            "-Mode",
            "F5Only",
            "-ExistingSandboxPath",
            str(sandbox),
            "-RunId",
            "probe-test",
            "-InputManifestPath",
            str(manifest),
        "-DryRun",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "F5_ONLY_ROUTE_SELECTED" in result.stdout
    assert "GENERIC_SETUP_EXECUTED=NO" in result.stdout
    assert "RUNTIME_COPY_EXECUTED=NO" in result.stdout
    assert "F5_EXECUTED=NO" in result.stdout


def test_probe_f5_only_real_requires_guard_context(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    result = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PROBE),
            "-Mode",
            "F5Only",
            "-ExecutionMode",
            "RealF5",
            "-ExistingSandboxPath",
            str(sandbox),
            "-RunId",
            "probe-real-no-context",
            "-InputManifestPath",
            str(manifest),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "EXECUTION_CONTEXT_REQUIRED" in result.stdout + result.stderr


def test_probe_f5_only_invalid_context_refused(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    context = tmp_path / "invalid-context.json"
    context.write_text("{}\n", encoding="utf-8")
    result = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PROBE),
            "-Mode",
            "F5Only",
            "-ExecutionMode",
            "RealF5",
            "-ExecutionContextPath",
            str(context),
            "-ExistingSandboxPath",
            str(sandbox),
            "-RunId",
            "probe-invalid-context",
            "-InputManifestPath",
            str(manifest),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "EXECUTION_CONTEXT_INVALID" in result.stdout + result.stderr


@WINDOWS_REALF5_PROBE_ONLY
def test_guarded_real_dispatch_boundary_uses_existing_sandbox_only(tmp_path: Path) -> None:
    sandbox, marker = _sandbox(tmp_path)
    _canonical_layout(sandbox)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    result = _run_guarded_real(tmp_path, sandbox, manifest)

    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout + result.stderr
    assert "GUARDED_EXECUTION_CONTEXT=PASS" in output
    assert "CANONICAL_F5_TEST_CHECKPOINT=PASS" in output
    assert "WOULD_ENTER_REAL_F5_ROUTE=YES" not in output
    assert "REAL_F5_EXECUTED=NO" in output
    assert "NEW_RUNTIME_COPY=0" in output
    assert "NEW_SANDBOX=NO" in output
    assert marker.read_bytes() == b"runtime"
    assert not (tmp_path / "evidence" / "trials").exists()
    state = json.loads(_lifecycle_state_file(tmp_path / "state").read_text(encoding="utf-8"))
    assert state["execution_state"] == "COMPLETED"
    assert (tmp_path / "evidence" / "F5_EXECUTION_CONTEXT.json").is_file()


@WINDOWS_REALF5_PROBE_ONLY
def test_guarded_real_dispatch_replaces_existing_execution_context(tmp_path: Path) -> None:
    sandbox, marker = _sandbox(tmp_path)
    _canonical_layout(sandbox)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    context_path = evidence_root / "F5_EXECUTION_CONTEXT.json"
    context_path.write_text('{"stale": true}\n', encoding="utf-8")

    result = _run_guarded_real(
        tmp_path,
        sandbox,
        manifest,
        evidence_root=evidence_root,
        context_path=context_path,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    context = json.loads(context_path.read_text(encoding="utf-8"))
    assert context["schema"] == "AO-04-C3-F5-EXECUTION-CONTEXT-V1"
    assert context["run_id"] == "real-test"
    assert context["lifecycle_state"] == "RUNNING"
    assert list(evidence_root.glob(f"{context_path.name}.*.tmp")) == []
    assert list(evidence_root.glob(f"{context_path.name}.*.backup")) == []
    output = result.stdout + result.stderr
    assert "GUARDED_EXECUTION_CONTEXT=PASS" in output
    assert "REAL_F5_EXECUTED=NO" in output
    assert marker.read_bytes() == b"runtime"


@WINDOWS_REALF5_PROBE_ONLY
def test_f5only_canonical_failure_propagates_to_guard(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    _canonical_layout(sandbox)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    command = _guarded_real_command(
        tmp_path,
        sandbox,
        manifest,
        run_id="canonical-failure",
        state_root=tmp_path / "state",
        evidence_root=tmp_path / "evidence",
    )
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    environment["QI_CRAWLER_F5_TEST_CANONICAL_FAILURE"] = "1"

    result = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode != 0
    assert "CANONICAL_F5_ROUTE_ENTERED=YES" in result.stdout + result.stderr
    assert "F5_PROBE_FAILED" in result.stdout + result.stderr
    state = json.loads(_lifecycle_state_file(tmp_path / "state").read_text(encoding="utf-8"))
    assert state["execution_state"] == "FAILED"


@WINDOWS_REALF5_PROBE_ONLY
def test_guarded_real_path_reaches_canonical_f5_checkpoint(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    _canonical_layout(sandbox)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)

    result = _run_guarded_real(tmp_path, sandbox, manifest)

    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout + result.stderr
    assert "CANONICAL_F5_TEST_CHECKPOINT=PASS" in output
    assert "WOULD_ENTER_REAL_F5_ROUTE=YES" not in output


def test_probe_defines_one_canonical_f5_function() -> None:
    source = PROBE.read_text(encoding="utf-8")
    assert source.count("function Invoke-F5CanonicalRoute") == 1


def test_sequential_and_f5only_call_the_same_canonical_route() -> None:
    source = PROBE.read_text(encoding="utf-8")
    marker = "function Invoke-F5CanonicalRoute"
    canonical_start = source.find(marker)
    assert canonical_start >= 0
    calls = [index for index in range(len(source)) if source.startswith("Invoke-F5CanonicalRoute", index)]
    assert len(calls) >= 3
    assert any(index < canonical_start for index in calls) is False
    assert any(index > canonical_start for index in calls)
    assert "Mode -eq 'F5Only'" in source
    assert "Mode -eq 'Sequential'" in source or "Sequential" in source
    f5only_start = source.index("if ($f5OnlyRoute)")
    sequential_start = source.index("$trialId='AO04-C2-F5-'")
    f5only_dispatch = source[f5only_start:sequential_start]
    assert "Invoke-F5CanonicalRoute" in f5only_dispatch
    assert "New-Trial" not in f5only_dispatch
    assert "Copy-Item" not in f5only_dispatch
    assert "NEW_SANDBOX=NO" in f5only_dispatch
    assert "SEQUENTIAL_FALLBACK=NO" in f5only_dispatch


@WINDOWS_REALF5_PROBE_ONLY
@pytest.mark.parametrize(
    ("field", "replacement", "expected"),
    [
        ("canonical_sandbox_path", "wrong-sandbox", "canonical_sandbox_path"),
        ("input_manifest_path", "wrong-manifest.json", "input_manifest_path"),
        ("guard_identity_sha256", "0" * 64, "GUARD_IDENTITY"),
        ("probe_identity_sha256", "0" * 64, "PROBE_IDENTITY"),
        ("run_id", "wrong-run", "RUN_ID"),
        ("lifecycle_state", "COMPLETED", "LIFECYCLE_STATE"),
    ],
)
def test_guarded_context_drift_is_refused(
    tmp_path: Path, field: str, replacement: str, expected: str
) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"
    evidence_root = tmp_path / "evidence"
    generated = _run_guarded_real(
        tmp_path,
        sandbox,
        manifest,
        state_root=state_root,
        evidence_root=evidence_root,
    )
    assert generated.returncode == 0, generated.stdout + generated.stderr
    context_path = evidence_root / "F5_EXECUTION_CONTEXT.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    if field == "canonical_sandbox_path" or field == "input_manifest_path":
        context[field] = str(tmp_path / replacement)
    else:
        context[field] = replacement
    context_path.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
    state_path = _lifecycle_state_file(state_root)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["execution_state"] = "RUNNING"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    result = subprocess.run(
        _probe_real_command(sandbox, manifest, context_path, state_root, evidence_root),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode != 0
    assert expected in result.stdout + result.stderr


@WINDOWS_REALF5_PROBE_ONLY
def test_direct_probe_refuses_when_lifecycle_is_not_running(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"
    evidence_root = tmp_path / "evidence"
    generated = _run_guarded_real(
        tmp_path,
        sandbox,
        manifest,
        state_root=state_root,
        evidence_root=evidence_root,
    )
    assert generated.returncode == 0, generated.stdout + generated.stderr
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    result = subprocess.run(
        _probe_real_command(
            sandbox,
            manifest,
            evidence_root / "F5_EXECUTION_CONTEXT.json",
            state_root,
            evidence_root,
        ),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert result.returncode != 0
    assert "LIFECYCLE_STATE" in result.stdout + result.stderr


@WINDOWS_REALF5_PROBE_ONLY
def test_direct_probe_refuses_without_outer_lock(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"
    evidence_root = tmp_path / "evidence"
    generated = _run_guarded_real(
        tmp_path,
        sandbox,
        manifest,
        state_root=state_root,
        evidence_root=evidence_root,
    )
    assert generated.returncode == 0, generated.stdout + generated.stderr
    state_path = _lifecycle_state_file(state_root)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["execution_state"] = "RUNNING"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    result = subprocess.run(
        _probe_real_command(
            sandbox,
            manifest,
            evidence_root / "F5_EXECUTION_CONTEXT.json",
            state_root,
            evidence_root,
        ),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert result.returncode != 0
    assert "LOCK_NOT_HELD" in result.stdout + result.stderr


@WINDOWS_REALF5_PROBE_ONLY
def test_guarded_real_dispatch_keeps_outer_lock_held(tmp_path: Path) -> None:
    sandbox, _ = _sandbox(tmp_path)
    input_path = tmp_path / "controller.ps1"
    input_path.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, input_path)
    state_root = tmp_path / "state"
    evidence_root = tmp_path / "evidence"
    environment = os.environ.copy()
    environment["QI_CRAWLER_F5_TEST_MODE"] = "1"
    first = subprocess.Popen(
        _guarded_real_command(
            tmp_path,
            sandbox,
            manifest,
            run_id="lock-holder",
            state_root=state_root,
            evidence_root=evidence_root,
            dispatch_hold_seconds=3,
        ),
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    try:
        _wait_for_running_lifecycle(
            state_root,
            run_id="lock-holder",
            sandbox=sandbox,
        )
        second = _run_guarded_real(
            tmp_path,
            sandbox,
            manifest,
            run_id="lock-contender",
            state_root=state_root,
            evidence_root=tmp_path / "evidence-second",
        )
        assert second.returncode != 0
        assert "CONCURRENT_TRIAL_BLOCKED" in second.stdout + second.stderr
        state_during_contender = json.loads(
            _lifecycle_state_file(state_root).read_text(encoding="utf-8")
        )
        assert state_during_contender["last_run_id"] == "lock-holder"
        assert state_during_contender["execution_state"] == "RUNNING"
    finally:
        first_stdout, first_stderr = first.communicate(timeout=15)
        assert first.returncode == 0, first_stdout + first_stderr


@pytest.mark.skipif(
    sys.platform != "win32" or shutil.which("powershell.exe") is None,
    reason="Windows PowerShell Job Object positive control",
)
def test_job_object_positive_control_keeps_outer_process_and_lock(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(JOB_HELPER),
            "-Mode",
            "PositiveControl",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "JOB_ACTIVE_COUNT_BEFORE=1" in result.stdout
    assert "JOB_ACTIVE_COUNT_AFTER=0" in result.stdout
    assert "OUTER_ALIVE=YES" in result.stdout
    assert "LOCK_SURVIVES_JOB_KILL=YES" in result.stdout
