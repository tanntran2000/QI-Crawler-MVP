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

### FB-0003 — Keep SA Excel source identity explicit

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-MI-SRC-01
Type: BUSINESS
Authority: A0 HUMAN_DECISION
Observation: KHMT and TBMT workbooks share Excel as a transport format but
belong to separate PL and IB namespaces; filename-only routing is unsafe.
Evidence: approved SA Excel Source Routing Work Order and real KHMT/TBMT
workbook header/identity inspection.
Impact: Sending TBMT into the KHMT importer creates false missing-header
errors; guessing a source can create invalid Bid Radar state.
Suggestion: Detect filename/schema/identity evidence, require a named human
override for conflicts or unknown filenames, and keep correction history
append-only.
Scope change required: NO
Response: Added bounded source detection, controlled TBMT recognition,
append-only source-type review events, and regression coverage.
Disposition: ACCEPTED in WP-MI-SRC-01; TBMT import remains deferred.
Promoted to: docs/agent/HUMAN_COLLABORATION.md and source-type routing contract
```

### FB-0004 — Require tiered PRE/POST documentation checkpoints

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-DOC-LIFECYCLE-SYNC
Type: PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: Every Parent and Micro Work Package must have PRE and POST
documentation checkpoints, using a tiered model so ordinary editing/testing
does not create unnecessary document, commit or history churn.
Evidence: approved WP-GOV-DOC-LIFECYCLE-SYNC Work Order.
Impact: Handoffs remain current and actionable without becoming a diary.
Suggestion: Require lightweight Micro PRE/POST state and full history only for
Parent or material-event transitions.
Scope change required: NO
Response: Added to the documentation lifecycle contract and operating rules.
Disposition: ACCEPTED; durable governance update in this WP.
Promoted to: AGENTS.md; docs/agent/OPERATING_MODEL.md;
docs/agent/LOCAL_STAGED_INTEGRATION.md; docs/agent/MEMORY_INDEX.md
```

### FB-0005 — Restore hosted-CI gating after quota recovery

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-DOC-LIFECYCLE-SYNC
Type: CI / PROCESS
Authority: A0 HUMAN_DECISION
Observation: Hosted-CI-gated GitHub integration must return when GitHub
Actions quota is restored and the required workflow executes normally, but it
must not be activated before quota restoration.
Evidence: approved WP-GOV-DOC-LIFECYCLE-SYNC Work Order.
Impact: Temporary local staged integration remains distinct from the future
default hosted-CI mode; unavailable quota is never CI PASS.
Suggestion: Keep the activation condition explicit and require Human authority
for any later exception.
Scope change required: NO
Response: Added the activation condition without changing the current waiver.
Disposition: ACCEPTED; durable governance update in this WP.
Promoted to: AGENTS.md; docs/agent/LOCAL_STAGED_INTEGRATION.md
```

### FB-0006 — Read-before-work with context-economical read modes

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-DOC-LIFECYCLE-SYNC
Type: PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: Agents must read authoritative files before work and before
prompt generation, including the blueprint when required, while selecting
FULL, DELTA or NO-RE-READ so unchanged context is not repeatedly loaded.
Impact: Prevents stale-context execution without wasting time, tokens or
hosted-CI quota on unnecessary repeated reads.
Scope change required: NO
Response: Added an explicit read-mode selector, Parent/Micro distinction and
Prompt Writer selector contract.
Disposition: ACCEPTED; durable governance update in this correction.
Promoted to: docs/agent/MEMORY_INDEX.md; docs/agent/MASTER_ROADMAP.md;
docs/agent/HUMAN_COLLABORATION.md
```
