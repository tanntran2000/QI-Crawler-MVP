from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
GUARD = REPO / "tools" / "release" / "a3_f5_guard.ps1"
PROBE = REPO / "tools" / "release" / "a3_probe_windows.ps1"
SEED_TOOL = REPO / "tools" / "release" / "a3_f5_seed_db.py"
BOUNDED_IO = REPO / "tools" / "release" / "a3_f5_bounded_io.ps1"
RECOVERY = REPO / "tools" / "release" / "a3_recovery.py"
JOB_HELPER = REPO / "tools" / "release" / "a3_job_object.ps1"
NATIVE_LINEAGE = REPO / "tools" / "release" / "a3_native_lineage.ps1"
OBSERVER = REPO / "tools" / "release" / "a3_process_observer.py"
PHASE_HELPER = REPO / "tools" / "release" / "a3_phase_contract.ps1"

from tools.release.a3_f5_seed_db import logical_database_digest


def _powershell() -> str:
    for candidate in ("powershell.exe", "powershell", "pwsh.exe", "pwsh"):
        executable = shutil.which(candidate)
        if executable:
            return executable
    pytest.skip("PowerShell is required for the pre-execution contract tests")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resource_id(sandbox: Path) -> str:
    value = str(sandbox.resolve()).rstrip("\\").lower().replace("\\", "/")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sandbox(tmp_path: Path, *, complete: bool = True) -> Path:
    sandbox = tmp_path / "sandbox"
    runtime = sandbox / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "runtime-marker.bin").write_bytes(b"runtime")
    if complete:
        (sandbox / "install" / "QI-Crawler").mkdir(parents=True)
        (sandbox / "install" / "QI-Crawler" / "QI-Crawler.exe").write_bytes(b"fixture")
        (sandbox / "data" / "data" / "database").mkdir(parents=True)
        (sandbox / "transaction").mkdir()
    return sandbox


def _contract(tmp_path: Path, sandbox: Path, **changes: object) -> Path:
    contract = {
        "schema": "AO-04-C3-F5-PREEXECUTION-CONTRACT-V1",
        "contract_status": "VALID",
        "sandbox_path": str(sandbox.resolve()),
        "sandbox_resource_id": _resource_id(sandbox),
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
            "build_identity": "synthetic-runtime",
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
                "bound_source": "runtime manifest",
                "recovery_requirement": "preserve",
            },
            {
                "id": "install",
                "relative_path": "install",
                "classification": "PREEXISTING_IMMUTABLE_INPUT",
                "kind": "directory",
                "must_exist_before_dispatch": True,
                "may_be_created_during_f5": False,
                "expected_max_bytes": 6,
                "bound_source": "synthetic fixture",
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
                "bound_source": "synthetic empty fixture",
                "recovery_requirement": "snapshot before trial",
            },
            {
                "id": "transaction",
                "relative_path": "transaction",
                "classification": "PREEXISTING_MUTABLE_FIXTURE",
                "kind": "directory",
                "must_exist_before_dispatch": True,
                "may_be_created_during_f5": False,
                "expected_max_bytes": 1024,
                "bound_source": "synthetic transaction cap",
                "recovery_requirement": "journaled state",
            },
            {
                "id": "routes",
                "relative_path": "routes",
                "classification": "GENERATED_BOUNDED_EVIDENCE",
                "kind": "directory",
                "must_exist_before_dispatch": False,
                "may_be_created_during_f5": True,
                "expected_max_bytes": 4096,
                "bound_source": "five route artifacts",
                "recovery_requirement": "retain receipts",
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
                "bound_source": "synthetic bounded transaction state",
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
    for key, value in changes.items():
        contract[key] = value
    path = tmp_path / "F5_PREEXECUTION_CONTRACT.json"
    path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    return path


def _fm021_contract(tmp_path: Path, sandbox: Path, **changes: object) -> Path:
    db = sandbox / "data" / "data" / "database" / "egp.db"
    with closing(sqlite3.connect(db)) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT NOT NULL)")
        connection.execute("INSERT INTO alembic_version VALUES ('0020_add_tender_operational_revision_events')")
        connection.commit()
    contract = _contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    digest = logical_database_digest(db).sha256
    seed_spec = tmp_path / "DB_FIXTURE_SEED_SPEC.json"
    seed_spec.write_text(
        json.dumps(
            {
                "target_revision": "0020_add_tender_operational_revision_events",
                "expected_logical_digest": digest,
                "business_data_required": False,
            }
        ) + "\n",
        encoding="utf-8",
    )
    data.update(
        {
            "schema": "AO-04-C3-F5-PREEXECUTION-CONTRACT-FM021-V1",
            "contract_status": "READY_FOR_MATERIALIZATION",
            "real_f5_authorized": False,
            "real_f5_authorized_field_semantics": (
                "THIS_TECHNICAL_CONTRACT_DOES_NOT_ITSELF_AUTHORIZE_EXECUTION"
            ),
            "contract_grants_execution_authority": False,
            "execution_authority_source": "EXTERNAL_PLANNER_WORK_ORDER",
            "seed_spec_identity": {"path": str(seed_spec.resolve()), "sha256": _sha(seed_spec)},
            "recovery_semantics": {
                "model": "PRE_MIGRATION_DB_GENERATION_INVARIANCE",
                "start_schema": "0020_add_tender_operational_revision_events",
                "end_schema": "0020_add_tender_operational_revision_events",
                "schema_downgrade": "OUT_OF_SCOPE",
            },
            "fixture_identities": [
                {
                    "id": "V09_EXECUTABLE",
                    "relative_path": "install/QI-Crawler/QI-Crawler.exe",
                    "size_bytes": 7,
                    "sha256": _sha(sandbox / "install" / "QI-Crawler" / "QI-Crawler.exe"),
                },
                {
                    "id": "SYNTHETIC_DB_0020",
                    "source_path": str(db.resolve()),
                    "relative_path": "data/data/database/egp.db",
                    "size_bytes": db.stat().st_size,
                    "sha256": _sha(db),
                    "logical_digest_algorithm": "qi-sqlite-logical-v1",
                    "logical_digest": digest,
                    "schema": "0020_add_tender_operational_revision_events",
                },
            ],
            "logical_digest_tool": {"path": str(SEED_TOOL.resolve()), "sha256": _sha(SEED_TOOL)},
            "job_helper_identity": {"path": str(JOB_HELPER.resolve()), "sha256": _sha(JOB_HELPER)},
            "native_lineage_identity": {"path": str(NATIVE_LINEAGE.resolve()), "sha256": _sha(NATIVE_LINEAGE)},
            "observer_identity": {"path": str(OBSERVER.resolve()), "sha256": _sha(OBSERVER)},
            "bounded_io_identity": {"path": str(BOUNDED_IO.resolve()), "sha256": _sha(BOUNDED_IO)},
            "recovery_identity": {"path": str(RECOVERY.resolve()), "sha256": _sha(RECOVERY)},
            "material_write_bounds": [
                {
                    "write_class": name,
                    "max_file_count": 64,
                    "max_per_file_bytes": 16_777_216,
                    "max_aggregate_bytes": 67_108_864,
                    "max_atomic_overlap_bytes": 16_777_216,
                    **(
                        {"max_records": 4096, "max_field_bytes": 32768}
                        if name == "PROCESS_CENSUS"
                        else {}
                    ),
                    **(
                        {"max_entries": 4}
                        if name == "DB_MANIFEST"
                        else {}
                    ),
                    **(
                        {"max_stdout_bytes": 1_048_576, "max_stderr_bytes": 1_048_576, "max_runtime_seconds": 60}
                        if name in {"ROUTE_ARTIFACTS", "RECOVERY"}
                        else {}
                    ),
                }
                for name in (
                    "EVIDENCE_META",
                    "PROCESS_CENSUS",
                    "TX_STATE",
                    "DB_MANIFEST",
                    "ROUTE_ARTIFACTS",
                    "RECOVERY",
                )
            ],
        }
    )
    data.update(changes)
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return contract


def test_fm021_contract_declares_external_execution_authority(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    contract = json.loads(_fm021_contract(tmp_path, sandbox).read_text(encoding="utf-8"))

    assert contract["real_f5_authorized"] is False
    assert contract["contract_grants_execution_authority"] is False
    assert contract["execution_authority_source"] == "EXTERNAL_PLANNER_WORK_ORDER"
    assert contract["real_f5_authorized_field_semantics"] == (
        "THIS_TECHNICAL_CONTRACT_DOES_NOT_ITSELF_AUTHORIZE_EXECUTION"
    )


def _manifest(tmp_path: Path, sandbox: Path, input_path: Path, contract: Path | None) -> Path:
    runtime = sandbox / "runtime"
    entries = [
        {
            "relative_path": "runtime-marker.bin",
            "size_bytes": 7,
            "sha256": _sha(runtime / "runtime-marker.bin"),
            "tracked": "NO",
            "reparse_point": "NO",
            "read_status": "PASS",
        }
    ]
    inputs = [
        {
            "path": str(input_path.resolve()),
            "classification": "EXECUTION_INPUT",
            "size_bytes": input_path.stat().st_size,
            "sha256": _sha(input_path),
            "tracked": "NO",
            "reparse_point": "NO",
            "read_status": "PASS",
        }
    ]
    if contract is not None:
        inputs.append(
            {
                "path": str(contract.resolve()),
                "classification": "EXECUTION_INPUT",
                "size_bytes": contract.stat().st_size,
                "sha256": _sha(contract),
                "tracked": "NO",
                "reparse_point": "NO",
                "read_status": "PASS",
            }
        )
    manifest = {
        "schema": "AO-04-C3-F5-TRIAL-INPUT-V1",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).splitlines(),
        "sandbox_path": str(sandbox.resolve()),
        "runtime_root": str(runtime.resolve()),
        "runtime_build_identity": "synthetic-runtime",
        "runtime_manifest": entries,
        "execution_inputs": inputs,
        "generated_inputs": [],
        "environment_allowlist": {"AO_GUARD_TEST": "1"},
    }
    path = tmp_path / "trial-input-manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def _run(
    tmp_path: Path,
    sandbox: Path,
    manifest: Path,
    *extra: str,
    contract: Path | None = None,
    preflight: bool = True,
) -> subprocess.CompletedProcess[str]:
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
        str(sandbox),
        "-RunId",
        "c1-test",
        "-InputManifestPath",
        str(manifest),
    ]
    if preflight:
        command.append("-PreflightOnly")
    if contract is not None:
        command.extend(["-PreexecutionContractPath", str(contract)])
    command.extend(extra)
    env = os.environ.copy()
    env["QI_CRAWLER_F5_TEST_MODE"] = "1"
    return subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False, env=env)


def _phase_case(
    tmp_path: Path, *, expected_phase: str, journal_phase: str | None = None,
    exe_bytes: bytes = b"stub",
) -> tuple[Path, Path, Path]:
    sandbox = _sandbox(tmp_path)
    canonical = sandbox / "install" / "QI-Crawler" / "QI-Crawler.exe"
    canonical.write_bytes(exe_bytes)
    if journal_phase is not None:
        (sandbox / "transaction" / "cutover.json").write_text(
            json.dumps({"phase": journal_phase}) + "\n", encoding="utf-8"
        )
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["schema"] = "AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V1"
    data["fixture_identities"][0]["size_bytes"] = canonical.stat().st_size
    data["phase_helper_identity"] = {
        "path": str(PHASE_HELPER.resolve()), "sha256": _sha(PHASE_HELPER)
    }
    data["phase_model"] = {
        "schema": "A3-F5-PHASE-MODEL-V1",
        "expected_phase": expected_phase,
        "pretrial_exe_sha256": hashlib.sha256(b"v09").hexdigest(),
        "maintenance_stub_sha256": hashlib.sha256(b"stub").hexdigest(),
    }
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return sandbox, contract, _manifest(tmp_path, sandbox, source, contract)


def test_phase_red_pretrial_rejects_installed_stub(tmp_path: Path) -> None:
    sandbox, contract, manifest = _phase_case(tmp_path, expected_phase="PRETRIAL")
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "A3_PHASE_MISMATCH" in result.stdout + result.stderr


def test_phase_red_unknown_phase_is_not_accepted(tmp_path: Path) -> None:
    sandbox, contract, manifest = _phase_case(tmp_path, expected_phase="UNKNOWN")
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "A3_PHASE_INVALID" in result.stdout + result.stderr


def test_phase_red_stub_staged_is_not_post_barrier(tmp_path: Path) -> None:
    sandbox, contract, manifest = _phase_case(
        tmp_path, expected_phase="POST_BARRIER_MAINTENANCE", journal_phase="BARRIER_CANDIDATE"
    )
    _ = manifest
    command = (
        f". '{PHASE_HELPER}'; "
        f"$model=(Get-Content -Raw -LiteralPath '{contract}' | ConvertFrom-Json).phase_model; "
        f"Assert-A3Phase -Sandbox '{sandbox}' -Model $model "
        "-ExpectedPhase 'POST_BARRIER_MAINTENANCE'"
    )
    result = subprocess.run(
        [_powershell(), "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=REPO, text=True, capture_output=True, check=False,
    )
    assert result.returncode != 0
    assert "A3_PHASE_MISMATCH" in result.stdout + result.stderr


def _observe_phase(sandbox: Path, contract: Path, expected_phase: str) -> subprocess.CompletedProcess[str]:
    command = (
        f". '{PHASE_HELPER}'; "
        f"$model=(Get-Content -Raw -LiteralPath '{contract}' | ConvertFrom-Json).phase_model; "
        f"Assert-A3Phase -Sandbox '{sandbox}' -Model $model "
        f"-ExpectedPhase '{expected_phase}'"
    )
    return subprocess.run(
        [_powershell(), "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=REPO, text=True, capture_output=True, check=False,
    )


def test_phase_pretrial_v09_preflight_passes(tmp_path: Path) -> None:
    sandbox, contract, manifest = _phase_case(
        tmp_path, expected_phase="PRETRIAL", exe_bytes=b"v09"
    )
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PREEXECUTION_CONTRACT=PASS" in result.stdout


def test_phase_pretrial_companion_refuses(tmp_path: Path) -> None:
    sandbox, contract, manifest = _phase_case(
        tmp_path, expected_phase="PRETRIAL", exe_bytes=b"v09"
    )
    (sandbox / "install" / "QI-Crawler" / "maintenance_stub_state.json").write_text(
        "{}\n", encoding="utf-8"
    )
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "A3_PHASE_MISMATCH" in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("exe_bytes", "journal_phase", "expected_phase", "passes"),
    [
        (b"stub", "BARRIER_CANDIDATE", "CUTOVER_STUB_STAGED", True),
        (b"stub", "BARRIER_CANDIDATE", "POST_BARRIER_MAINTENANCE", False),
        (b"stub", "BARRIER_CONFIRMED", "POST_BARRIER_MAINTENANCE", True),
        (b"stub", None, "POST_BARRIER_MAINTENANCE", False),
        (b"v09", "BARRIER_CONFIRMED", "POST_BARRIER_MAINTENANCE", False),
    ],
)
def test_phase_observation_matrix(
    tmp_path: Path, exe_bytes: bytes, journal_phase: str | None,
    expected_phase: str, passes: bool,
) -> None:
    sandbox, contract, _ = _phase_case(
        tmp_path, expected_phase="PRETRIAL", journal_phase=journal_phase,
        exe_bytes=exe_bytes,
    )
    result = _observe_phase(sandbox, contract, expected_phase)
    assert (result.returncode == 0) is passes, result.stdout + result.stderr
    if not passes:
        assert "A3_PHASE_MISMATCH" in result.stdout + result.stderr


@pytest.mark.parametrize("bad_schema", ["A3-F5-PHASE-MODEL-V0", "UNKNOWN", ""])
def test_phase_model_schema_refuses(tmp_path: Path, bad_schema: str) -> None:
    sandbox, contract, _ = _phase_case(
        tmp_path, expected_phase="PRETRIAL", exe_bytes=b"v09"
    )
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["phase_model"]["schema"] = bad_schema
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    result = _observe_phase(sandbox, contract, "PRETRIAL")
    assert result.returncode != 0
    assert "A3_PHASE_INVALID" in result.stdout + result.stderr


def test_phase_malformed_transaction_refuses(tmp_path: Path) -> None:
    sandbox, contract, _ = _phase_case(
        tmp_path, expected_phase="PRETRIAL", exe_bytes=b"v09"
    )
    (sandbox / "transaction" / "cutover.json").write_text("{broken", encoding="utf-8")
    result = _observe_phase(sandbox, contract, "PRETRIAL")
    assert result.returncode != 0
    assert "A3_PHASE_INVALID" in result.stdout + result.stderr


def test_phase_pretrial_with_transaction_activity_refuses(tmp_path: Path) -> None:
    sandbox, contract, _ = _phase_case(
        tmp_path, expected_phase="PRETRIAL", journal_phase="CUTOVER_INTENT",
        exe_bytes=b"v09",
    )
    result = _observe_phase(sandbox, contract, "PRETRIAL")
    assert result.returncode != 0
    assert "A3_PHASE_MISMATCH" in result.stdout + result.stderr


def test_unknown_preexecution_schema_refuses(tmp_path: Path) -> None:
    sandbox, contract, _ = _phase_case(
        tmp_path, expected_phase="PRETRIAL", exe_bytes=b"v09"
    )
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["schema"] = "AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V99"
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    source = tmp_path / "controller.ps1"
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_INVALID" in result.stdout + result.stderr


def test_phase_aware_contract_without_phase_model_refuses(tmp_path: Path) -> None:
    sandbox, contract, _ = _phase_case(
        tmp_path, expected_phase="PRETRIAL", exe_bytes=b"v09"
    )
    data = json.loads(contract.read_text(encoding="utf-8"))
    data.pop("phase_model")
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    source = tmp_path / "controller.ps1"
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "A3_PHASE_INVALID" in result.stdout + result.stderr


def test_r1_reproduces_capacity_unknown_without_contract(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, None)
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
        "r1",
        "-InputManifestPath",
        str(manifest),
        "-TestStateRoot",
        str(tmp_path / "state"),
        "-TestGlobalLockPath",
        str(tmp_path / "lock"),
    ]
    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False, env=os.environ | {"QI_CRAWLER_F5_TEST_MODE": "1"})
    assert result.returncode != 0
    assert "CAPACITY_UNKNOWN" in result.stdout + result.stderr


def test_r2_layout_is_not_implicitly_bound(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data.pop("required_layout")
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_LAYOUT_UNBOUND" in result.stdout + result.stderr


def test_r3_missing_substantive_directory_is_not_a_generated_directory(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path, complete=False)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "EXISTING_SANDBOX_LAYOUT_INVALID" in result.stdout + result.stderr


def test_g1_valid_contract_binds_capacity_and_layout(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PREEXECUTION_CONTRACT=PASS" in result.stdout
    assert "EXISTING_SANDBOX_LAYOUT=PASS" in result.stdout
    assert "CAPACITY_CONTRACT=PASS" in result.stdout


def test_g2_missing_contract_fails_closed(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, None)
    result = _run(tmp_path, sandbox, manifest, contract=tmp_path / "missing.json")
    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_REQUIRED" in result.stdout + result.stderr


def test_g3_tampered_contract_fails_closed(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["next_operation_peak_bytes"] = 999
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_CAPACITY_UNBOUND" in result.stdout + result.stderr


def test_g4_wrong_sandbox_fails_closed(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    other = _sandbox(tmp_path / "other")
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, other)
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_SANDBOX_MISMATCH" in result.stdout + result.stderr


def test_g5_wrong_route_identity_fails_closed(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["canonical_route_identity"]["function"] = "WrongRoute"
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_ROUTE_MISMATCH" in result.stdout + result.stderr


def test_g6_unknown_capacity_operation_fails_closed(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["capacity_operations"][0]["operation_id"] = "UNKNOWN"
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_CAPACITY_UNBOUND" in result.stdout + result.stderr


def test_g7_insufficient_capacity_fails_closed(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["capacity_operations"][0]["peak_bytes"] = 10**15
    data["next_operation_peak_bytes"] = 10**15
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "CAPACITY_INSUFFICIENT" in result.stdout + result.stderr


def test_g8_missing_substantive_layout_is_hold(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path, complete=False)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode != 0
    assert "EXISTING_SANDBOX_LAYOUT_INVALID" in result.stdout + result.stderr


def test_g9_generated_empty_control_directory_is_optional(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _contract(tmp_path, sandbox)
    manifest = _manifest(tmp_path, sandbox, source, contract)
    result = _run(tmp_path, sandbox, manifest, contract=contract)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (sandbox / "routes").exists()


def test_fm021_contract_binds_fixture_identity_and_all_write_classes(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    manifest = _manifest(tmp_path, sandbox, source, contract)

    result = _run(tmp_path, sandbox, manifest, contract=contract)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "FIXTURE_IDENTITIES=PASS" in result.stdout
    assert "MATERIAL_WRITE_BOUNDS=PASS" in result.stdout


def test_fm021_contract_missing_write_class_refuses(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["material_write_bounds"] = data["material_write_bounds"][:-1]
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)

    result = _run(tmp_path, sandbox, manifest, contract=contract)

    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_WRITE_BOUND_UNKNOWN" in result.stdout + result.stderr


def test_fm021_contract_wrong_job_helper_identity_refuses(tmp_path: Path) -> None:
    """Changing the Job helper without rebinding must invalidate RealF5 preflight."""
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["job_helper_identity"] = {
        "path": str(JOB_HELPER.resolve()),
        "sha256": "0" * 64,
    }
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)

    result = _run(tmp_path, sandbox, manifest, contract=contract)

    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_JOB_IDENTITY_MISMATCH" in result.stdout + result.stderr


def test_fm021_contract_wrong_observer_identity_refuses(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["observer_identity"]["sha256"] = "0" * 64
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)

    result = _run(tmp_path, sandbox, manifest, contract=contract)

    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_OBSERVER_IDENTITY_MISMATCH" in result.stdout + result.stderr


def test_fm021_contract_wrong_native_lineage_identity_refuses(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["native_lineage_identity"]["sha256"] = "0" * 64
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)

    result = _run(tmp_path, sandbox, manifest, contract=contract)

    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_NATIVE_LINEAGE_IDENTITY_MISMATCH" in result.stdout + result.stderr


@pytest.mark.parametrize("field", ["sha256", "logical_digest"])
def test_fm021_contract_wrong_db_identity_refuses(tmp_path: Path, field: str) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["fixture_identities"][1][field] = "0" * 64
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)

    result = _run(tmp_path, sandbox, manifest, contract=contract)

    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_FIXTURE_MISMATCH" in result.stdout + result.stderr


@pytest.mark.parametrize(
    "field", ["schema", "seed_spec_sha", "seed_spec_revision", "recovery_model"]
)
def test_fm021_contract_rejects_wrong_schema_seed_or_recovery_model(
    tmp_path: Path, field: str
) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    data = json.loads(contract.read_text(encoding="utf-8"))
    if field == "schema":
        data["fixture_identities"][1]["schema"] = "0022_add_tender_recovery_events"
    elif field == "seed_spec_sha":
        data["seed_spec_identity"]["sha256"] = "0" * 64
    elif field == "seed_spec_revision":
        seed_spec = Path(data["seed_spec_identity"]["path"])
        seed_data = json.loads(seed_spec.read_text(encoding="utf-8"))
        seed_data["target_revision"] = "0022_add_tender_recovery_events"
        seed_spec.write_text(json.dumps(seed_data) + "\n", encoding="utf-8")
        data["seed_spec_identity"]["sha256"] = _sha(seed_spec)
    else:
        data["recovery_semantics"]["model"] = "SCHEMA_DOWNGRADE_0022_TO_0020"
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)

    result = _run(tmp_path, sandbox, manifest, contract=contract)

    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_FIXTURE_MISMATCH" in result.stdout + result.stderr


def test_fm021_contract_rejects_0022_db_even_if_identity_is_rebound(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    source = tmp_path / "controller.ps1"
    source.write_text("guard\n", encoding="utf-8")
    contract = _fm021_contract(tmp_path, sandbox)
    db = sandbox / "data" / "data" / "database" / "egp.db"
    with closing(sqlite3.connect(db)) as connection:
        connection.execute(
            "UPDATE alembic_version SET version_num = ?",
            ("0022_add_tender_recovery_events",),
        )
        connection.commit()
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["fixture_identities"][1].update(
        {
            "sha256": _sha(db),
            "size_bytes": db.stat().st_size,
            "logical_digest": logical_database_digest(db).sha256,
        }
    )
    seed_spec = Path(data["seed_spec_identity"]["path"])
    seed_data = json.loads(seed_spec.read_text(encoding="utf-8"))
    seed_data["expected_logical_digest"] = data["fixture_identities"][1]["logical_digest"]
    seed_spec.write_text(json.dumps(seed_data) + "\n", encoding="utf-8")
    data["seed_spec_identity"]["sha256"] = _sha(seed_spec)
    contract.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(tmp_path, sandbox, source, contract)

    result = _run(tmp_path, sandbox, manifest, contract=contract)

    assert result.returncode != 0
    assert "PREEXECUTION_CONTRACT_FIXTURE_MISMATCH" in result.stdout + result.stderr
    assert db.exists()
    assert "database schema is not pre-migration 0020" in result.stdout + result.stderr
