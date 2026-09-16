from __future__ import annotations

from pathlib import Path

import pytest

from tools.release.a3_process_observer import (
    F5_CANONICAL_REQUIRED_GATES,
    A3ProcessObserver,
    ObserverConfig,
    ProcessClass,
    ScopeProof,
    ScopeProofAuthority,
    aggregate_mandatory_gates,
)

LEGACY_SHA = "a" * 64
STUB_SHA = "b" * 64


def _complete_tree_proof() -> ScopeProof:
    return ScopeProof(
        observed_scope="SANDBOX_PROCESS_TREE",
        scope_complete=True,
        zero_proof_authority=ScopeProofAuthority.COMPLETE_PID_TREE,
        scope_evidence={
            "process_tree_complete": True,
            "root_absent": True,
            "tree_dead": True,
        },
    )


def _job_containment_proof() -> ScopeProof:
    return ScopeProof(
        observed_scope="F5_CONTROLLER_JOB",
        scope_complete=True,
        zero_proof_authority=ScopeProofAuthority.JOB_OBJECT_CONTAINMENT,
        scope_evidence={
            "root_identity_bound": True,
            "process_tree_complete": True,
            "job_membership_complete": True,
        },
    )


def _job_drained_proof() -> ScopeProof:
    return ScopeProof(
        observed_scope="F5_CONTROLLER_JOB_DRAINED",
        scope_complete=True,
        zero_proof_authority=ScopeProofAuthority.JOB_OBJECT_DRAINED,
        scope_evidence={
            "job_terminated": True,
            "job_active_after": 0,
            "receipt_persisted": True,
        },
    )


def _composite_proof(*, completed: int = 5) -> ScopeProof:
    return ScopeProof(
        observed_scope="F5_COMPOSITE_JOB_SCOPE",
        scope_complete=True,
        zero_proof_authority=ScopeProofAuthority.COMPOSITE_JOB_DRAINED,
        scope_evidence={
            "controller_job_drained": True,
            "route_jobs_drained": completed == 5,
            "route_contract_intact": completed == 5,
            "receipt_persisted": completed == 5,
            "expected_route_count": 5,
            "completed_route_count": completed,
        },
    )


def _config(tmp_path: Path) -> ObserverConfig:
    legacy = tmp_path / "legacy" / "QI-Crawler.exe"
    controller = tmp_path / "controller" / "AO03-Controller.exe"
    stub = tmp_path / "stub" / "QI-Crawler.exe"
    return ObserverConfig(
        trial_root=tmp_path,
        legacy_paths=frozenset({legacy}),
        controller_paths=frozenset({controller}),
        stub_paths=frozenset({stub}),
        legacy_sha256=LEGACY_SHA,
    )


def _shared_config(
    tmp_path: Path,
    bindings: tuple[dict[str, object], ...] = (),
) -> ObserverConfig:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    return ObserverConfig(
        trial_root=tmp_path,
        legacy_paths=frozenset({canonical}),
        stub_paths=frozenset({canonical}),
        legacy_sha256=LEGACY_SHA,
        stub_sha256=STUB_SHA,
        authoritative_process_identities=bindings,
    )


def _binding(
    pid: int = 100,
    *,
    role: str = ProcessClass.SANDBOX_LEGACY.value,
    digest: str = LEGACY_SHA,
    start_time: str = "2026-09-10T00:00:00Z",
    source: str = "LAUNCH_RECEIPT",
) -> dict[str, object]:
    return {
        "pid": pid,
        "start_time_utc": start_time,
        "role": role,
        "executable_sha256": digest,
        "identity_source": source,
    }


def _record(pid: int, path: str | None, **overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "pid": pid,
        "parent_pid": overrides.pop("parent_pid", None),
        "image_path": path,
        "image_sha256": overrides.pop("image_sha256", None),
        "start_time_utc": overrides.pop("start_time_utc", "2026-09-10T00:00:00Z"),
        "command_line": overrides.pop("command_line", None),
        "access_status": overrides.pop("access_status", "PASS"),
        "evidence_source": overrides.pop("evidence_source", "fixture"),
    }
    record.update(overrides)
    return record


def test_running_legacy_positive_control_is_counted_and_zero_is_false(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    snapshot = observer.census(
        [_record(101, str(tmp_path / "legacy" / "QI-Crawler.exe"), image_sha256=LEGACY_SHA)],
        event_name="positive-control-running",
        positive_control_passed=True,
        known_legacy_roots_absent=False,
    )

    assert snapshot.legacy_count == 1
    assert snapshot.legacy_zero_proven is False
    assert snapshot.records[0].classification == ProcessClass.SANDBOX_LEGACY


def test_shared_path_stub_sha_without_binding_is_unresolved(tmp_path: Path) -> None:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    observer = A3ProcessObserver(_shared_config(tmp_path))

    record = observer.classify_record(
        _record(100, str(canonical), image_sha256=STUB_SHA, relevant=True)
    )

    assert record.classification == ProcessClass.UNRESOLVED_RELEVANT


def test_shared_path_legacy_sha_without_binding_is_unresolved(tmp_path: Path) -> None:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    observer = A3ProcessObserver(_shared_config(tmp_path))

    record = observer.classify_record(
        _record(101, str(canonical), image_sha256=LEGACY_SHA, relevant=True)
    )

    assert record.classification == ProcessClass.UNRESOLVED_RELEVANT


def test_shared_path_valid_legacy_binding_authorizes_legacy(tmp_path: Path) -> None:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    observer = A3ProcessObserver(_shared_config(tmp_path, (_binding(),)))

    record = observer.classify_record(
        _record(100, str(canonical), image_sha256=STUB_SHA, relevant=True)
    )

    assert record.classification == ProcessClass.SANDBOX_LEGACY


def test_shared_path_valid_stub_binding_authorizes_stub(tmp_path: Path) -> None:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    observer = A3ProcessObserver(
        _shared_config(
            tmp_path,
            (_binding(role=ProcessClass.SANDBOX_STUB.value, digest=STUB_SHA),),
        )
    )

    record = observer.classify_record(
        _record(100, str(canonical), image_sha256=LEGACY_SHA, relevant=True)
    )

    assert record.classification == ProcessClass.SANDBOX_STUB


def test_shared_path_pid_creation_mismatch_is_unresolved(tmp_path: Path) -> None:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    observer = A3ProcessObserver(_shared_config(tmp_path, (_binding(),)))

    record = observer.classify_record(
        _record(
            100,
            str(canonical),
            image_sha256=LEGACY_SHA,
            start_time_utc="2026-09-10T00:00:01Z",
            relevant=True,
        )
    )

    assert record.classification == ProcessClass.UNRESOLVED_RELEVANT


def test_shared_path_binding_role_sha_mismatch_is_unresolved(tmp_path: Path) -> None:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    observer = A3ProcessObserver(
        _shared_config(
            tmp_path,
            (_binding(digest=STUB_SHA),),
        )
    )

    record = observer.classify_record(
        _record(100, str(canonical), image_sha256=LEGACY_SHA, relevant=True)
    )

    assert record.classification == ProcessClass.UNRESOLVED_RELEVANT


@pytest.mark.parametrize(
    ("role", "binding_sha", "record_sha", "expected"),
    [
        (ProcessClass.SANDBOX_LEGACY.value, LEGACY_SHA, STUB_SHA, ProcessClass.SANDBOX_LEGACY),
        (ProcessClass.SANDBOX_STUB.value, STUB_SHA, LEGACY_SHA, ProcessClass.SANDBOX_STUB),
    ],
)
def test_shared_path_role_survives_current_disk_replacement(
    tmp_path: Path,
    role: str,
    binding_sha: str,
    record_sha: str,
    expected: ProcessClass,
) -> None:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    observer = A3ProcessObserver(
        _shared_config(tmp_path, (_binding(role=role, digest=binding_sha),))
    )

    record = observer.classify_record(
        _record(100, str(canonical), image_sha256=record_sha, relevant=True)
    )

    assert record.classification == expected


def test_shared_path_ambiguity_blocks_legacy_zero_proof(tmp_path: Path) -> None:
    canonical = tmp_path / "install" / "QI-Crawler" / "QI-Crawler.exe"
    observer = A3ProcessObserver(_shared_config(tmp_path))

    snapshot = observer.census(
        [_record(100, str(canonical), image_sha256=STUB_SHA, relevant=True)],
        event_name="shared-canonical-ambiguous",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
    )

    assert snapshot.records[0].classification == ProcessClass.UNRESOLVED_RELEVANT
    assert snapshot.unresolved_relevant_count == 1
    assert snapshot.legacy_zero_proven is False


@pytest.mark.parametrize(
    "invalid",
    [
        _binding(pid=0),
        _binding(start_time="2026-09-10T00:00:00"),
        _binding(digest="not-a-sha"),
        _binding(role="SANDBOX_CONTROLLER"),
        _binding(source="PID_REOPEN"),
    ],
)
def test_malformed_authoritative_binding_fails_closed(
    tmp_path: Path, invalid: dict[str, object]
) -> None:
    with pytest.raises(ValueError, match="PROCESS_IDENTITY_BINDING"):
        _shared_config(tmp_path, (invalid,))


def test_duplicate_authoritative_bindings_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="PROCESS_IDENTITY_BINDING"):
        _shared_config(tmp_path, (_binding(), _binding()))


def test_terminated_positive_control_proves_zero(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    snapshot = observer.census(
        [],
        event_name="positive-control-terminated",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof=_complete_tree_proof(),
    )

    assert snapshot.legacy_count == 0
    assert snapshot.unresolved_relevant_count == 0
    assert snapshot.legacy_zero_proven is True


def test_empty_census_with_incomplete_scope_does_not_prove_zero(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))

    snapshot = observer.census(
        [],
        event_name="incomplete-scope",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof=ScopeProof(
            observed_scope="F5_CONTROLLER_JOB",
            scope_complete=False,
            zero_proof_authority=ScopeProofAuthority.JOB_OBJECT_CONTAINMENT,
            scope_evidence={"job_membership_complete": False},
        ),
    )

    assert snapshot.scope_complete is False
    assert snapshot.legacy_zero_proven is False


def test_empty_census_with_job_drained_scope_proves_zero(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))

    snapshot = observer.census(
        [],
        event_name="job-drained-empty",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof=_job_drained_proof(),
    )

    assert snapshot.scope_complete is True
    assert snapshot.zero_proof_authority == ScopeProofAuthority.JOB_OBJECT_DRAINED.value
    assert snapshot.legacy_zero_proven is True


def test_legacy_record_blocks_zero_even_with_complete_scope(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    snapshot = observer.census(
        [_record(101, str(tmp_path / "legacy" / "QI-Crawler.exe"), image_sha256=LEGACY_SHA)],
        event_name="legacy-with-complete-scope",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof=_complete_tree_proof(),
    )

    assert snapshot.legacy_count == 1
    assert snapshot.legacy_zero_proven is False


def test_unresolved_relevant_record_blocks_zero_with_complete_scope(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path), known_pids=frozenset({404}))
    snapshot = observer.census(
        [_record(404, None, access_status="ACCESS_DENIED")],
        event_name="unresolved-with-complete-scope",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof=_complete_tree_proof(),
    )

    assert snapshot.unresolved_relevant_count == 1
    assert snapshot.legacy_zero_proven is False


def test_malformed_scope_authority_fails_closed(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    snapshot = observer.census(
        [],
        event_name="malformed-authority",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof={
            "observed_scope": "F5_CONTROLLER_JOB_DRAINED",
            "scope_complete": True,
            "zero_proof_authority": "JOB_OBJECT_DRAINED",
            "scope_evidence": {"job_active_after": "zero"},
        },
    )

    assert snapshot.scope_complete is False
    assert snapshot.zero_proof_authority == ScopeProofAuthority.JOB_OBJECT_DRAINED.value
    assert snapshot.legacy_zero_proven is False


def test_unrecognized_scope_authority_fails_closed(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    snapshot = observer.census(
        [],
        event_name="unrecognized-authority",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof={
            "observed_scope": "F5_CONTROLLER_JOB_DRAINED",
            "scope_complete": True,
            "zero_proof_authority": "MACHINE_WIDE_SCAN",
            "scope_evidence": {},
        },
    )

    assert snapshot.scope_complete is False
    assert snapshot.zero_proof_authority is None
    assert snapshot.legacy_zero_proven is False


def test_scope_proof_receipt_exposes_bounded_job_authority() -> None:
    proof = _job_drained_proof()

    assert proof.proves_zero() is True
    assert proof.to_dict() == {
        "observed_scope": "F5_CONTROLLER_JOB_DRAINED",
        "scope_complete": True,
        "zero_proof_authority": "JOB_OBJECT_DRAINED",
        "scope_evidence": {
            "job_active_after": 0,
            "job_terminated": True,
            "receipt_persisted": True,
        },
    }


def test_scope_proof_metadata_is_bounded_and_immutable() -> None:
    proof = _job_drained_proof()

    with pytest.raises(TypeError):
        proof.scope_evidence["job_active_after"] = 1  # type: ignore[index]
    with pytest.raises(ValueError, match="SCOPE_PROOF"):
        ScopeProof.from_mapping(
            {
                "observed_scope": "F5_CONTROLLER_JOB_DRAINED",
                "scope_complete": False,
                "zero_proof_authority": None,
                "scope_evidence": {"unregistered": True},
            }
        )


def test_incomplete_p4_route_job_cannot_prove_zero(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    proof = ScopeProof(
        observed_scope="P4_ROUTE_JOB",
        scope_complete=True,
        zero_proof_authority=ScopeProofAuthority.JOB_OBJECT_DRAINED,
        scope_evidence={
            "job_terminated": True,
            "job_active_after": 1,
            "route_completion_observed": True,
            "route_job_complete": False,
            "lineage_complete": False,
            "total_job_processes": 2,
            "launcher_exit_code": 0,
        },
    )
    snapshot = observer.census(
        [],
        event_name="p4-incomplete",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof=proof,
    )

    assert snapshot.scope_complete is False
    assert snapshot.legacy_zero_proven is False


def test_incomplete_p5_route_set_cannot_prove_zero(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    proof = _composite_proof(completed=4)
    snapshot = observer.census(
        [],
        event_name="p5-incomplete-routes",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof=proof,
    )

    assert snapshot.scope_complete is False
    assert snapshot.legacy_zero_proven is False


def test_empty_census_without_scope_proof_does_not_prove_zero(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))

    snapshot = observer.census(
        [],
        event_name="scope-less-empty-census",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
    )

    assert snapshot.scope_complete is False
    assert snapshot.legacy_zero_proven is False


def test_controller_stub_and_external_process_are_distinct(tmp_path: Path) -> None:
    config = _config(tmp_path)
    observer = A3ProcessObserver(config)
    records = observer.classify_records(
        [
            _record(1, str(tmp_path / "controller" / "AO03-Controller.exe")),
            _record(2, str(tmp_path / "stub" / "QI-Crawler.exe")),
            _record(3, str(tmp_path.parent / "external" / "QI-Crawler.exe"), image_sha256=LEGACY_SHA),
        ]
    )

    assert [record.classification for record in records] == [
        ProcessClass.SANDBOX_CONTROLLER,
        ProcessClass.SANDBOX_STUB,
        ProcessClass.IRRELEVANT,
    ]


def test_unreadable_relevant_process_is_retained_and_blocks_zero(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path), known_pids=frozenset({404}))
    snapshot = observer.census(
        [
            _record(
                404,
                None,
                access_status="ACCESS_DENIED",
                evidence_source="pid-receipt",
            )
        ],
        event_name="unreadable",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
    )

    assert len(snapshot.records) == 1
    assert snapshot.records[0].classification == ProcessClass.UNRESOLVED_RELEVANT
    assert snapshot.unresolved_relevant_count == 1
    assert snapshot.legacy_zero_proven is False


def test_unknown_sandbox_process_is_not_legacy_or_dropped(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    snapshot = observer.census(
        [_record(505, str(tmp_path / "other" / "helper.exe"))],
        event_name="child-shape",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
        scope_proof=_complete_tree_proof(),
    )

    assert snapshot.records[0].classification == ProcessClass.SANDBOX_OTHER
    assert snapshot.legacy_count == 0
    assert snapshot.legacy_zero_proven is True


def test_process_identity_and_timestamp_are_preserved(tmp_path: Path) -> None:
    observer = A3ProcessObserver(_config(tmp_path))
    snapshot = observer.census(
        [
            _record(
                606,
                str(tmp_path / "legacy" / "QI-Crawler.exe"),
                image_sha256=LEGACY_SHA,
                start_time_utc="2026-09-10T01:02:03Z",
                command_line="QI-Crawler.exe --sandbox",
            )
        ],
        event_name="identity",
        positive_control_passed=True,
        known_legacy_roots_absent=False,
    )

    evidence = snapshot.records[0]
    assert evidence.pid == 606
    assert evidence.start_time_utc == "2026-09-10T01:02:03Z"
    assert evidence.command_line == "QI-Crawler.exe --sandbox"
    assert evidence.image_sha256 == LEGACY_SHA


def test_aggregate_mandatory_gates_fails_closed() -> None:
    assert aggregate_mandatory_gates({}) == ("HOLD", False)
    assert aggregate_mandatory_gates({"gate": None}) == ("HOLD", False)
    assert aggregate_mandatory_gates({"gate": False}) == ("HOLD", False)
    assert aggregate_mandatory_gates({"gate": True}) == ("PASS", True)


def test_f5_contract_refuses_omitted_recovery_and_manifest_gates() -> None:
    assert aggregate_mandatory_gates({"route_contract": True}, contract="F5_CANONICAL_V1") == (
        "HOLD", False
    )
    valid = {name: True for name in F5_CANONICAL_REQUIRED_GATES}
    assert aggregate_mandatory_gates(valid, contract="F5_CANONICAL_V1") == ("PASS", True)
    for missing in ("recovery_verified", "final_schema_expected", "final_logical_digest_unchanged",
                    "final_stub_identity", "evidence_manifest_complete"):
        incomplete = dict(valid)
        del incomplete[missing]
        assert aggregate_mandatory_gates(incomplete, contract="F5_CANONICAL_V1") == (
            "HOLD", False
        )
