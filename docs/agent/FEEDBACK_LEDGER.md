# Feedback Ledger

This ledger records bounded, material feedback shared by Team Bid and agents.
It is not a transcript. One entry should represent one observation or
decision and must have an explicit lifecycle state.

## Record format

```text
FB-xxxx
State: OPEN | REVIEWED | ACCEPTED | REJECTED | PARKED | PROMOTED | RESOLVED
Author:
Role:
WP:
Type: BUSINESS | ARCHITECTURE | DEFECT | PROCESS | PLUGIN | TEST_GAP | HANDOFF | CI | OTHER
Authority:
Observation:
Evidence:
Impact:
Suggestion:
Scope change required: YES / NO
Response:
Disposition:
Promoted to:
```

## Authority levels

- **A0 HUMAN_DECISION** — explicit business or merge decision.
- **A1 VERIFIED_SOURCE_GROUND_TRUTH** — verified external/source evidence.
- **A2 MERGED_CODE_MACHINE_EVIDENCE** — reproducible evidence on `main`.
- **A3 REVIEW_FINDING** — independent audit finding.
- **A4 IMPLEMENTATION_FINDING** — builder observation.
- **A5 PROPOSAL_HYPOTHESIS** — unverified suggestion.

Lower authority never overrides higher authority. A scope change requires a
new approved Work Order or explicit human approval; it must not be smuggled
into a feedback entry.

## Retention

Keep roughly 20–30 active material entries. Compact resolved, rejected, and
promoted history into concise records rather than allowing an unbounded chat
log to grow.

## Active feedback

### FB-0001 — Reconcile stale local baseline before branching

```text
State: RESOLVED
Author: PR #40 audit
Role: REVIEWER_AUDITOR
WP: WP-GOV-01
Type: HANDOFF
Authority: A3 REVIEW_FINDING
Observation: Local main was one commit behind the verified remote main at
entry, so the requested Work Order base was not initially present locally.
Evidence: local e345256 was fast-forwarded to remote 07ef548 before branch
creation.
Impact: Starting from stale Git state could produce an invalid baseline and
misleading handoff/CI conclusions.
Suggestion: Reconcile main with fetch + fast-forward verification before any
branch or file write.
Scope change required: NO
Response: The checkout was reconciled and the Entry Review was repeated before
the WP approval lease was used.
Disposition: PROMOTED to the durable LAW 9 read-in and Memory Index workflow.
Promoted to: AGENTS.md LAW 9; docs/agent/MEMORY_INDEX.md
```

### FB-0002 — Make plugin execution auditable

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-REL-01 corrective Stage A
Type: PLUGIN
Authority: A0 HUMAN_DECISION
Observation: Earlier technical prompts named CodeGraph and Superpowers but
did not require auditable execution evidence.
Evidence: Corrective Stage A Work Order, section 0–2.
Impact: Plugin use could be asserted without proving impact analysis,
systematic debugging, TDD, or verification workflow execution.
Suggestion: Applicable prompts and handoffs must name required plugins/skills,
invocation timing, expected analysis, fallback, and returned evidence.
Scope change required: NO
Response: Added a durable Plugin Execution Contract to AGENTS.md and aligned
the Human Collaboration and Operating Model documents.
Disposition: PROMOTED to durable governance.
Promoted to: AGENTS.md Plugin execution contract; docs/agent/HUMAN_COLLABORATION.md; docs/agent/OPERATING_MODEL.md
```
