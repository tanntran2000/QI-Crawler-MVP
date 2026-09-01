"""Fail-closed operational revision transition and bounded adjacent diff workflow."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from .market_intelligence.opportunity_contract import OpportunityIdentity
from .tender_revision_persistence import (
    PersistedRevisionEvent,
    TenderRevisionPersistence,
    TenderRevisionPersistenceError,
)


class RevisionTransitionError(ValueError):
    """Raised when a revision transition cannot be evaluated safely."""


class RevisionDecision(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ACCEPT = "ACCEPTED"
    REJECT = "REJECTED"


class RevisionTransitionOutcome(StrEnum):
    INITIAL_ACCEPTED = "INITIAL_ACCEPTED"
    ACCEPTED_PENDING = "ACCEPTED_PENDING"
    ADVANCED = "ADVANCED"
    REJECTED = "REJECTED"
    NO_DOWNGRADE = "NO_DOWNGRADE"
    NO_CHANGE = "NO_CHANGE"
    HOLD = "HOLD"


class SourceDiffState(StrEnum):
    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"
    ADDED = "ADDED"
    REMOVED_FROM_NEW_REVISION = "REMOVED_FROM_NEW_REVISION"
    UNKNOWN_RELATION = "UNKNOWN_RELATION"


@dataclass(frozen=True, slots=True)
class OperationalRevision:
    release_id: int
    identity: OpportunityIdentity
    event_id: int

    @property
    def base_id(self) -> str:
        return self.identity.base_id

    @property
    def revision(self) -> str:
        return self.identity.revision or ""


@dataclass(frozen=True, slots=True)
class RevisionDiff:
    key: str
    state: SourceDiffState
    previous_sha256: str | None
    latest_sha256: str | None


class AdjacentRevisionDiff(Mapping[str, RevisionDiff]):
    """Mapping-like bounded comparison, with deterministic change entries."""

    def __init__(self, changes: tuple[RevisionDiff, ...]):
        self.changes = changes
        self._by_key = {change.key: change for change in changes}

    def __getitem__(self, key: str) -> RevisionDiff:
        return self._by_key[key]

    def __iter__(self):
        return iter(self._by_key)

    def __len__(self) -> int:
        return len(self._by_key)

    @property
    def states(self) -> tuple[SourceDiffState, ...]:
        return tuple(change.state for change in self.changes)


@dataclass(frozen=True, slots=True)
class RevisionTransitionResult:
    outcome: RevisionTransitionOutcome
    previous: OperationalRevision | None
    latest: OperationalRevision | None
    event: PersistedRevisionEvent | None = None
    pending: PersistedRevisionEvent | None = None


class TenderRevisionTransitionService:
    """Application workflow enforcing latest-forward-only revision decisions."""

    def __init__(self, persistence: TenderRevisionPersistence):
        self.persistence = persistence

    def operational_latest(self, case_id: str) -> OperationalRevision | None:
        return self._operational(self.persistence.latest_accepted(case_id))

    def pending_transition(self, case_id: str) -> PersistedRevisionEvent | None:
        return self.persistence.latest_pending(case_id)

    def transition(
        self,
        case_id: str,
        release_id: int,
        *,
        decision: RevisionDecision | str | None,
        actor: str,
        reason: str,
        evidence: str,
    ) -> RevisionTransitionResult:
        try:
            normalized = RevisionDecision(str(decision or "").strip().upper())
        except ValueError as exc:
            raise RevisionTransitionError("decision is required") from exc
        try:
            release = self.persistence.release_record(case_id, release_id)
            current_event = self.persistence.latest_accepted(case_id)
            pending = self.persistence.latest_pending(case_id)
        except TenderRevisionPersistenceError as exc:
            raise RevisionTransitionError(str(exc)) from exc
        identity = OpportunityIdentity.from_raw(release.raw_id)
        current = self._operational(current_event)
        previous = current
        if current is not None and identity.base_id != current.base_id:
            return RevisionTransitionResult(
                RevisionTransitionOutcome.HOLD, previous, current, pending=pending
            )
        if current is not None:
            current_number = self._revision_number(current.revision)
            incoming_number = self._revision_number(identity.revision)
            if normalized is RevisionDecision.ACCEPTED and incoming_number < current_number:
                return RevisionTransitionResult(
                    RevisionTransitionOutcome.NO_DOWNGRADE, previous, current, pending=pending
                )
            if normalized is RevisionDecision.ACCEPTED and incoming_number == current_number:
                event = self._record(
                    case_id, release_id, "ACCEPTED", actor=actor, reason=reason, evidence=evidence
                )
                return RevisionTransitionResult(
                    RevisionTransitionOutcome.NO_CHANGE, previous, current, event, pending
                )
            if normalized is RevisionDecision.ACCEPTED and incoming_number > current_number:
                if pending is not None and pending.release_id != release_id:
                    return RevisionTransitionResult(
                        RevisionTransitionOutcome.HOLD, previous, current, pending=pending
                    )
                if pending is not None and pending.release_id == release_id:
                    return RevisionTransitionResult(
                        RevisionTransitionOutcome.ACCEPTED_PENDING,
                        previous,
                        current,
                        pending,
                        pending,
                    )
                event = self._record(
                    case_id,
                    release_id,
                    "ACCEPTED_PENDING",
                    actor=actor,
                    reason=reason,
                    evidence=evidence,
                    from_release_id=current.release_id,
                    accepted_at=datetime.now(UTC),
                )
                return RevisionTransitionResult(
                    RevisionTransitionOutcome.ACCEPTED_PENDING, previous, current, event, event
                )
        try:
            event = self._record(
                case_id,
                release_id,
                normalized.value,
                actor=actor,
                reason=reason,
                evidence=evidence,
            )
        except TenderRevisionPersistenceError as exc:
            raise RevisionTransitionError(str(exc)) from exc
        latest = self._operational(event) if normalized is RevisionDecision.ACCEPTED else current
        outcome = (
            RevisionTransitionOutcome.INITIAL_ACCEPTED
            if normalized is RevisionDecision.ACCEPTED and current is None
            else RevisionTransitionOutcome.REJECTED
        )
        return RevisionTransitionResult(outcome, previous, latest, event, pending)

    def accept_revision(self, case_id: str, release_id: int, **kwargs) -> RevisionTransitionResult:
        return self.transition(case_id, release_id, decision=RevisionDecision.ACCEPTED, **kwargs)

    def reject_revision(self, case_id: str, release_id: int, **kwargs) -> RevisionTransitionResult:
        return self.transition(case_id, release_id, decision=RevisionDecision.REJECTED, **kwargs)

    record_transition = transition
    apply_decision = transition

    def activate_revision(
        self,
        case_id: str,
        release_id: int,
        *,
        actor: str,
        reason: str,
        evidence: str,
    ) -> RevisionTransitionResult:
        try:
            current_event = self.persistence.latest_accepted(case_id)
            pending = self.persistence.latest_pending(case_id)
            candidate = self.persistence.release_record(case_id, release_id)
        except TenderRevisionPersistenceError as exc:
            raise RevisionTransitionError(str(exc)) from exc
        current = self._operational(current_event)
        if pending is None or pending.release_id != release_id or current is None:
            return RevisionTransitionResult(RevisionTransitionOutcome.HOLD, current, current, pending=pending)
        candidate_identity = OpportunityIdentity.from_raw(candidate.raw_id)
        if candidate_identity.base_id != current.base_id:
            return RevisionTransitionResult(RevisionTransitionOutcome.HOLD, current, current, pending=pending)
        if self._revision_number(candidate_identity.revision) <= self._revision_number(current.revision):
            return RevisionTransitionResult(RevisionTransitionOutcome.HOLD, current, current, pending=pending)
        comparison = self.persistence.latest_comparison(
            case_id, pending.from_release_id or current.release_id, release_id
        )
        if comparison is None:
            return RevisionTransitionResult(RevisionTransitionOutcome.HOLD, current, current, pending=pending)
        event = self._record(
            case_id,
            release_id,
            "TRANSITION_ACTIVATED",
            actor=actor,
            reason=reason,
            evidence=evidence,
            from_release_id=pending.from_release_id,
            comparison_schema_version=comparison.comparison_schema_version,
            comparison_payload=comparison.comparison_payload,
            activated_at=datetime.now(UTC),
        )
        return RevisionTransitionResult(
            RevisionTransitionOutcome.ADVANCED,
            current,
            self._operational(event),
            event,
            None,
        )

    activate_pending_transition = activate_revision

    def compare_adjacent_revisions(
        self,
        case_id: str,
        previous_release_id: int,
        latest_release_id: int,
        *,
        previous_snapshot: Mapping[str, str] | None = None,
        latest_snapshot: Mapping[str, str] | None = None,
        new_source_observation_complete: bool = False,
        completeness_evidence: str | None = None,
        persist: bool = True,
        actor: str = "system",
        reason: str = "adjacent revision comparison",
        evidence: str = "bounded adjacent comparison",
    ) -> AdjacentRevisionDiff:
        try:
            previous = self.persistence.release_record(case_id, previous_release_id)
            latest = self.persistence.release_record(case_id, latest_release_id)
        except TenderRevisionPersistenceError as exc:
            raise RevisionTransitionError(str(exc)) from exc
        previous_identity = OpportunityIdentity.from_raw(previous.raw_id)
        latest_identity = OpportunityIdentity.from_raw(latest.raw_id)
        if previous_identity.base_id != latest_identity.base_id:
            raise RevisionTransitionError("adjacent revisions require one lineage")
        if self._revision_number(latest_identity.revision) - self._revision_number(previous_identity.revision) != 1:
            raise RevisionTransitionError("comparison is limited to adjacent revisions")
        previous_values = (
            dict(previous_snapshot)
            if previous_snapshot is not None
            else self.persistence.document_snapshot(case_id, previous_release_id)
        )
        latest_values = (
            dict(latest_snapshot)
            if latest_snapshot is not None
            else self.persistence.document_snapshot(case_id, latest_release_id)
        )
        changes = []
        for key in sorted(set(previous_values) | set(latest_values)):
            before = previous_values.get(key)
            after = latest_values.get(key)
            if before is None:
                state = SourceDiffState.ADDED
            elif after is None:
                state = (
                    SourceDiffState.REMOVED_FROM_NEW_REVISION
                    if new_source_observation_complete and str(completeness_evidence or "").strip()
                    else SourceDiffState.UNKNOWN_RELATION
                )
            elif self._sha(before) == self._sha(after):
                state = SourceDiffState.UNCHANGED
            else:
                state = SourceDiffState.CHANGED
            changes.append(RevisionDiff(key, state, before, after))
        diff = AdjacentRevisionDiff(tuple(changes))
        if persist:
            payload = json.dumps(
                {
                    "previous_release_id": previous_release_id,
                    "latest_release_id": latest_release_id,
                    "changes": [
                        {
                            "key": item.key,
                            "state": item.state.value,
                            "previous_sha256": item.previous_sha256,
                            "latest_sha256": item.latest_sha256,
                        }
                        for item in diff.changes
                    ],
                },
                sort_keys=True,
            )
            self.persistence.record_comparison(
                case_id,
                previous_release_id,
                latest_release_id,
                payload=payload,
                schema_version="adjacent-v1",
                actor=actor,
                reason=reason,
                evidence=evidence,
                source_observation_complete=new_source_observation_complete,
                completeness_evidence=completeness_evidence,
            )
        return diff

    compare_previous_latest = compare_adjacent_revisions
    adjacent_diff = compare_adjacent_revisions

    def _record(self, case_id: str, release_id: int, decision: str, **kwargs) -> PersistedRevisionEvent:
        return self.persistence.record_event(
            case_id,
            release_id,
            decision,
            **kwargs,
        )

    @staticmethod
    def _operational(event: PersistedRevisionEvent | None) -> OperationalRevision | None:
        if event is None:
            return None
        return OperationalRevision(event.release_id, event.identity, event.event_id)

    @staticmethod
    def _revision_number(value: str | None) -> int:
        if not value or not value.isdigit():
            raise RevisionTransitionError("revision must be numeric")
        return int(value)

    @staticmethod
    def _sha(value: object) -> str:
        return str(value).casefold()


__all__ = [
    "AdjacentRevisionDiff",
    "OperationalRevision",
    "RevisionDecision",
    "RevisionDiff",
    "RevisionTransitionError",
    "RevisionTransitionOutcome",
    "SourceDiffState",
    "TenderRevisionTransitionService",
]
