from __future__ import annotations

from pathlib import Path

import pytest

from tools.release.a3_process_observer import (
    F5_CANONICAL_REQUIRED_GATES,
    A3ProcessObserver,
    ObserverConfig,
    ProcessClass,
    aggregate_mandatory_gates,
)

LEGACY_SHA = "a" * 64
STUB_SHA = "b" * 64


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
    )

    assert snapshot.legacy_count == 0
    assert snapshot.unresolved_relevant_count == 0
    assert snapshot.legacy_zero_proven is True


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
