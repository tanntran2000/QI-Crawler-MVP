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
    command = (
        "function Resolve-Path { param($LiteralPath) "
        "if ($LiteralPath -like '*release_staging*') { throw 'HISTORICAL_ARTIFACT_FORBIDDEN' }; "
        "Microsoft.PowerShell.Management\\Resolve-Path -LiteralPath $LiteralPath }; "
        f"& {_ps(SYNTHETIC_ROUTE)} -Root {_ps(tmp_path / 'one-run')}"
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
