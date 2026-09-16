from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import pytest

REPO = Path(__file__).resolve().parents[1]
BOUNDED_IO = REPO / "tools" / "release" / "a3_f5_bounded_io.ps1"
PROBE = REPO / "tools" / "release" / "a3_probe_windows.ps1"
OBSERVER = REPO / "tools" / "release" / "a3_process_observer.py"
_TRACE_PHASES = (
    "PROCESS_STARTED",
    "SCRIPT_IMPORT_BEGIN",
    "SCRIPT_IMPORT_END",
    "INITIALIZE_BEGIN",
    "INITIALIZE_END",
    "WRITE_BEGIN",
    "WRITE_END",
    "USAGE_BEGIN",
    "USAGE_END",
    "OUTPUT_BEGIN",
    "OUTPUT_END",
    "SCRIPT_END",
)


def _powershell() -> str:
    for candidate in ("powershell.exe", "powershell", "pwsh.exe", "pwsh"):
        executable = shutil.which(candidate)
        if executable:
            return executable
    pytest.skip("PowerShell is required for bounded-I/O tests")


def _run(script: str, *, timeout: float = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def _write_trace_record(trace_path: Path, phase: str, *, started: float, pid: int) -> None:
    elapsed_ms = max(0, int((perf_counter() - started) * 1000))
    line = (
        f"{elapsed_ms}ms | {datetime.now(UTC).isoformat()} | "
        f"pid={pid} | {phase}\n"
    )
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8", newline="") as stream:
        stream.write(line)
        stream.flush()


def _read_trace_records(trace_path: Path) -> list[str]:
    try:
        return [line.strip() for line in trace_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    except OSError:
        return []


def _trace_phase(record: str) -> str:
    return record.rsplit("|", 1)[-1].strip()


def _trace_state(records: list[str]) -> tuple[str, str, str]:
    last_completed = "NONE"
    in_progress = "PROCESS_STARTUP" if not records else "NONE"
    next_phase = "PROCESS_STARTED" if not records else "UNKNOWN"
    for record in records:
        phase = _trace_phase(record)
        if phase == "PROCESS_STARTED":
            last_completed = phase
            in_progress = "NONE"
            next_phase = "SCRIPT_IMPORT_BEGIN"
        elif phase.endswith("_BEGIN"):
            in_progress = phase.removesuffix("_BEGIN")
            next_phase = f"{in_progress}_END"
        elif phase in _TRACE_PHASES:
            last_completed = phase
            in_progress = "NONE"
            index = _TRACE_PHASES.index(phase)
            next_phase = _TRACE_PHASES[index + 1] if index + 1 < len(_TRACE_PHASES) else "NONE"
        else:
            next_phase = "UNKNOWN"
    return last_completed, in_progress, next_phase


class _PowerShellTraceTimeout(RuntimeError):
    def __init__(
        self,
        *,
        timeout: float,
        elapsed: float,
        trace_path: Path,
        records: list[str],
    ) -> None:
        self.timeout = timeout
        self.elapsed = elapsed
        self.trace_path = trace_path
        self.records = records
        (
            self.last_completed_phase,
            self.in_progress_phase,
            self.next_phase_expected,
        ) = _trace_state(records)
        trace = "\n".join(records) if records else "(no trace records captured)"
        super().__init__(
            "POWERSHELL_TIMEOUT\n"
            f"timeout={timeout:g}s elapsed_before_timeout={elapsed:.3f}s\n"
            f"TRACE_PATH={trace_path}\n"
            f"TRACE:\n{trace}\n"
            f"LAST_COMPLETED_PHASE={self.last_completed_phase}\n"
            f"IN_PROGRESS_PHASE={self.in_progress_phase}\n"
            f"NEXT_PHASE_EXPECTED={self.next_phase_expected}"
        )


def _run_traced(script: str, *, trace_path: Path, timeout: float = 30) -> subprocess.CompletedProcess[str]:
    started = perf_counter()
    try:
        return _run(script, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise _PowerShellTraceTimeout(
            timeout=timeout,
            elapsed=perf_counter() - started,
            trace_path=trace_path,
            records=_read_trace_records(trace_path),
        ) from error


def _traced_bounded_json_script(trace_path: Path, target: Path) -> str:
    return f"""
$ErrorActionPreference = 'Stop'
$tracePath = {_quote(trace_path)}
$traceWatch = [Diagnostics.Stopwatch]::StartNew()
$traceEncoding = New-Object System.Text.UTF8Encoding($false)
function Write-C2Trace([string]$phase) {{
    $line = ('{{0}}ms | {{1}} | pid={{2}} | {{3}}' -f [int]$traceWatch.Elapsed.TotalMilliseconds, [DateTime]::UtcNow.ToString('o'), $PID, $phase)
    [IO.File]::AppendAllText($tracePath, $line + [Environment]::NewLine, $traceEncoding)
}}
Write-C2Trace 'PROCESS_STARTED'
Write-C2Trace 'SCRIPT_IMPORT_BEGIN'
. {_quote(BOUNDED_IO)}
Write-C2Trace 'SCRIPT_IMPORT_END'
Write-C2Trace 'INITIALIZE_BEGIN'
Initialize-F5BoundedIo -Limits @{{ EVIDENCE_META = @{{ max_file_count=2; max_per_file_bytes=256; max_aggregate_bytes=512; max_atomic_overlap_bytes=256 }} }}
Write-C2Trace 'INITIALIZE_END'
Write-C2Trace 'WRITE_BEGIN'
Write-F5BoundedJson -Path {_quote(target)} -Value ([ordered]@{{result='PASS'}}) -WriteClass EVIDENCE_META -Immutable
Write-C2Trace 'WRITE_END'
Write-C2Trace 'USAGE_BEGIN'
$usage = Get-F5BoundedIoUsage | ConvertTo-Json -Compress
Write-C2Trace 'USAGE_END'
Write-C2Trace 'OUTPUT_BEGIN'
Write-Output $usage
Write-C2Trace 'OUTPUT_END'
Write-C2Trace 'SCRIPT_END'
"""


def test_bounded_json_write_is_atomic_and_records_usage(tmp_path: Path) -> None:
    target = tmp_path / "receipt.json"
    trace_path = tmp_path / "powershell-trace.log"
    result = _run_traced(
        _traced_bounded_json_script(trace_path, target), trace_path=trace_path
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(target.read_text(encoding="utf-8")) == {"result": "PASS"}
    assert not target.with_name(target.name + ".bounded.tmp").exists()
    usage = json.loads(result.stdout.strip().splitlines()[-1])
    assert usage["EVIDENCE_META"]["file_count"] == 1
    records = _read_trace_records(trace_path)
    assert [_trace_phase(record) for record in records] == list(_TRACE_PHASES)
    assert _trace_phase(records[-1]) == "SCRIPT_END"


def test_oversized_write_fails_closed_without_partial_target(tmp_path: Path) -> None:
    target = tmp_path / "too-large.json"
    script = f"""
. {_quote(BOUNDED_IO)}
Initialize-F5BoundedIo -Limits @{{ EVIDENCE_META = @{{ max_file_count=1; max_per_file_bytes=32; max_aggregate_bytes=32; max_atomic_overlap_bytes=32 }} }}
Write-F5BoundedJson -Path {_quote(target)} -Value ([ordered]@{{payload=('x' * 128)}}) -WriteClass EVIDENCE_META
"""
    result = _run(script)

    assert result.returncode != 0
    assert "MATERIAL_WRITE_BOUND_EXCEEDED" in (result.stdout + result.stderr)
    assert not target.exists()


def test_aggregate_and_file_count_limits_are_enforced(tmp_path: Path) -> None:
    first = tmp_path / "one.txt"
    second = tmp_path / "two.txt"
    script = f"""
. {_quote(BOUNDED_IO)}
Initialize-F5BoundedIo -Limits @{{ ROUTE_ARTIFACTS = @{{ max_file_count=1; max_per_file_bytes=64; max_aggregate_bytes=64; max_atomic_overlap_bytes=64 }} }}
Write-F5BoundedText -Path {_quote(first)} -Text 'ok' -WriteClass ROUTE_ARTIFACTS
Write-F5BoundedText -Path {_quote(second)} -Text 'also-ok' -WriteClass ROUTE_ARTIFACTS
"""
    result = _run(script)

    assert result.returncode != 0
    assert "MATERIAL_WRITE_BOUND_EXCEEDED" in (result.stdout + result.stderr)
    assert first.exists()
    assert not second.exists()


def test_bounded_process_output_refuses_stdout_overflow(tmp_path: Path) -> None:
    output = tmp_path / "process.json"
    script = f"""
. {_quote(BOUNDED_IO)}
Initialize-F5BoundedIo -Limits @{{ ROUTE_ARTIFACTS = @{{ max_file_count=4; max_per_file_bytes=4096; max_aggregate_bytes=8192; max_atomic_overlap_bytes=4096; max_stdout_bytes=32; max_stderr_bytes=32; max_runtime_seconds=10 }} }}
Invoke-F5BoundedProcess -FilePath {_quote(Path(_powershell()))} -Arguments @('-NoProfile','-Command',\"[Console]::Out.Write('x' * 256)\") -WriteClass ROUTE_ARTIFACTS -ResultPath {_quote(output)}
"""
    result = _run(script)

    assert result.returncode != 0
    assert "MATERIAL_WRITE_BOUND_EXCEEDED" in (result.stdout + result.stderr)
    assert not output.exists()


def test_process_census_cardinality_and_field_limits_fail_closed() -> None:
    script = f"""
. {_quote(BOUNDED_IO)}
Assert-F5BoundedRecords -Records @(@{{command_line=('x' * 80)}}) -MaxRecords 2 -MaxFieldBytes 32 -MaxSerializedBytes 256 -Label PROCESS_CENSUS
"""
    result = _run(script)

    assert result.returncode != 0
    assert "MATERIAL_WRITE_BOUND_EXCEEDED" in (result.stdout + result.stderr)


@pytest.mark.skipif(
    sys.platform != "win32" or shutil.which("powershell.exe") is None,
    reason="Windows PowerShell 5.1 is required",
)
def test_explicit_empty_census_is_bounded_under_windows_powershell_51() -> None:
    powershell = shutil.which("powershell.exe")
    assert powershell is not None
    script = f"""
$ErrorActionPreference = 'Stop'
. {_quote(BOUNDED_IO)}
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) {{ throw 'PS51_REQUIRED' }}
$records = @()
Assert-F5BoundedRecords -Records $records -MaxRecords 0 -MaxFieldBytes 32 -MaxSerializedBytes 4 -Label PROCESS_CENSUS
'EMPTY_CENSUS_BOUNDED=PASS'
"""
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "EMPTY_CENSUS_BOUNDED=PASS" in result.stdout


def test_empty_census_receipt_is_valid_bounded_json(tmp_path: Path) -> None:
    target = tmp_path / "empty-census.json"
    script = f"""
$ErrorActionPreference = 'Stop'
. {_quote(BOUNDED_IO)}
Initialize-F5BoundedIo -Limits @{{ PROCESS_CENSUS = @{{ max_file_count=1; max_per_file_bytes=4; max_aggregate_bytes=4; max_atomic_overlap_bytes=4 }} }}
$records = @()
Assert-F5BoundedRecords -Records $records -MaxRecords 0 -MaxFieldBytes 32 -MaxSerializedBytes 4 -Label PROCESS_CENSUS
Write-F5BoundedJson -Path {_quote(target)} -Value $records -WriteClass PROCESS_CENSUS
"""
    result = _run(script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(target.read_text(encoding="utf-8")) == []


def test_sandbox_p0_census_preserves_explicit_empty_array(tmp_path: Path) -> None:
    script = f"""
$ErrorActionPreference = 'Stop'
. {_quote(BOUNDED_IO)}
Initialize-F5BoundedIo -Limits @{{ PROCESS_CENSUS = @{{ max_file_count=1; max_per_file_bytes=64; max_aggregate_bytes=64; max_atomic_overlap_bytes=64; max_records=0; max_field_bytes=32 }} }}
$source = Get-Content -Raw -LiteralPath {_quote(PROBE)}
$start = $source.IndexOf('function Get-RawCensus(')
$end = $source.IndexOf('function Invoke-Observer(', $start)
if ($start -lt 0 -or $end -le $start) {{ throw 'CENSUS_FUNCTION_NOT_FOUND' }}
. ([scriptblock]::Create($source.Substring($start, $end - $start)))
$records = Get-RawCensus -KnownPids @() -TrialRoot {_quote(tmp_path)}
if ($null -eq $records -or $records -isnot [array] -or $records.Count -ne 0) {{ throw 'EMPTY_ARRAY_IDENTITY_LOST' }}
'P0_EMPTY_ARRAY=PASS'
"""
    result = _run(script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "P0_EMPTY_ARRAY=PASS" in result.stdout


@pytest.mark.parametrize(
    ("records", "max_records", "max_bytes", "expected_pass"),
    [
        ("@(@{pid=1})", 1, 128, True),
        ("@(@{pid=1},@{pid=2})", 2, 128, True),
        ("@(@{pid=1},@{pid=2},@{pid=3})", 2, 128, False),
        ("@(@{command_line=('x' * 40)})", 1, 16, False),
        ("$null", 1, 128, False),
        ("@('not-a-record')", 1, 128, False),
    ],
)
def test_census_record_limits_and_shape_fail_closed(
    records: str, max_records: int, max_bytes: int, expected_pass: bool
) -> None:
    script = f"""
$ErrorActionPreference = 'Stop'
. {_quote(BOUNDED_IO)}
$records = {records}
Assert-F5BoundedRecords -Records $records -MaxRecords {max_records} -MaxFieldBytes 128 -MaxSerializedBytes {max_bytes} -Label PROCESS_CENSUS
'CENSUS_ACCEPTED=YES'
"""
    result = _run(script)

    if expected_pass:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "CENSUS_ACCEPTED=YES" in result.stdout
    else:
        assert result.returncode != 0
        assert "CENSUS_ACCEPTED=YES" not in result.stdout


@pytest.mark.skipif(
    sys.platform != "win32" or shutil.which("powershell.exe") is None,
    reason="Windows PowerShell 5.1 synthetic P0 route",
)
def test_synthetic_canonical_p0_observer_reaches_pre_p1_boundary(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    trial = tmp_path / "trial"
    trial.mkdir()
    python = REPO / ".venv" / "Scripts" / "python.exe"
    script = f"""
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) {{ throw 'PS51_REQUIRED' }}
. {_quote(BOUNDED_IO)}
Initialize-F5BoundedIo -Limits @{{
    PROCESS_CENSUS = @{{ max_file_count=4; max_per_file_bytes=8192; max_aggregate_bytes=32768; max_atomic_overlap_bytes=8192; max_records=0; max_field_bytes=512 }}
    ROUTE_ARTIFACTS = @{{ max_file_count=4; max_per_file_bytes=8192; max_aggregate_bytes=32768; max_atomic_overlap_bytes=8192; max_stdout_bytes=8192; max_stderr_bytes=8192; max_runtime_seconds=15 }}
}}
$source = Get-Content -Raw -LiteralPath {_quote(PROBE)}
foreach ($pair in @(
    @('function Get-Sha256(', 'function Get-CanonicalPath('),
    @('function Write-Json(', 'function Get-ProcessTreeEvidence('),
    @('function Get-RawCensus(', '$script:observerSequence = 0')
)) {{
    $start = $source.IndexOf($pair[0])
    $end = $source.IndexOf($pair[1], $start + 1)
    if ($start -lt 0 -or $end -le $start) {{ throw 'CANONICAL_P0_FUNCTION_NOT_FOUND' }}
    . ([scriptblock]::Create($source.Substring($start, $end - $start)))
}}
$evidence = {_quote(evidence)}
$observer = {_quote(OBSERVER)}
$python = {_quote(python)}
$legacyHash = ('0' * 64)
$stubHash = ('1' * 64)
$script:observerSequence = 0
$f5 = [pscustomobject]@{{ root = {_quote(trial)} }}
$trialId = 'synthetic-p0'
$routeStart = $source.IndexOf('function Invoke-F5CanonicalRoute')
$p0Start = $source.IndexOf('$p0=Invoke-Observer', $routeStart)
$nextDispatch = $source.IndexOf('$f5Job = Start-A3ContainedProcess', $p0Start)
if ($routeStart -lt 0 -or $p0Start -lt 0 -or $nextDispatch -le $p0Start) {{ throw 'CANONICAL_P0_BOUNDARY_NOT_FOUND' }}
$p0Call = $source.Substring($p0Start, $nextDispatch - $p0Start)
if (-not $p0Call.Contains("'P0_BEFORE_CUTOVER_TRIAL'")) {{ throw 'CANONICAL_P0_STAGE_MISMATCH' }}
. ([scriptblock]::Create($p0Call))
if ($null -eq $p0) {{ throw 'P0_SNAPSHOT_MISSING' }}
'NEXT_PRE_P1_DISPATCH_BOUNDARY_REACHED=YES'
"""
    result = _run(script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "NEXT_PRE_P1_DISPATCH_BOUNDARY_REACHED=YES" in result.stdout
    raw = json.loads((evidence / "observer" / "P0_BEFORE_CUTOVER_TRIAL.raw.json").read_text())
    assert raw == []
    snapshot = json.loads(
        (evidence / "observer" / "P0_BEFORE_CUTOVER_TRIAL.snapshot.json").read_text()
    )
    assert snapshot["trial_id"] == "synthetic-p0"


def test_traced_powershell_timeout_preserves_side_channel_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trace_path = tmp_path / "powershell-trace.log"
    started = perf_counter()

    def fake_run(*args, **kwargs):
        del args
        assert kwargs["timeout"] == 0.05
        for phase in (
            "PROCESS_STARTED",
            "SCRIPT_IMPORT_BEGIN",
            "SCRIPT_IMPORT_END",
            "INITIALIZE_BEGIN",
        ):
            _write_trace_record(trace_path, phase, started=started, pid=1234)
        raise subprocess.TimeoutExpired("synthetic-powershell", kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(_PowerShellTraceTimeout) as caught:
        _run_traced("ignored", trace_path=trace_path, timeout=0.05)

    error = caught.value
    assert trace_path.exists()
    assert error.last_completed_phase == "SCRIPT_IMPORT_END"
    assert error.in_progress_phase == "INITIALIZE"
    assert error.next_phase_expected == "INITIALIZE_END"
    message = str(error)
    assert "POWERSHELL_TIMEOUT" in message
    assert "elapsed_before_timeout=" in message
    assert "TRACE_PATH" in message
    assert "PROCESS_STARTED" in message
    assert "LAST_COMPLETED_PHASE=SCRIPT_IMPORT_END" in message
    assert "IN_PROGRESS_PHASE=INITIALIZE" in message
    assert "NEXT_PHASE_EXPECTED=INITIALIZE_END" in message
