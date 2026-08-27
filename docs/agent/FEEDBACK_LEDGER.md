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

### FB-0007 — Adopt the QI Knowledge and Verification System blueprint

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-BLUEPRINT-KVS-HANDOFF-01
Type: ARCHITECTURE
Authority: A0 HUMAN_DECISION
Observation: QI-KVS is a cross-cutting, versioned knowledge and verification
corpus boundary; it is not a new roadmap lane or an active implementation.
Evidence: approved Blueprint KVS Work Order.
Impact: Future rules must remain distinct from source truth, Ground Truth,
SOP decisions and evaluator code.
Suggestion: Record the QI-KVS principles, Product House placement and staged
promotion lifecycle in the master roadmap.
Scope change required: NO
Response: Blueprint revision 1.2 records the target boundary and gates without
activating Knowledge DB/API/MCP or AI implementation.
Disposition: ACCEPTED; PROMOTED to durable roadmap governance.
Promoted to: docs/agent/MASTER_ROADMAP.md
```

### FB-0008 — Strengthen roadmap read and handoff freshness gates

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-BLUEPRINT-KVS-HANDOFF-01
Type: HANDOFF / PROCESS
Authority: A0 HUMAN_DECISION
Observation: A stale roadmap or post-merge handoff can give an agent false
execution context even when Git/GitHub is the live repository authority.
Evidence: approved Blueprint KVS Work Order and prior handoff lifecycle audits.
Impact: Agents may start from an unresolved frontier, stale Parent state or
missing audited-head/provenance fields.
Suggestion: Require a roadmap entry gate, bounded FULL/DELTA/NO-RE-READ modes,
and a post-merge reconciliation before the next technical handoff.
Scope change required: NO
Response: Added the entry, freshness and strict handoff contracts to the
durable governance documents; CURRENT remains the active snapshot authority.
Disposition: ACCEPTED; PROMOTED to durable governance.
Promoted to: AGENTS.md; docs/agent/MEMORY_INDEX.md;
docs/agent/OPERATING_MODEL.md; docs/agent/HUMAN_COLLABORATION.md;
docs/agent/LOCAL_STAGED_INTEGRATION.md
```

### FB-0009 — Direct-object independent review is the default

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-MI-TBMT-02C-1 governance correction
Type: PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: When exact Git objects are available, the Reviewer must perform
the independent local audit directly and return an INDEPENDENT_REVIEW_PACKET.
Evidence: approved material governance correction before 02C-1 review.
Impact: Requiring a manually exported patch by default weakens object
authority and adds unnecessary handoff friction.
Suggestion: Audit BASE_SHA..HEAD_SHA directly; use a patch only as fallback.
Scope change required: NO
Response: Added direct-object review, Reviewer authority ordering and the
standard independent packet to the durable governance spine.
Disposition: ACCEPTED; PROMOTED to durable governance.
Promoted to: AGENTS.md; docs/agent/OPERATING_MODEL.md;
docs/agent/HUMAN_COLLABORATION.md; docs/agent/LOCAL_STAGED_INTEGRATION.md;
docs/agent/MEMORY_INDEX.md
```

### FB-0010 — Require immediate routing of material knowledge into Context Spine

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-MI-TBMT-02C / governance correction
Type: PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: Material beneficial changes, newly verified facts, accepted
governance/process rules, systemic lessons and other durable project knowledge
must be routed to the correct Spine authority immediately at the governed
transition instead of remaining only in chat.
Impact: Prevents continuity from depending on chat history and keeps roadmap,
memory, failure knowledge, lessons, feedback and handoff aligned.
Scope change required: NO
Response: Added the SPINE IMMEDIATE PROMOTION gate and required Spine audit
fields to the governance flow.
Disposition: ACCEPTED / PROMOTED
Promoted to: AGENTS.md; docs/agent/OPERATING_MODEL.md;
docs/agent/HUMAN_COLLABORATION.md; docs/agent/LOCAL_STAGED_INTEGRATION.md;
docs/agent/MEMORY_INDEX.md
```

### FB-0011 — Park Parent-centric governance reform until TBMT closeout

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-MI-TBMT-02C-4
Type: PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: WP-MI-TBMT-02C completes under existing governance; do not
rewrite AGENTS, MASTER_ROADMAP or integration law mid-Parent.
Evidence: approved 02C-4 acceptance Work Order.
Impact: Keeps the active Parent's acceptance and audit flow bounded while
preserving a dedicated post-Parent governance reform decision.
Suggestion: After TBMT Parent closeout, evaluate a Parent-centric flow where
Micro-WPs are locally verified/audited and Parent-WPs own PR/CI/merge gates;
Planner and Reviewer remain separate authorities.
Scope change required: NO
Response: The Parent closeout condition was reached when PR #60 merged, but
the governance law is not rewritten by this reconciliation. Route the
proposal toward `WP-GOV-INTEGRATION-V2-01 — Parent-Centric Integration & CI
Governance` after the Human-requested full local bug audit.
Disposition: ACCEPTED / QUEUED_FOR_POST_AUDIT_PROMOTION
Promoted to: WP-GOV-INTEGRATION-V2-01 (queued after full local bug audit)
```

### FB-0012 — Temporary CI waiver after exact-head runner failures

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-MI-TBMT-02C
Type: CI / PROCESS
Authority: A0 HUMAN_DECISION
Observation: Hosted CI was held after three exact-head pre-execution
failures on PR #60 because GitHub Actions did not allocate a runner.
Evidence: CI run 32865755230; attempts 1/2/3 failed before any job step ran.
Impact: The existing temporary local-staged-integration / CI-waiver flow may
resume for this Parent without treating the hosted result as product failure.
Decision: This is a temporary exception, not CI PASS; PENDING_RETRO_CI remains
YES, official Team Bid release remains blocked, and the normal hosted-CI gate
returns when runner execution is healthy.
Scope change required: NO
Response: Recorded the waiver in CURRENT.md and kept durable governance law
unchanged; future Parent-centric governance FB-0011 remains separate and
inactive.
Disposition: ACCEPTED
Promoted to: N/A — temporary operational waiver
```

### FB-0013 — Full local bug audit before further governance or product work

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-MI-TBMT-02C post-merge reconciliation
Type: TEST_GAP / PROCESS
Authority: A0 HUMAN_DECISION
Observation: After the 02C closeout, run a fresh full local audit/test sweep
and prioritize finding defects before continuing with governance or product
work.
Evidence: Human post-merge instruction following PR #60 and the active
full-repository audit hold.
Impact: Prevents unresolved runtime, logic and architecture defects from
being hidden by a governance transition or a new feature slice.
Suggestion: The audit must establish evidence and root cause first; it must
not silently fix defects. Any correction requires a separate bounded Work
Package and independent review.
Scope change required: NO
Response: Recorded as the exactly-one next action in CURRENT.md; no correction
is authorized by this feedback entry.
Disposition: ACCEPTED / QUEUED_FOR_NEXT_WORK_PACKAGE
Promoted to: CURRENT.md execution state; future findings route to the
applicable failure/lesson authority
```

### FB-0014 — Human priority override for Roadmap Delta

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-ROADMAP-DELTA-01
Type: PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: The full local bug-hunt remains desired but is deferred; the
MASTER_ROADMAP_DELTA governance WP becomes the immediate next work package.
Evidence: Human A0 decision in the Roadmap Delta Work Order after PR #61.
Impact: Changes execution order without invalidating the bug-hunt's value or
future intent.
Suggestion: Keep the bug-hunt parked and run it after the Delta governance
transition unless Human authority changes the order again.
Scope change required: NO
Response: Recorded `BUG_HUNT = PARKED_BY_HUMAN_A0` and
`MASTER_ROADMAP_DELTA = IMPLEMENTING` in CURRENT.md.
Disposition: ACCEPTED / EXECUTION_ORDER_OVERRIDE_ONLY
Promoted to: CURRENT.md; MASTER_ROADMAP_DELTA.md
```

### FB-0015 — Reviewer continuity and documentation freshness authority

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-ROADMAP-DELTA-01
Type: PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: The independent Reviewer must compare the current WP and Builder
output with MASTER_ROADMAP_DELTA, MASTER_ROADMAP and relevant Context Spine
files, then report stale or missing promotion to the Planner.
Evidence: Human A0 Reviewer continuity decision in the Roadmap Delta Work Order.
Impact: Prevents implementation from proceeding with stale organizational
knowledge or a missing roadmap promotion.
Suggestion: Require implementation, roadmap-fit and Spine-freshness audits;
the Reviewer remains independent, non-writing and non-Planner.
Scope change required: NO
Response: Added the Delta read gate, Reviewer bridge and freshness fields to
the governance contracts; no Reviewer edit or promotion authority is added.
Independent audit: PASS
PR #62: MERGED
Disposition: PROMOTED / DURABLE_GOVERNANCE_STATE
Promoted to: AGENTS.md; docs/agent/MEMORY_INDEX.md;
docs/agent/OPERATING_MODEL.md; docs/agent/LOCAL_STAGED_INTEGRATION.md;
docs/agent/MASTER_ROADMAP_DELTA.md
```

### FB-0016 — Planner Human Intent & Strategic Continuity

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-PLANNER-CONTINUITY-01
Type: GOVERNANCE / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: Planner is the primary strategic collaboration interface where
Human and Planner discuss work before Builder execution. Planner preserves
material Human intent, gives every material statement an explicit disposition,
routes current-scope requirements into the Builder Work Order, and routes
future or out-of-scope intent to the correct Context Spine authority.
Impact: Planner provides strategic synthesis across the three-pole development
model while Human retains final material authority; future roles receive
strategic handoff context and Builder-readable contracts with Reviewer challenge
criteria.
Constraint: Planner interprets Reviewer findings after audit but may not become
Reviewer, rewrite HOLD into PASS without governed resolution, or replace Human
authority.
Evidence: Human A0 decision recorded for the post-merge Roadmap Delta
transition.
Independent audit: PASS
PR #64: MERGED
Merged feature head: db19f42985030f2b154804f959fca615c523a06e
Merge commit: d10445fc2ffc92e810f0d6258160151efc1c846f
Scope change required: NO
Response: Implemented, independently audited and merged as durable governance
through the Planner Continuity Work Package.
Disposition: PROMOTED / DURABLE_GOVERNANCE_STATE
Promoted to: CURRENT.md; MASTER_ROADMAP_DELTA.md; PROJECT_MEMORY.md
```

### FB-0017 — Planner Review Orchestration & Role Continuity

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-PLANNER-CONTINUITY-01
Type: GOVERNANCE / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: Planner analyzes Builder output before constructing a WP-specific,
  risk-oriented Reviewer challenge; after review, Planner directly reconciles
  Master Roadmap, Delta, Context Spine, live state and Human intent before
  sending its own strategic conclusion to Human.
Required contract: Explicit role contracts, ROLE_ENTRY_GATE,
  LATEST_WP_SPINE_SYNC_AUDIT and PLANNER_POST_REVIEW_DECISION are mandatory
  for future agents and takeovers.
Impact: Preserves Human intent, Reviewer independence and evidence-backed
  strategic continuity across the three-pole development model.
Evidence: Human A0 decision captured in Planner Continuity M0.
Independent audit: PASS
PR #64: MERGED
Merged feature head: db19f42985030f2b154804f959fca615c523a06e
Merge commit: d10445fc2ffc92e810f0d6258160151efc1c846f
Scope change required: NO
Response: Implemented, independently audited and merged as durable governance
through the Planner Continuity Work Package; no product capability change is
implied.
Disposition: PROMOTED / DURABLE_GOVERNANCE_STATE
Promoted to: CURRENT.md; MASTER_ROADMAP_DELTA.md; PROJECT_MEMORY.md
```

### FB-0018 — Builder Implementation Integrity & Evidence Discipline

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-BUILDER-INTEGRITY-01 / FUTURE
Type: GOVERNANCE / PROCESS
Authority: A0 HUMAN_DECISION
Observation: Future Builder Integrity governance must defend authoritative
  layers, preserve TDD RED/GREEN traceability, require realistic tests and
  Builder preflight, enforce claim discipline, avoid mocks proving the thing
  under test, distinguish local PASS from CI PASS, and distinguish Builder
  done from Reviewer PASS.
Impact: Prevents evidence overclaiming and implementation drift without
  changing the current Planner Continuity scope.
Evidence: Previously approved Human A0 Builder Integrity direction, captured
  during Planner Continuity M0.
Scope change required: NO
Response: Staged as a future governance Delta only; no Builder Integrity
  implementation is authorized in this Parent.
Disposition: ACCEPTED / QUEUED_FOR_WP_GOV_BUILDER_INTEGRITY_01
Promoted to: CURRENT.md; MASTER_ROADMAP_DELTA.md
```
