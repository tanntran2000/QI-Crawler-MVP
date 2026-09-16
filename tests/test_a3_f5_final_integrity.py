"""Native, disposable controls for the canonical A3 F5 integrity seams."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.release.a3_process_observer import F5_CANONICAL_REQUIRED_GATES

REPO = Path(__file__).resolve().parents[1]
BOUNDED_IO = REPO / "tools" / "release" / "a3_f5_bounded_io.ps1"
PROBE = REPO / "tools" / "release" / "a3_probe_windows.ps1"
SYNTHETIC_ROUTE = REPO / "tests" / "a3_f5_synthetic_route.ps1"


def _ps(value: Path | str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _run(script: str) -> subprocess.CompletedProcess[str]:
    powershell = shutil.which("powershell.exe")
    if powershell is None or sys.platform != "win32":
        pytest.skip("Native Windows PowerShell 5.1 is required")
    return subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _probe_functions() -> str:
    return f"""
$source = Get-Content -Raw -LiteralPath {_ps(PROBE)}
$tokens=$null; $parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$parseErrors)
if (@($parseErrors).Count -ne 0) {{ throw 'PROBE_PARSE_FAILED' }}
foreach($function in @($ast.FindAll({{param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]}},$true))) {{
    . ([scriptblock]::Create($function.Extent.Text))
}}
"""


_FAILURE_ARTIFACT_MAX_BYTES = 256 * 1024
_FAILURE_ARTIFACT_NAMES = (
    "a3_synthetic_failure_core.json",
    "a3_synthetic_gate_inputs.json",
    "a3_synthetic_aggregates.json",
    "a3_synthetic_route_failures.json",
)


def _read_json_or_missing(path: Path) -> object:
    if not path.is_file():
        return "MISSING"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "MISSING"


def _bounded_text(value: object, limit: int = 32 * 1024) -> object:
    if value == "MISSING" or value is None:
        return "MISSING"
    text = str(value)
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    return encoded[:limit].decode("utf-8", errors="replace") + "...[TRUNCATED]"


def _classify_synthetic_failure(
    core: object,
    *,
    positive_exit_code: object,
    negative_control_pass: object,
) -> dict[str, object]:
    if not isinstance(core, dict):
        return {
            "classification": "VERDICT_EVIDENCE_MISSING",
            "failed_or_non_true_gates": ["MISSING"],
        }
    gates = core.get("mandatory_gates")
    if not isinstance(gates, dict):
        return {
            "classification": "VERDICT_EVIDENCE_MISSING",
            "failed_or_non_true_gates": ["MISSING"],
        }
    failed = sorted(str(name) for name, value in gates.items() if value is not True)
    if failed:
        classification = "MANDATORY_GATE_HOLD"
    elif positive_exit_code == "MISSING" or negative_control_pass == "MISSING":
        classification = "VERDICT_EVIDENCE_MISSING"
    elif positive_exit_code != 0:
        classification = "POSITIVE_AGGREGATE_EXECUTION_FAILURE"
    elif negative_control_pass is not True:
        classification = "NEGATIVE_CONTROL_FAILURE"
    else:
        classification = "UNKNOWN_FAILURE"
    return {
        "classification": classification,
        "failed_or_non_true_gates": failed or ["NONE"],
    }


def _project_aggregate(value: object) -> object:
    if not isinstance(value, dict):
        return "MISSING"
    return {
        "exit_code": value.get("exit_code", "MISSING"),
        "stdout": _bounded_text(value.get("stdout", "MISSING")),
        "stderr": _bounded_text(value.get("stderr", "MISSING")),
    }


def _project_route(value: object) -> object:
    if not isinstance(value, dict):
        return "MISSING"
    process_result = value.get("process_result")
    if not isinstance(process_result, dict):
        process_result = {}
    tree = value.get(
        "process_tree_evidence",
        process_result.get("process_tree_evidence", "MISSING"),
    )
    if isinstance(tree, dict):
        tree = {
            "ids": tree.get("ids", "MISSING"),
            "enumeration_status": tree.get("enumeration_status", "MISSING"),
            "descendant_discovery_status": tree.get(
                "descendant_discovery_status", "MISSING"
            ),
            "root_pid_status": tree.get("root_pid_status", "MISSING"),
            "unresolved_descendants": tree.get("unresolved_descendants", "MISSING"),
            "rejected_parent_edges": tree.get("rejected_parent_edges", "MISSING"),
        }
    return {
        "trial_id": value.get("trial_id", "MISSING"),
        "route_type": value.get("route_type", "MISSING"),
        "route_kind": value.get("route_kind", "MISSING"),
        "result": value.get("result", "MISSING"),
        "launcher_pid": value.get("launcher_pid", process_result.get("launcher_pid", "MISSING")),
        "launcher_identity": value.get("launcher_identity", "MISSING"),
        "observed_job_pids": value.get("observed_job_pids", process_result.get("observed_job_pids", "MISSING")),
        "total_job_processes": value.get("total_job_processes", process_result.get("total_job_processes", "MISSING")),
        "active_after": value.get("active_after", process_result.get("active_after", "MISSING")),
        "launcher_exit_code": value.get("launcher_exit_code", process_result.get("launcher_exit_code", "MISSING")),
        "process_tree_evidence": tree,
    }


def _retain_synthetic_failure_evidence(
    run_root: Path,
    result: subprocess.CompletedProcess[str],
    *,
    destination: Path | None = None,
) -> tuple[Path, ...]:
    """Retain only four small diagnostics when the canonical rehearsal fails."""
    if result.returncode == 0:
        return ()
    if destination is None:
        ci_root = os.environ.get("CI_TEST_ROOT")
        if not ci_root:
            return ()
        destination = Path(ci_root).resolve() / "evidence"
    destination.mkdir(parents=True, exist_ok=True)
    source = Path(run_root) / "evidence" / "f5" / "synthetic-A"
    core = _read_json_or_missing(source / "probe_verdict_core.json")
    gate_inputs = _read_json_or_missing(source / "gate_inputs.json")
    positive = _read_json_or_missing(source / "aggregate_positive.process.json")
    negative = _read_json_or_missing(source / "aggregate_negative.process.json")
    if isinstance(core, dict):
        gates = core.get("mandatory_gates", "MISSING")
        positive_exit = core.get("positive_exit_code", "MISSING")
        negative_pass = core.get("negative_control_pass", "MISSING")
    else:
        gates = "MISSING"
        positive_exit = "MISSING"
        negative_pass = "MISSING"
    diagnostic = _classify_synthetic_failure(
        core,
        positive_exit_code=positive_exit,
        negative_control_pass=negative_pass,
    )
    if isinstance(gate_inputs, dict):
        gate_payload: object = {
            "trial_id": core.get("trial_id", "MISSING") if isinstance(core, dict) else "MISSING",
            "gate_contract": gate_inputs.get("gate_contract", "MISSING"),
            "mandatory_gates": gate_inputs.get("mandatory_gates", gates),
            "failed_or_non_true_gates": diagnostic["failed_or_non_true_gates"],
        }
    else:
        gate_payload = "MISSING"
    route_files = sorted((source / "receipts").glob("P4_*.json"))
    route_payload: object = (
        [_project_route(_read_json_or_missing(path)) for path in route_files]
        if route_files
        else "MISSING"
    )
    core_payload = {
        "trial_id": core.get("trial_id", "MISSING") if isinstance(core, dict) else "MISSING",
        "final_probe_result": core.get("final_probe_result", "MISSING") if isinstance(core, dict) else "MISSING",
        "mandatory_gates": gates,
        "positive_exit_code": positive_exit,
        "negative_control_pass": negative_pass,
        "failed_or_non_true_gates": diagnostic["failed_or_non_true_gates"],
        "diagnostic_classification": diagnostic["classification"],
        "subprocess_stdout": _bounded_text(getattr(result, "stdout", "MISSING")),
        "subprocess_stderr": _bounded_text(getattr(result, "stderr", "MISSING")),
    }
    aggregate_payload = {
        "trial_id": core.get("trial_id", "MISSING") if isinstance(core, dict) else "MISSING",
        "positive": _project_aggregate(positive),
        "negative": _project_aggregate(negative),
        "positive_exit_code": (
            positive.get("exit_code", "MISSING") if isinstance(positive, dict) else "MISSING"
        ),
        "positive_stdout": (
            _bounded_text(positive.get("stdout", "MISSING"))
            if isinstance(positive, dict)
            else "MISSING"
        ),
        "positive_stderr": (
            _bounded_text(positive.get("stderr", "MISSING"))
            if isinstance(positive, dict)
            else "MISSING"
        ),
        "negative_exit_code": (
            negative.get("exit_code", "MISSING") if isinstance(negative, dict) else "MISSING"
        ),
        "negative_stdout": (
            _bounded_text(negative.get("stdout", "MISSING"))
            if isinstance(negative, dict)
            else "MISSING"
        ),
        "negative_stderr": (
            _bounded_text(negative.get("stderr", "MISSING"))
            if isinstance(negative, dict)
            else "MISSING"
        ),
        "negative_control_pass": negative_pass,
    }
    payloads = (core_payload, gate_payload, aggregate_payload, {
        "trial_id": core.get("trial_id", "MISSING") if isinstance(core, dict) else "MISSING",
        "route_failures": route_payload,
    })
    retained: list[Path] = []
    for name, payload in zip(_FAILURE_ARTIFACT_NAMES, payloads, strict=True):
        path = destination / name
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if len(text.encode("utf-8")) > _FAILURE_ARTIFACT_MAX_BYTES:
            text = json.dumps(
                {
                    "diagnostic_classification": diagnostic["classification"],
                    "failed_or_non_true_gates": diagnostic["failed_or_non_true_gates"],
                    "diagnostic_status": "BOUNDED_TRUNCATED",
                },
                indent=2,
                sort_keys=True,
            ) + "\n"
        temporary = path.with_name(path.name + ".tmp")
        try:
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()
        retained.append(path)
    return tuple(retained)


def test_p1_zero_byte_marker_is_bounded_but_null_and_overlimit_fail(tmp_path: Path) -> None:
    marker = tmp_path / "continue-A3-F4"
    null_target = tmp_path / "null"
    over_target = tmp_path / "over"
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
Initialize-F5BoundedIo -Limits @{{TX_STATE=@{{max_file_count=1;max_per_file_bytes=1;max_aggregate_bytes=1;max_atomic_overlap_bytes=1}}}}
Write-F5BoundedText -Path {_ps(marker)} -Text '' -WriteClass TX_STATE
$nullRejected=$false
try {{ Write-F5BoundedBytes -Path {_ps(null_target)} -Bytes $null -WriteClass TX_STATE }} catch {{ $nullRejected=$true }}
$overRejected=$false
try {{ Write-F5BoundedBytes -Path {_ps(over_target)} -Bytes ([byte[]]@(65,66)) -WriteClass TX_STATE }} catch {{ $overRejected=$true }}
$usage=Get-F5BoundedIoUsage
if (-not $nullRejected -or -not $overRejected -or $usage.TX_STATE.file_count -ne 1) {{ throw 'BOUNDARY_FAIL' }}
'P1_ZERO_BYTE_MARKER=PASS'
"""
    result = _run(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "P1_ZERO_BYTE_MARKER=PASS" in result.stdout
    assert marker.is_file() and marker.stat().st_size == 0
    assert not null_target.exists() and not over_target.exists()


@pytest.mark.parametrize("directory", ["route with spaces", "route_plain"])
def test_canonical_cmd_launcher_preserves_path_arguments_and_exit(
    tmp_path: Path, directory: str
) -> None:
    route_dir = tmp_path / directory
    route_dir.mkdir()
    command = route_dir / "synthetic route.cmd"
    command.write_text(
        '@echo off\r\nif not "%~1"=="two words" exit /b 9\r\nexit /b 17\r\n',
        encoding="ascii",
    )
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
$process=Start-F5CommandArtifact -Path {_ps(command)} -Arguments @('two words') -WorkingDirectory {_ps(route_dir)}
if (-not $process.WaitForExit(10000)) {{ throw 'CMD_TIMEOUT' }}
'EXIT=' + $process.ExitCode
"""
    result = _run(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EXIT=17" in result.stdout


def test_recovery_expected_barrier_refusal_is_bound_to_trial_and_final_identity(
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "QI-Crawler.exe"
    canonical.write_bytes(b"synthetic stub")
    stub_sha = hashlib.sha256(canonical.read_bytes()).hexdigest()
    observer = tmp_path / "P3.json"
    observer.write_text(json.dumps({"trial_id": "trial-A", "legacy_zero_proven": True}), encoding="utf-8")
    process = tmp_path / "recovery-process.json"
    process.write_text(
        json.dumps({
            "exit_code": 2,
            "trial_id": "trial-A",
            "stdout": json.dumps({"status": "MAINTENANCE_RECOVERY_REQUIRED", "mutated": False}),
            "stderr": "",
        }), encoding="utf-8",
    )
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
{_probe_functions()}
$dbBefore=@{{files=@(@{{name='egp.db';sha256='abc';size_bytes=10}})}}
$dbAfter=@{{files=@(@{{name='egp.db';sha256='abc';size_bytes=10}})}}
$logicalBefore=@{{sha256='digest';revision='0020_add_tender_operational_revision_events'}}
$logicalAfter=@{{sha256='digest';revision='0020_add_tender_operational_revision_events'}}
[void](Assert-F5MaintenanceRecovery -EvidenceRoot {_ps(tmp_path)} -SandboxRoot {_ps(tmp_path)} -TrialId 'trial-A' -ProcessReceiptPath {_ps(process)} -ObserverReceiptPath {_ps(observer)} -CanonicalPath {_ps(canonical)} -ExpectedStubSha256 '{stub_sha}' -DbBefore $dbBefore -DbAfter $dbAfter -LogicalBefore $logicalBefore -LogicalAfter $logicalAfter -ExpectedSchema '0020_add_tender_operational_revision_events')
'RECOVERY_BINDING=PASS'
"""
    result = _run(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RECOVERY_BINDING=PASS" in result.stdout


def test_shortcut_budget_rejection_creates_no_file(tmp_path: Path) -> None:
    shortcut = tmp_path / "route.lnk"
    target = tmp_path / "stub.exe"
    target.write_bytes(b"synthetic")
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
{_probe_functions()}
Initialize-F5BoundedIo -Limits @{{ROUTE_ARTIFACTS=@{{max_file_count=1;max_per_file_bytes=128;max_aggregate_bytes=128;max_atomic_overlap_bytes=128}}}}
$rejected=$false
try {{ Write-F5BoundedShortcut -Path {_ps(shortcut)} -TargetPath {_ps(target)} -Root {_ps(tmp_path)} }} catch {{ $rejected=($_.Exception.Message -match 'MATERIAL_WRITE_BOUND_EXCEEDED') }}
if (-not $rejected -or (Test-Path -LiteralPath {_ps(shortcut)}) -or (Test-Path -LiteralPath {_ps(shortcut.with_name(shortcut.name + '.bounded.tmp.lnk'))})) {{ throw 'BUDGET_PREWRITE_FAILED' }}
'SHORTCUT_BUDGET_PREWRITE=PASS'
"""
    result = _run(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SHORTCUT_BUDGET_PREWRITE=PASS" in result.stdout


def test_shortcut_is_persisted_only_after_bounded_precheck(tmp_path: Path) -> None:
    shortcut = tmp_path / "route with spaces.lnk"
    target = tmp_path / "stub.exe"
    target.write_bytes(b"synthetic")
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
{_probe_functions()}
Initialize-F5BoundedIo -Limits @{{ROUTE_ARTIFACTS=@{{max_file_count=1;max_per_file_bytes=8192;max_aggregate_bytes=8192;max_atomic_overlap_bytes=8192}}}}
$resolved=Write-F5BoundedShortcut -Path {_ps(shortcut)} -TargetPath {_ps(target)} -Root {_ps(tmp_path)}
$usage=Get-F5BoundedIoUsage
if ($resolved -ne {_ps(target)} -or $usage.ROUTE_ARTIFACTS.file_count -ne 1 -or $usage.ROUTE_ARTIFACTS.aggregate_bytes -lt 1) {{ throw 'SHORTCUT_BOUNDED_POSITIVE_FAIL' }}
'SHORTCUT_BOUNDED_POSITIVE=PASS'
"""
    result = _run(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SHORTCUT_BOUNDED_POSITIVE=PASS" in result.stdout
    assert shortcut.is_file()
    assert not shortcut.with_name(shortcut.name + ".bounded.tmp.lnk").exists()


def test_shortcut_write_exception_leaves_no_partial_or_final_file(tmp_path: Path) -> None:
    shortcut = tmp_path / "route.lnk"
    temporary = shortcut.with_name(shortcut.name + ".bounded.tmp.lnk")
    target = tmp_path / "stub.exe"
    target.write_bytes(b"synthetic")
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
{_probe_functions()}
Initialize-F5BoundedIo -Limits @{{ROUTE_ARTIFACTS=@{{max_file_count=1;max_per_file_bytes=8192;max_aggregate_bytes=8192;max_atomic_overlap_bytes=8192}}}}
function New-Object {{
    [IO.File]::WriteAllText({_ps(temporary)},'partial')
    throw 'SYNTHETIC_COM_WRITE_FAILURE'
}}
$rejected=$false
try {{ Write-F5BoundedShortcut -Path {_ps(shortcut)} -TargetPath {_ps(target)} -Root {_ps(tmp_path)} }} catch {{ $rejected=($_.Exception.Message -match 'SYNTHETIC_COM_WRITE_FAILURE') }}
if (-not $rejected) {{ throw 'SHORTCUT_FAILURE_NOT_PROPAGATED' }}
'SHORTCUT_FAILURE=HELD'
"""
    result = _run(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SHORTCUT_FAILURE=HELD" in result.stdout
    assert not shortcut.exists() and not temporary.exists()


def test_manifest_is_verified_after_write_and_tamper_is_rejected(tmp_path: Path) -> None:
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    p1 = receipts / "P1.json"
    p1.write_text('{"trial_id":"trial-A"}\n', encoding="utf-8")
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
{_probe_functions()}
Initialize-F5BoundedIo -Limits @{{EVIDENCE_META=@{{max_file_count=4;max_per_file_bytes=8388608;max_aggregate_bytes=16777216;max_atomic_overlap_bytes=8388608}}}}
$result=New-EvidenceManifest -Root {_ps(tmp_path)} -TrialId 'trial-A' -RequiredPaths @('receipts/P1.json')
if (-not $result.verified) {{ throw 'MANIFEST_NOT_VERIFIED' }}
$tamper={_ps(p1)}
[IO.File]::AppendAllText($tamper,'x')
$rejected=$false
try {{ [void](Assert-F5EvidenceManifest -Root {_ps(tmp_path)} -ManifestPath $result.path -TrialId 'trial-A' -RequiredPaths @('receipts/P1.json')) }} catch {{ $rejected=$true }}
if (-not $rejected) {{ throw 'MANIFEST_TAMPER_ACCEPTED' }}
'MANIFEST_ORDER=PASS'
"""
    result = _run(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MANIFEST_ORDER=PASS" in result.stdout


@pytest.mark.parametrize(
    "fault",
    ["nonzero_exit", "missing_receipt", "malformed_receipt", "wrong_run_id", "wrong_process_run_id",
     "physical_db_drift", "logical_db_drift", "wrong_schema", "wrong_stub"],
)
def test_recovery_faults_cannot_validate(tmp_path: Path, fault: str) -> None:
    canonical = tmp_path / "QI-Crawler.exe"
    canonical.write_bytes(b"synthetic stub")
    stub_sha = hashlib.sha256(canonical.read_bytes()).hexdigest()
    observer = tmp_path / "P3.json"
    observer.write_text(
        json.dumps({"trial_id": "wrong" if fault == "wrong_run_id" else "trial-A",
                    "legacy_zero_proven": True}), encoding="utf-8",
    )
    process = tmp_path / "recovery-process.json"
    if fault != "missing_receipt":
        process.write_text(
            "{" if fault == "malformed_receipt" else json.dumps({
                "exit_code": 1 if fault == "nonzero_exit" else 2,
                "trial_id": "wrong" if fault == "wrong_process_run_id" else "trial-A",
                "stdout": json.dumps({"status": "MAINTENANCE_RECOVERY_REQUIRED", "mutated": False}),
            }), encoding="utf-8",
        )
    db_after = "def" if fault == "physical_db_drift" else "abc"
    logical_after = "other" if fault == "logical_db_drift" else "digest"
    schema_after = "0022_wrong" if fault == "wrong_schema" else "0020_add_tender_operational_revision_events"
    expected_stub = "0" * 64 if fault == "wrong_stub" else stub_sha
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
{_probe_functions()}
$dbBefore=@{{files=@(@{{name='egp.db';sha256='abc';size_bytes=10}})}}
$dbAfter=@{{files=@(@{{name='egp.db';sha256='{db_after}';size_bytes=10}})}}
$logicalBefore=@{{sha256='digest';revision='0020_add_tender_operational_revision_events'}}
$logicalAfter=@{{sha256='{logical_after}';revision='{schema_after}'}}
[void](Assert-F5MaintenanceRecovery -EvidenceRoot {_ps(tmp_path)} -SandboxRoot {_ps(tmp_path)} -TrialId 'trial-A' -ProcessReceiptPath {_ps(process)} -ObserverReceiptPath {_ps(observer)} -CanonicalPath {_ps(canonical)} -ExpectedStubSha256 '{expected_stub}' -DbBefore $dbBefore -DbAfter $dbAfter -LogicalBefore $logicalBefore -LogicalAfter $logicalAfter -ExpectedSchema '0020_add_tender_operational_revision_events')
'AGGREGATE_PASS'
"""
    result = _run(script)
    assert result.returncode != 0
    assert "AGGREGATE_PASS" not in result.stdout


@pytest.mark.parametrize("fault", ["missing", "truncated", "malformed", "missing_required", "sha_mismatch"])
def test_manifest_faults_cannot_validate(tmp_path: Path, fault: str) -> None:
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    (receipts / "P1.json").write_text('{"trial_id":"trial-A"}\n', encoding="utf-8")
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
{_probe_functions()}
Initialize-F5BoundedIo -Limits @{{EVIDENCE_META=@{{max_file_count=2;max_per_file_bytes=8388608;max_aggregate_bytes=16777216;max_atomic_overlap_bytes=8388608}}}}
$manifest=New-EvidenceManifest -Root {_ps(tmp_path)} -TrialId 'trial-A' -RequiredPaths @('receipts/P1.json')
switch ('{fault}') {{
    'missing' {{ Remove-Item -LiteralPath $manifest.path -Force }}
    'truncated' {{ [IO.File]::WriteAllText($manifest.path,'[') }}
    'malformed' {{ [IO.File]::WriteAllText($manifest.path,'not-json') }}
    'missing_required' {{ }}
    'sha_mismatch' {{ [IO.File]::AppendAllText({_ps(receipts / 'P1.json')},'x') }}
}}
[void](Assert-F5EvidenceManifest -Root {_ps(tmp_path)} -ManifestPath $manifest.path -TrialId 'trial-A' -RequiredPaths @($(if ('{fault}' -eq 'missing_required') {{ 'receipts/P2.json' }} else {{ 'receipts/P1.json' }})))
'AGGREGATE_PASS'
"""
    result = _run(script)
    assert result.returncode != 0
    assert "AGGREGATE_PASS" not in result.stdout


def test_manifest_write_budget_failure_has_no_completion_artifact(tmp_path: Path) -> None:
    (tmp_path / "receipt.json").write_text("{}", encoding="utf-8")
    script = f"""
$ErrorActionPreference='Stop'
. {_ps(BOUNDED_IO)}
{_probe_functions()}
Initialize-F5BoundedIo -Limits @{{EVIDENCE_META=@{{max_file_count=1;max_per_file_bytes=1;max_aggregate_bytes=1;max_atomic_overlap_bytes=1}}}}
[void](New-EvidenceManifest -Root {_ps(tmp_path)} -TrialId 'trial-A' -RequiredPaths @('receipt.json'))
'AGGREGATE_PASS'
"""
    result = _run(script)
    assert result.returncode != 0
    assert "AGGREGATE_PASS" not in result.stdout
    assert not (tmp_path / "evidence_manifest.json").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Native Windows Job route")
def test_synthetic_canonical_route_rehearsal(tmp_path: Path) -> None:
    """Exercise the on-disk canonical P0→P5 function with only disposable assets."""
    environment = os.environ.copy()
    environment.pop("QI_CRAWLER_DATA_DIR", None)
    # Refuse historical artifacts even on a developer machine where they exist.
    run_root = tmp_path / "one-run"
    command = (
        "function Resolve-Path { param($LiteralPath) "
        "if ($LiteralPath -like '*release_staging*') { throw 'HISTORICAL_ARTIFACT_FORBIDDEN' }; "
        "Microsoft.PowerShell.Management\\Resolve-Path -LiteralPath $LiteralPath }; "
        f"& {_ps(SYNTHETIC_ROUTE)} -Root {_ps(run_root)}"
    )
    result = subprocess.run(
        [shutil.which("powershell.exe") or "powershell.exe", "-NoProfile", "-NonInteractive",
         "-Command", command],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=180,
        env=environment,
        check=False,
    )
    if result.returncode != 0:
        _retain_synthetic_failure_evidence(run_root, result)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SYNTHETIC_AGGREGATE_VERDICT=PASS" in result.stdout


@pytest.mark.skipif(sys.platform != "win32", reason="Native Windows Job route")
@pytest.mark.parametrize("fault", [
    "p1_bound", "cmd_path", "cmd_exit", "p4_survivor", "p4_unknown",
    "budget", "manifest", "recovery", "recovery_missing", "db_mismatch",
])
def test_synthetic_canonical_fault_matrix_fails_closed(tmp_path: Path, fault: str) -> None:
    """One fault per disposable run through the same on-disk canonical route."""
    environment = os.environ.copy()
    environment.pop("QI_CRAWLER_DATA_DIR", None)
    result = subprocess.run(
        [shutil.which("powershell.exe") or "powershell.exe", "-NoProfile", "-NonInteractive",
         "-File", str(SYNTHETIC_ROUTE), "-Root", str(tmp_path / "one-run"), "-Fault", fault],
        cwd=REPO, capture_output=True, text=True, timeout=180, env=environment, check=False,
    )
    assert result.returncode != 0, (fault, result.stdout + result.stderr)
    assert "SYNTHETIC_AGGREGATE_VERDICT=PASS" not in result.stdout, fault
    assert "SYNTHETIC_FAULT_ANCHOR_INVALID" not in result.stdout + result.stderr, fault
    expected = {
        "p1_bound": "FAULT_P1_BOUND",
        "cmd_path": "FAULT_CMD_PATH",
        "cmd_exit": "FAULT_CMD_EXIT",
        "p4_survivor": "JOB_ROUTE_ACTIVE_TIMEOUT",
        "p4_unknown": "F5_CANONICAL_ROUTE_VERDICT_HOLD",
        "budget": "FAULT_BUDGET",
        "manifest": "F5_EVIDENCE_REQUIRED_ARTIFACT_MISSING",
        "recovery": "FAULT_RECOVERY",
        "recovery_missing": "F5_RECOVERY_EVIDENCE_MISSING",
        "db_mismatch": "F5_FINAL_DB_PHYSICAL_IDENTITY_MISMATCH",
    }
    assert expected[fault] in result.stdout + result.stderr, fault
    receipts = tmp_path / "one-run" / "evidence" / "f5" / "synthetic-A" / "receipts"
    p4_count = sum(not path.name.endswith("_FAIL.json") for path in receipts.glob("P4_*.json"))
    expected_p4 = 0 if fault == "p1_bound" else 3 if fault in {
        "cmd_path", "cmd_exit", "p4_survivor", "budget"
    } else 5
    assert p4_count == expected_p4, (fault, p4_count)


def test_canonical_route_declares_the_complete_f5_gate_contract() -> None:
    source = PROBE.read_text(encoding="utf-8")
    gate_line = next(line for line in source.splitlines() if line.startswith("$gates=[ordered]@{"))
    names = set(re.findall(r"(?<![-\w])([A-Za-z_]\w*)=", gate_line))
    names.discard("gates")
    assert names == F5_CANONICAL_REQUIRED_GATES


def test_final_receipt_keeps_same_gate_set_as_aggregate_input() -> None:
    source = PROBE.read_text(encoding="utf-8")
    after_input = source.split("$gateInput=Join-Path $f5Evidence 'gate_inputs.json'", 1)[1]
    before_core = after_input.split("$core=[ordered]@{", 1)[0]
    assert not re.search(r"\$gates\[[^]]+\]\s*=", before_core)


def test_failure_diagnostics_name_false_mandatory_gate() -> None:
    diagnostic = _classify_synthetic_failure(
        {"mandatory_gates": {"route_contract": False, "job_created": True}},
        positive_exit_code=2,
        negative_control_pass=False,
    )
    assert diagnostic["classification"] == "MANDATORY_GATE_HOLD"
    assert diagnostic["failed_or_non_true_gates"] == ["route_contract"]


def test_failure_diagnostics_classify_positive_aggregate_failure() -> None:
    diagnostic = _classify_synthetic_failure(
        {"mandatory_gates": {"route_contract": True}},
        positive_exit_code=7,
        negative_control_pass=True,
    )
    assert diagnostic["classification"] == "POSITIVE_AGGREGATE_EXECUTION_FAILURE"


def test_failure_diagnostics_classify_negative_control_failure() -> None:
    diagnostic = _classify_synthetic_failure(
        {"mandatory_gates": {"route_contract": True}},
        positive_exit_code=0,
        negative_control_pass=False,
    )
    assert diagnostic["classification"] == "NEGATIVE_CONTROL_FAILURE"


def test_failure_diagnostics_mark_missing_core_verdict() -> None:
    diagnostic = _classify_synthetic_failure(
        "MISSING",
        positive_exit_code="MISSING",
        negative_control_pass="MISSING",
    )
    assert diagnostic["classification"] == "VERDICT_EVIDENCE_MISSING"


def test_failure_retention_is_four_bounded_artifacts_and_marks_missing(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run"
    source = run_root / "evidence" / "f5" / "synthetic-A"
    (source / "receipts").mkdir(parents=True)
    (source / "probe_verdict_core.json").write_text(
        json.dumps({
            "trial_id": "trial-A",
            "final_probe_result": "HOLD",
            "mandatory_gates": {"route_contract": False},
            "positive_exit_code": 2,
            "negative_control_pass": True,
        }),
        encoding="utf-8",
    )
    (source / "gate_inputs.json").write_text(
        json.dumps({"gate_contract": "F5_CANONICAL_V1", "mandatory_gates": {"route_contract": False}}),
        encoding="utf-8",
    )
    (source / "aggregate_positive.process.json").write_text(
        json.dumps({"exit_code": 2, "stdout": "HOLD", "stderr": ""}), encoding="utf-8"
    )
    (source / "receipts" / "P4_canonical.json").write_text(
        json.dumps({"trial_id": "trial-A", "route_type": "canonical", "result": "HOLD"}),
        encoding="utf-8",
    )
    result = subprocess.CompletedProcess([], 2, stdout="route output", stderr="route error")
    destination = tmp_path / "ci" / "evidence"
    paths = _retain_synthetic_failure_evidence(run_root, result, destination=destination)
    assert [path.name for path in paths] == [
        "a3_synthetic_failure_core.json",
        "a3_synthetic_gate_inputs.json",
        "a3_synthetic_aggregates.json",
        "a3_synthetic_route_failures.json",
    ]
    assert len(list(destination.iterdir())) == 4
    core = json.loads((destination / "a3_synthetic_failure_core.json").read_text(encoding="utf-8"))
    assert core["failed_or_non_true_gates"] == ["route_contract"]
    assert core["diagnostic_classification"] == "MANDATORY_GATE_HOLD"
    aggregates = json.loads((destination / "a3_synthetic_aggregates.json").read_text(encoding="utf-8"))
    assert aggregates["negative"] == "MISSING"
    assert all(path.stat().st_size <= 256 * 1024 for path in paths)
