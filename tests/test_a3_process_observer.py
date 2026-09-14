from __future__ import annotations

from pathlib import Path

from tools.release.a3_process_observer import (
    F5_CANONICAL_REQUIRED_GATES,
    A3ProcessObserver,
    ObserverConfig,
    ProcessClass,
    aggregate_mandatory_gates,
)

LEGACY_SHA = "a" * 64


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
