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

### FB-0019 — Role-specific Planner Prompt Profiles

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-AGENT-PROMPT-PROFILES-01 / M0
Type: GOVERNANCE / PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: Prompts must not be written ad hoc. Planner must study each
  role's canonical duties and authority before constructing a task. Builder
  and Reviewer require distinct role-specific prompt contracts; Builder scope
  governs execution and proof, while Reviewer scope governs independent
  challenge and must not presuppose PASS. Reviewer challenge follows review of
  actual Builder output/evidence, and Planner remains engaged through Builder
  result, Reviewer result, CI/remote integration and post-state transitions.
Impact: Preserves role separation, Human intent, independent review and
  evidence-backed completion across future Builder and Reviewer work.
Evidence: Human A0 governance direction captured in M0 after PR #66 merge.
Suggestion: Implement canonical Planner-generated Builder and Reviewer prompt
  profiles in later bounded micro-WPs with explicit entry, scope and evidence
  contracts.
Scope change required: NO
Response: Implemented and corrected as canonical Builder and Reviewer
  prompt-profile contracts; PR #67 merged the audited result to main and the
  exact-head CI run `33057122566` passed all required jobs.
Disposition: PROMOTED_DURABLE_GOVERNANCE_STATE
Promoted to: AGENTS.md; docs/agent/OPERATING_MODEL.md;
  docs/agent/HUMAN_COLLABORATION.md; docs/agent/LOCAL_STAGED_INTEGRATION.md;
  docs/agent/PROJECT_MEMORY.md
```

### FB-0020 — Large Bounded Batch Execution & Review

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-AGENT-PROMPT-PROFILES-01 / M0
Type: GOVERNANCE / PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: Builder and Reviewer should receive larger coherent workloads so
  project execution does not stall on trivial command/commit boundaries.
  Larger Work Packages must remain bounded and auditable. Builder should
  receive an approval lease covering the authorized batch, rather than
  requiring reapproval for each safe in-scope command, git add, local commit,
  targeted test, or normal stage transition. A large Builder batch should
  retain internal stages, targeted verification, semantic local commits,
  final batch verification and explicit stop conditions. Increasing Builder
  workload must not weaken architecture invariants, data safety, test
  discipline, evidence quality, scope boundaries, or Human authority.
  Reviewer workload should also be larger: audit the coherent batch rather
  than every trivial micro-change. Reviewer must compensate for the larger
  audit object with a stronger risk-oriented challenge covering architecture,
  invariants, implementation logic, test fitness, compatibility,
  recovery/data safety, claim accuracy and applicable organizational-memory
  freshness. Independent Reviewer separation remains mandatory. Material risk
  boundaries may still require an intermediate stop/checkpoint.
  Final principle: BIGGER WORK PACKAGE + SMALL SEMANTIC COMMITS + STAGE
  SELF-VERIFICATION + STRONG INDEPENDENT REVIEW + STOP ON MATERIAL RISK =
  FASTER EXECUTION WITHOUT LOWERING GOVERNANCE QUALITY.
Impact: Reduce Human/Planner/Builder round-trip latency while preserving
  technical stability and proof-gated delivery.
Evidence: Human A0 governance direction captured in M0-C2 after the original
  M0 commit.
Response: Implemented and corrected as a large bounded batch and Approval
  Lease contract with internal stage safety; PR #67 merged the audited result
  to main and the exact-head CI run `33057122566` passed all required jobs.
Disposition: PROMOTED_DURABLE_GOVERNANCE_STATE
Promoted to: AGENTS.md; docs/agent/OPERATING_MODEL.md;
  docs/agent/HUMAN_COLLABORATION.md; docs/agent/LOCAL_STAGED_INTEGRATION.md;
  docs/agent/PROJECT_MEMORY.md
```

### FB-0021 — CURRENT Write Authority & Transition Ownership

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-GOV-AGENT-PROMPT-PROFILES-01 / M1 correction
Type: GOVERNANCE / PROCESS / HANDOFF
Authority: A0 HUMAN_DECISION
Observation: CURRENT.md is an active handoff and transition authority, not a
  command/test/edit diary. It is conditionally writable by the active
  BUILDER_SINGLE_WRITER only when CURRENT is in approved WRITE_SCOPE, a
  governed transition trigger exists, and each fact has evidence and authority
  provenance. The Builder may record observable facts and already-resolved
  Reviewer, Planner or Human decisions from exact evidence, but may not
  originate those decisions. RECORD_AUTHORITY != ORIGINATE_AUTHORITY.
Impact: Preserves handoff freshness, role separation, authority provenance and
  evidence-backed transitions without turning a Large Batch into a diary.
Evidence: Human A0 requirement recorded in the M1 independent audit finding
  F-001 and this bounded forward-correction Work Order.
Suggestion: Keep CURRENT updates at governed transition frequency and reconcile
  authority-derived values from exact source evidence.
Scope change required: NO
Response: Implemented in the M1 correction candidate; independent re-audit
  passed, PR #67 merged the result to main and the exact-head CI run
  `33057122566` passed all required jobs.
Disposition: PROMOTED_DURABLE_GOVERNANCE_STATE
Promoted to: AGENTS.md; docs/agent/OPERATING_MODEL.md;
  docs/agent/LOCAL_STAGED_INTEGRATION.md; docs/agent/PROJECT_MEMORY.md
```

### FB-0022 — Warehouse Domain Authority Model

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-WH-MIN-01
Type: ARCHITECTURE
Authority: A0 HUMAN_DECISION
Decision: OPTION_B_DOMAIN_FIRST_TENDERCASE
Observation: Filesystem/folder presentation may exist later, but TenderCase,
  domain identity and database identity remain authoritative. BUSINESS_FOLDER
  != DATABASE_IDENTITY, FILENAME != DOCUMENT_IDENTITY and DOCUMENT_ROLE !=
  PACKAGE_MEMBERSHIP. Option C / filesystem-first authority is not selected
  for the current architecture.
Impact: Keeps Warehouse lifecycle meaning in Domain Core and prevents a
  presentation folder, filename or document role from becoming package
  identity or membership authority.
Evidence: Human A0 approval for WP-WH-MIN-01 Stage 0 and Option B, now backed
  by merged PR #69 and its independently audited Minimum Safe Warehouse slice.
Scope change required: NO
Response: Preserved as the Option B authority anchor and reconciled with the
  merged Minimum Safe Warehouse facts; broader Warehouse work remains bounded.
Disposition: PROMOTED_DURABLE_GOVERNANCE_STATE after PR #69
Promoted to: docs/agent_handoff/CURRENT.md; docs/agent/MASTER_ROADMAP.md;
  docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent/PROJECT_MEMORY.md
```

### FB-0023 — Template-Driven Controlled Document Generation Boundary

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: POST-WAREHOUSE ROADMAP RECONCILIATION
Type: ARCHITECTURE
Authority: A0 HUMAN_DECISION
Observation: Two reviewed document-generation references align with the
  existing Bid Assistant / Output lane and support a generic template-driven,
  Human-reviewed controlled-output architecture.
Evidence: Human architecture discussion and Planner reconciliation after
  WP-WH-MIN-01 completion.
Impact: Provides a reusable future path for DOCX/forms/contracts and other
  approved document types without allowing generated output, filename,
  template, reference sample or AI inference to become source/business
  authority.
Suggestion: Enrich existing Lane 8 instead of creating a new roadmap lane.
  Use immutable/versioned templates, canonical fields,
  SOURCE_BACKED/HUMAN_INPUT/DERIVED provenance, readiness gates, controlled
  rendering, post-render validation and Human final review.
Scope change required: NO_CURRENT_IMPLEMENTATION
Response: Accepted as architecture / roadmap evolution only.
Disposition: ACCEPTED / PARKED_FOR_FUTURE_OUTPUT_WP
Promoted to: docs/agent/MASTER_ROADMAP.md;
  docs/agent/MASTER_ROADMAP_DELTA.md / RD-0011
```

### FB-0024 — Canonical Checkout Identity Gate

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-WH-OPS-01 post-merge closeout
Type: PROCESS / HANDOFF / GOVERNANCE
Authority: A0 HUMAN_DECISION
Observation: Builder and Reviewer can appear to use the same repository while
  actually operating in different filesystem checkouts and Git object databases.
Evidence: Builder canonical checkout was
  C:\Users\Admin\Desktop\QI Technology\QI Crawler\egp-crawler-python;
  Reviewer checkout was D:\QI Technology\QI Crawler\egp-crawler-python. The D:
  checkout could not resolve 42c09df..., while the C: checkout could.
Impact: Exact-object audits and baseline conclusions become unsafe without an
  explicit checkout identity proof.
Human decision: Every future agent proves the exact canonical folder and
  repository identity; Builder and Reviewer independently compare the proof.
Scope change required: NO
Response: Added a canonical checkout identity gate and distinct WRONG_CHECKOUT
  hold across the durable role, handoff and memory contracts.
Disposition: PROMOTED_DURABLE_GOVERNANCE_STATE
Promoted to: AGENTS.md; docs/agent/OPERATING_MODEL.md;
  docs/agent/HUMAN_COLLABORATION.md; docs/agent/LOCAL_STAGED_INTEGRATION.md;
  docs/agent/MEMORY_INDEX.md
```

### FB-0025 — Defer deep-review hardening until large Warehouse OPS Parent closes

```text
State: RESOLVED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-WH-OPS-01
Type: PROCESS / DEFECT / EXECUTION_ORDER
Authority: A0 HUMAN_DECISION
Observation: Potential crawler defects from earlier deep review were deferred
  until the bounded OPS-01 Parent closed.
Evidence: Planner revalidated the highest-priority findings after WP-WH-OPS-01;
  BUG-04, BUG-02 and BUG-11 were confirmed, Human approved
  WP-HARDEN-SOURCE-INTEGRITY-01, PR #74 merged independently audited fixes,
  and post-merge Python CI and CodeQL passed.
Impact: The confirmed source-integrity findings are now durably hardened
  without expanding the completed OPS-01 evidence.
Suggestion: Preserve the remaining stale-child reconciliation risk as a
  separate bounded follow-up; do not treat this hardening as full source
  history reconciliation.
Scope change required: NO
Response: The deferral condition was satisfied by PR #72 merge and the
  confirmed findings were resolved by independently audited PR #74.
Disposition: RESOLVED / PROMOTED_TO_MEM_020_AND_FAILURE_MEMORY
Promoted to: docs/agent/PROJECT_MEMORY.md; docs/agent/KNOWN_FAILURE_MODES.md;
  docs/agent/FEEDBACK_LEDGER.md
```

### FB-0026 — Persisted child rows may outlive a source-side deletion

```text
State: RESOLVED
Author: Independent Reviewer
Role: REVIEWER_AUDITOR
WP: WP-HARDEN-SOURCE-INTEGRITY-01 → WP-HARDEN-SOURCE-CHILD-RECONCILIATION-01
Type: DEFECT / TEST_GAP
Authority: A3 REVIEW_FINDING
Observation: Semantic hashing reflects the current parsed Attachment/TenderItem
  source snapshot, while persistence had historically been additive child upsert;
  an absent child could remain in the database.
Evidence: A3 review finding was followed by runtime reproduction V2 on current
  main, which confirmed the suspected stale-child behavior.
Impact: The canonical parsed source snapshot could differ from retained
  persisted child rows after source-side deletion or removal.
Suggestion: Revalidate the bounded risk before deciding on implementation; do
  not treat the original observation as runtime-confirmed at initial review time.
Scope change required: NO
Response: Runtime V2 confirmed the suspected defect; Human approved
  WP-HARDEN-SOURCE-CHILD-RECONCILIATION-01; TDD implementation was independently
  audited and merged as PR #76; post-merge Python CI and CodeQL PASS.
Disposition: RESOLVED / PROMOTED_TO_FM_014_AND_MEM_021
Promoted to: docs/agent/KNOWN_FAILURE_MODES.md / FM-014
  docs/agent/PROJECT_MEMORY.md / MEM-021
  docs/agent/LESSONS.md / Lesson 14
```

### FB-0027 — End current hardening sequence and return to Team Bid basic crawler

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
Authority: A0 HUMAN_DECISION
Type: PROCESS / EXECUTION_ORDER / PRODUCT_PRIORITY
WP: WP-HARDEN-SOURCE-CHILD-RECONCILIATION-01 / TERMINAL CLOSEOUT
Decision: CURRENT_HARDENING_SEQUENCE = CLOSED
NEXT_PRODUCT_DIRECTION = TEAM_BID_BASIC_CRAWLER_UPDATE
WP-WH-COMPLETE-01 = PARKED_NOT_AUTHORIZED
WP-WH-RECOVERY-01 = PARKED_NOT_AUTHORIZED
DEEP_HSMT_INTELLIGENCE = PARKED_NOT_AUTHORIZED
Boundary: PARKED != CANCELLED
Response: The reliability hardening sequence is closed for this transition.
The roadmap capabilities remain available for later Human reactivation.
Disposition: ACCEPTED / ROUTED_TO_CURRENT_AND_MASTER_ROADMAP_DELTA
Promoted to: docs/agent_handoff/CURRENT.md;
  docs/agent/MASTER_ROADMAP_DELTA.md
```

### FB-0028 — Role Boot, Prompt Continuity & Three-Pole Mutual Challenge

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
Authority: A0 HUMAN_DECISION
Type: GOVERNANCE / PROCESS / HANDOFF
WP: POST-WP-TB-BASIC-CRAWLER-01 GOVERNANCE FOLLOW-UP
Observation: Human approved Option B: create one canonical
docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md in a later bounded governance WP.
A newly assigned Planner, Builder or Reviewer must resolve ROLE, PHASE,
FIRST_ACTION, mandatory reads, authority, scope, stop conditions, return packet
and next authority. Prompt construction is ACTION-FIRST and role-specific.
Long/material WPs reread and reconcile the Delta at material boundaries, while
ALWAYS CHECK != ALWAYS MODIFY; every material Delta update is compared with
MASTER_ROADMAP and a conflict is HOLD → Planner/Human. Planner, Builder and
Reviewer are three execution-control poles beneath Human A0. Any pole may/must
HOLD on a material error in another pole's prompt, Work Order, audit, scope,
baseline, authority, evidence, Delta interpretation, Roadmap interpretation or
invariant. RIGHT_TO_CHALLENGE != RIGHT_TO_OVERRIDE and
RIGHT_TO_HOLD != RIGHT_TO_REWRITE_AUTHORITY. Human A0 remains top authority.
Builder may challenge Planner but may not write a Work Order; Reviewer may HOLD
but may not edit implementation; Planner may challenge Reviewer evidence but
may not rewrite independent Reviewer history; unresolved material authority
conflict escalates to Human.
Impact: Prevent prompt/context drift and make role takeover executable without
relying on chat memory.
Disposition: PROMOTED / MERGED_DURABLE_GOVERNANCE_STATE
Promoted to: AGENTS.md; docs/agent/OPERATING_MODEL.md;
  docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md; docs/agent/MEMORY_INDEX.md;
  docs/agent/HUMAN_COLLABORATION.md; docs/agent/PROJECT_MEMORY.md / MEM-023
```

### FB-0029 — Canonical Checkout Authority Correction

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
Authority: A0 HUMAN_DECISION
Type: GOVERNANCE / CORRECTION / CHECKOUT_AUTHORITY
WP: WP-GOV-ROLE-BOOT-PROMPT-CONTINUITY-01 / GOV-BOOT-D3
Corrects: FB-0024 CHECKOUT-LOCATION INTERPRETATION ONLY
Observation: A newer Git object being available in a non-canonical checkout
  did not transfer canonical authority to that checkout. The Human-established
  canonical checkout was and remains D:\QI Technology\QI Crawler\egp-crawler-python.
Evidence: GOV-BOOT-D0 transferred exact 9493fb17... to D with Git bundle SHA/tree
  identity preserved; GOV-BOOT-D1 revalidated PR #72–#80 on D; no product
  implementation defect was found; remote merge/CI evidence was preserved; the
  former C checkout was physically removed after decommission gates; D full
  pytest had 730 passed; Ruff, diff check and fsck passed; tracked tree was clean.
Merge evidence: PR #81 merged at 2826f8c6735fcf68f405a01386d6ab4e63476e57;
  GOV-BOOT-D4 independent audit PASS.
Impact: Object freshness and object availability must not be used to silently
  reassign the governed canonical checkout.
Required laws: NEWEST_OBJECT_LOCATION != CANONICAL_AUTHORITY;
  OBJECT_PRESENT_ON_NONCANONICAL != AUTHORITY_TRANSFER;
  OBJECT_MISSING_ON_CANONICAL → HOLD → SYNC / CONTROLLED EXACT-OBJECT TRANSFER;
  never silently reassign canonical authority.
Response: Preserve FB-0024's generic repository identity gate as valid while
  forward-correcting only its checkout-location interpretation.
Disposition: PROMOTED / MERGED_DURABLE_GOVERNANCE_STATE
Promoted to: docs/agent/FEEDBACK_LEDGER.md; docs/agent/KNOWN_FAILURE_MODES.md;
  docs/agent/PROJECT_MEMORY.md / MEM-023; docs/agent_handoff/CURRENT.md
```

### FB-0030 — Revision Transition & Human-Controlled Folder Intake

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
Authority: A0 HUMAN_DECISION
Type: PRODUCT / WORKFLOW / REVISION_CONTROL
WP: WP-TB-BASIC-CRAWLER-03 Parent PRE
Decision: IB suffix 00/01/02/... is the CĐT/e-GP published package revision;
  the crawler recognizes the revision and never invents one. Team Bid normally
  supplies the newest package known to them. A revision mismatch holds intake
  and asks Human whether to continue. The operational latest never downgrades;
  prior revisions remain preserved and only previous ↔ latest comparison is
  required. Folder selection performs one automatic recursive read-only scan;
  manual rescan is allowed and no realtime watcher is used. Every discovered
  candidate file requires Team Bid confirmation before Warehouse intake. Names
  such as Chapter III/Chapter V do not prove package membership across tenders.
  The managed package folder carries exact revision identity; short child names
  such as C3_01, C5_01, PL_01, REF_01 and OTH_01 are presentation metadata while
  original user filenames remain preserved. The crawler may surface potential
  work impact but Team Bid decides rework.
Disposition: ACCEPTED / ROUTED_TO_RD-0010_AND_WP-TB-BASIC-CRAWLER-03-DESIGN
Promoted to: docs/agent/MASTER_ROADMAP_DELTA.md / RD-0010;
  docs/agent_handoff/CURRENT.md
```
### FB-0031 — QI-Crawler v0.9.0 Operational Release Acceptance

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
Authority: A0 HUMAN_DECISION
Type: RELEASE / OPERATIONAL_ACCEPTANCE / EXECUTION_ORDER
WP: WP-REL-0.9.0-INPLACE-UPGRADE-01
Decision:
QI_CRAWLER_V0_9_0 = OPERATIONAL_RELEASE_ACCEPTED
TARGET = D:\QI-Crawler
RELEASE_SOURCE = bf46dbce7501ddf0ae0a7115ddde28eb3b137f62
INSTALLER_SHA256 = 3D99939420A4B3B582FE3CD2E883D44B17DE3223EA2F012B15CF0FC4F2053DD9
TAG = NO
GITHUB_RELEASE = NO
NEXT_WP_AUTHORIZED = NO
NEXT_ACTION = STOP_AND_DISCUSS_HUMAN_NEW_IDEAS
Boundary: Operational acceptance does not authorize Warehouse, NotebookLM,
Team Bid pilot expansion or any new product WP.
Disposition: ACCEPTED / ROUTED_TO_CURRENT_PROJECT_MEMORY_CHANGELOG
Promoted to: docs/agent_handoff/CURRENT.md;
  docs/agent/PROJECT_MEMORY.md / MEM-026; CHANGELOG.md

### FB-0032 — QI Agent Workbench Parent Authorization

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
Authority: A0 HUMAN_DECISION
Type: GOVERNANCE / AGENT_WORKBENCH / EXECUTION_ORDER
WP: WP-GOV-QI-WORKBENCH-01
Decision:
QI_AGENT_WORKBENCH = AUTHORIZED
PARENT_WP = WP-GOV-QI-WORKBENCH-01
PURPOSE = Governed manual context boot, task routing, skill selection, evidence and handoff for QI agents.
PRODUCT_CHANGE = NO
VERSION_IMPACT = NONE
AUTOMATION = NO
SCHEDULER = NO
MCP = NO
EXTERNAL_CONNECTOR = NO
AUTO_MERGE = NO
AUTO_RELEASE = NO
AUTO_SPINE = NO
IMPLEMENTATION_MODE = CONTROLLED_MICRO_WP
FIRST_IMPLEMENTATION_MICRO = MICRO-A
Boundary: Authorization applies only to the approved QI Agent Workbench design and implementation plan. It does not authorize Warehouse, deep HSMT, NotebookLM, Team Bid expansion, autonomous Agent Office, product code changes, API/GUI expansion, merge or release.
Superseded local state: WP-GOV-QI-WORKBENCH-01A is preserved as an unpromoted historical local draft and is not canonical authority.
Disposition: ACCEPTED / ROUTED_TO_QI_AGENT_WORKBENCH_PARENT
Promoted to: docs/agent_handoff/CURRENT.md
```

### FB-0033 — Budget is Team Bid priority, not crawler exclusion ceiling

```text
State: PROMOTED
Author: Human
Role: HUMAN_AUTHORITY
WP: WP-BID-RADAR-OPERATIONAL-PROFILE-01 / WORK_ORDER_VERSION=3
Type: BUSINESS / PRODUCT / WORKFLOW
Authority: A0 HUMAN_DECISION
Observation: 2,000,000,000 VND is the current Team Bid budget priority. It is
not the crawler's capability ceiling and must not be a default exclusion rule.
Evidence: Explicit Human A0 decision in Work Order v3.
Impact: The operational shortlist retains packages above the preferred amount
as expansion opportunities. Budget priority is configurable and separate from
technology, method, procurement and authoritative execution-location checks.
Suggestion: Show “Mức phù hợp của gói thầu” and “Ưu tiên ngân sách Team Bid”
separately in Team Bid business sheets; preserve canonical audit provenance.
Scope change required: YES — authorized by Work Order v3.
Evidence after implementation:
PR #94: MERGED
Audited feature head: bed46ddcb0c630abb79a0616e83611c961f6520a
Merge commit: 01ba604371d698249ea0739c61b9a59f234ba762
Raw-source acceptance: PASS
Response: The A0 budget decision is implemented and durably represented.
Disposition: PROMOTED / MERGED_AUTHORITY
Promoted to: docs/agent_handoff/CURRENT.md;
  docs/agent/PROJECT_MEMORY.md / MEM-028;
  docs/agent/MASTER_ROADMAP_DELTA.md
```

### FB-0034 — Warehouse sequence: Completeness → Recovery → Human Check

```text
State: ACCEPTED
Author: Human
Role: HUMAN_AUTHORITY
Type: PRODUCT / PRIORITY / SEQUENCING
Authority: A0 HUMAN_DECISION
Observation:
After post-merge Spine closeout, Human A0 selects:
1. WP-WH-COMPLETE-01
2. WP-WH-RECOVERY-01
3. STOP_FOR_HUMAN_CHECK
4. Human decides the next Product WP
Boundary:
Do not automatically proceed from Recovery into:
- HSMT Intelligence
- SOP Intelligence
- Ground Truth
- Controlled Learning / AI
- live e-GP
- R2B
- release
Disposition: ACCEPTED / ACTIVE_HUMAN_SEQUENCE
Promoted to: docs/agent_handoff/CURRENT.md;
  docs/agent/MASTER_ROADMAP_DELTA.md
```

### FB-0035 — Warehouse completeness entry contract

```text
State: ACCEPTED / PROMOTED / MERGED_VERIFIED
Author: Human / Planner
Role: HUMAN_AUTHORITY / PLANNER_ARCHITECT
WP: WP-WH-COMPLETE-01
Type: PRODUCT / WAREHOUSE / HSMT_READINESS
Authority: A0 HUMAN_DECISION + APPROVED WORK ORDER
Decision:
PL is optional for direct exact-IB/revision intake.
The Team Bid research priority is three logical core content roles:
  1. Phạm vi cung cấp và khối lượng
  2. Yêu cầu kỹ thuật và giải pháp
  3. Tiêu chuẩn đánh giá kỹ thuật
Partial research with one or two confirmed roles remains readable and
retrievable; three of three roles is FULL_RESEARCH_READY.
Supporting material may contain or supplement a core role.
Publication completeness is independent from core research readiness.
SHA proves content integrity, while exact membership governs package authority
and retrieval. Recovery remains a separate Parent WP.
Boundary:
No PL lifecycle, live e-GP, deep HSMT extraction, solution recommendation,
GO/HOLD/NO-GO, Ground Truth promotion, Recovery, release or broad GUI redesign.
Impact: Establishes the bounded Warehouse completeness entry state and keeps
Team Bid usability fail-closed without requiring a fixed file count.
Disposition: PROMOTED / MERGED_AUTHORITY
Evidence:
PR #97 merged at c3924ca7a61bbaf800f3912014db5fa286e30eb3 from audited head
b352f0e0752422dcd87d3ad3aa579c38b9f48e76; post-merge CI run 34298017061
passed. Real acceptance used IB2600502358-00 with 31 exact memberships and
3 identity-conflicting files fail-closed/quarantined; all 3 core roles were
confirmed and managed retrieval SHA verification passed.
Promoted to: docs/agent_handoff/CURRENT.md; docs/agent/MASTER_ROADMAP.md;
docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent/PROJECT_MEMORY.md / MEM-029
```

### FB-0036 — One-off process-evidence exception for Recovery

```text
State: ACCEPTED / CLOSED_NON_PRECEDENT
Author: Human A0
Role: HUMAN_AUTHORITY
Authority: A0 HUMAN_DECISION
Type: GOVERNANCE / PROCESS-EVIDENCE / EXCEPTION
WP: WP-WH-RECOVERY-01
Decision:
Human A0 accepted a bounded one-off process-evidence exception for the exact
Recovery candidate head 8e6442a2d59d9dac83401e4592d15f9c7590d654. The
exception allows integration of the already independently audited Recovery
implementation despite historical plugin invocation evidence not being
available for reconstruction.
Evidence:
Reviewer audit PASS on the exact local range f050d60...8e6442a; full local
suite 1048 passed; PR #99 merged at 961498b49992376a9d2aef97daec9d40043fa5d0;
post-merge CI 34312849224 PASS. Plugin evidence remains USAGE_NOT_PROVEN;
historical TDD evidence remains PARTIAL_PROCESS_EVIDENCE; recovery real-source
acceptance remains EVIDENCE_GAP.
Non-precedent: YES. This exception waives no CI gate, independent review,
merge authority, Roadmap promotion condition, release gate or Human business
decision. It applies only to the named candidate and WP.
Disposition: ACCEPTED / CONSUMED_BY_MERGED_RECOVERY_CLOSEOUT
Promoted to: docs/agent_handoff/CURRENT.md;
  docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent/PROJECT_MEMORY.md / MEM-030
```

### FB-0037 — F5 guard before real F5 and bounded retention direction

```text
State: ACCEPTED / ROUTED / NON_POLICY_PRECEDENT
Author: Human A0 / Planner
Role: HUMAN_AUTHORITY / PLANNER_ARCHITECT
Authority: A0 HUMAN_DECISION + APPROVED WORK ORDER
Type: RELEASE ENGINEERING / STORAGE SAFETY / GOVERNANCE DIRECTION
WP: AO-04-C3-F5-GUARD-01-SPINE
Decision:
- F5-GUARD must be independently audited before any real F5 execution.
- Real F5 requires a subsequent explicit Work Order.
- Default future retention direction requires evidence for active/open Parent WPs
  and the four most recently closed Parent WPs.
- The four-Parent window does not authorize unlimited duplicate runtime storage.
- Older Parents become compaction candidates, not automatic deletion targets.
- Protected business, HSMT, Warehouse, Ground Truth, release, rollback and
  open-finding evidence remains exception-based.
- Formal retention/capacity policy is deferred to a separate governance WP
  after the current A3 boundary.
GENERAL_GOVERNANCE_LAW_ACTIVE = NO
FORMAL_POLICY_IMPLEMENTED = NO
Boundary: This direction records the accepted transition and does not authorize
real F5, production access, production safety, deletion, or a general retention
policy.
Evidence: AO-04-C3-F5-GUARD-01-SPINE Work Order; guard evidence freeze
fa29c15ab1db933dcbeb345164693968a64c04cd821396b415fc8eccec29561c.
Disposition: ACCEPTED / DEFERRED_TO_SEPARATE_GOVERNANCE_WP
Promoted to: docs/agent_handoff/CURRENT.md;
  docs/agent/KNOWN_FAILURE_MODES.md; docs/agent/LESSONS.md
```
### FB-0038 — Storage headroom is an A3 execution constraint

State: ACCEPTED / ROUTED / NON-POLICY PRECEDENT

- Disk headroom is a hard execution constraint; full-test and component
  evidence can create material temporary storage.
- Do not run a full pytest without an explicit storage budget and reserve.
- Directory name, age, WP number or apparent obsolescence never establishes
  deletion authority.
- Heavy rebuildable artifacts may use a 3–4 recent-Parent retention direction
  only after reference, uniqueness and rebuildability analysis.
- This record authorizes no deletion and does not create a general retention
  policy.

### FB-0039 — Canonical path map and post-WP artifact ownership

State: HUMAN_REQUEST_CAPTURED / LOCAL_GOVERNANCE_AUTHORED / AUDIT_PENDING

Source: direct Human request, 2026-09-14, following Planner's path-registry
proposal. This records the requested direction, not approval of every authored
detail or an independent verdict.

- Every new WP must be traceable from Master Roadmap/Delta to the folders and
  exact destinations serving it; new names follow one stable registry.
- Agents reuse capability-owned modules, prevent unnecessary code/artifact
  growth, and never fabricate authorized WPs or output existence.
- At WP closeout, audit all new artifacts; retain purposeful product/evidence
  assets and remove only authorized, verified unnecessary transient outputs.
  Unknown/protected/shared data remains KEEP with an owner and review condition.
- Favor stable logical IDs and additive map evolution over repeated physical
  relocation. Actual C:/D: paths are still resolved and reported per run.

Routed to: AGENTS.md LAW 16; docs/agent/PATH_REGISTRY_CONTRACT.md;
docs/agent/PATH_REGISTRY.yaml; docs/agent/PATH_REGISTRY_ROLLOUT.md;
Memory Index, Role Boot and Master Roadmap navigation references.

Boundary: local governance authoring only. No existing-file deletion,
production migration, test rerun, new A3 trial, role takeover of active A3 work,
merge, release or claim that automated enforcement is implemented.

### FB-0040 — Reproducible CI and durable Crawler-wide protection

State: HUMAN_AUTHORIZED / INDEPENDENTLY_REVIEWED_CANDIDATE_AWAITING_HUMAN_INTEGRATION

Source: Human request, 2026-09-15, to fix repeated CI failures, prepare the
branch for GitHub push/merge review, and establish enduring CI law.

Planner disposition: preserve existing supported-platform gates; correct
developer-artifact dependencies; add a fail-closed final gate and diagnostic
evidence. Future capability work evolves risk-specific gates through the CI
Fitness Contract. Synthetic engineering verification is separate from real
release acceptance. A green workflow does not itself establish protection
settings or authorize merge/release.

Routed to: AGENTS.md, CI_CONTRACT.md, Work Order
`docs/superpowers/plans/2026-09-15-ci-portability-and-gates.md` and CURRENT.
Scope excludes new A3 trials and automatic merge/release. Independent cumulative
review identified C1/C2; Planner authorized the bounded forward failure-safety
correction under Human intent in update_transaction.py and its tests; no observed product caller or maturity
promotion. Final hosted gates and live protection readback precede Human
integration; reviewed candidate status does not mean merged or released.

### FB-0041 — Post-execution A3/F5 evidence and governance disposition

```text
State: ACCEPTED / ROUTED / INDEPENDENT_CLOSEOUT_AUDIT_PENDING
Author: Human A0
Role: HUMAN_AUTHORITY
Authority: POST_EXECUTION_HUMAN_DISPOSITION dated 2026-09-17
Type: GOVERNANCE / EVIDENCE / EXECUTION_CLOSEOUT
WP: WO-GOV-QI-A3-F5-FINAL-CLOSEOUT-01-R2
Decision:
- Retain the audited technical evidence for RealF5 RunId
  A3-F5-REALF5-20260917T065744Z.
- Retain the Reviewer verdict HOLD_GOVERNANCE_AUTHORITY_EVIDENCE unchanged.
- Do not rerun RealF5 and do not authorize Runtime Restore in this WP.
- Do not infer that Human never authorized execution merely because the
  original pre-dispatch receipt could not be independently located.
- Record the authority-provenance deviation, contradictory execution marker,
  and preventive controls in the appropriate Spine authorities.
PRE_EXECUTION_HUMAN_AUTHORITY = NOT_VERIFIED
HUMAN_NEVER_AUTHORIZED = NOT_CLAIMED
RETROACTIVE_PREAUTHORIZATION = NO
POST_EXECUTION_HUMAN_DISPOSITION = KEEP_TECHNICAL_REALF5_EVIDENCE;
  KEEP_REVIEWER_GOVERNANCE_HOLD; NO_REALF5_RERUN;
  NO_RUNTIME_RESTORE_IN_THIS_WP; RECORD_PROCESS_DEVIATION_AND_PREVENTION
Boundary: This post-execution disposition does not alter the historical
Reviewer verdict, retroactively authorize dispatch, approve Runtime Restore,
establish production safety, accept crawler operations, authorize merge or
permit another RealF5 trial. A later valid pre-dispatch receipt triggers only
DOCUMENTARY_AUTHORITY_REAUDIT; it does not trigger another execution.
Disposition: ACCEPTED / ROUTED_TO_CURRENT_FAILURE_MEMORY_AND_LESSONS
```

### FB-0042 — v0.10.0 cumulative internal-use release target

```text
State: ACCEPTED / ROUTED / IMPLEMENTATION_IN_PROGRESS
Author: Human A0
Role: HUMAN_AUTHORITY
Authority: WP-REL-V010-CANDIDATE-PREP-01 approved 2026-09-17
Type: RELEASE / VERSION / EXECUTION_PRIORITY
Decision:
- TARGET_VERSION = 0.10.0
- V091_TARGET = SUPERSEDED_BEFORE_OPERATIONAL_RELEASE
- PRIMARY_GOAL = CUMULATIVE_INTERNAL_USE_RELEASE
- NEW_PRODUCT_FEATURES = HOLD
- Prepare the isolated candidate pipeline before build, acceptance and Human
  promotion decisions.
Boundary: This decision authorizes the bounded release-preparation Parent. It
does not authorize a candidate build, real Team Bid data clone/migration,
installation, publish, promotion, tag, GitHub Release, RealF5 or new product
capability.
Disposition: ACCEPTED / ROUTED_TO_MASTER_ROADMAP_DELTA_AND_CURRENT
```

### FB-0043 — QI Agent Loop governance execution and B09 park

```text
State: ACCEPTED
Author: Human A0
Role: HUMAN_AUTHORITY
Authority: A0 HUMAN_DECISION recorded in the approved Work Order and Planner correction
Type: GOVERNANCE / AGENT_WORKBENCH / HANDOFF / EXECUTION_ORDER
WP: WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01
Decision:
PARENT_WP = GOVERNANCE_AGENT_LOOP_CONSOLIDATION
BUILDER_ROLE = BUILDER_SINGLE_WRITER
GOVERNANCE_BRANCH = codex/agent-loop-consolidation-01
BASE_SHA = 179c0712a14161ea25096e66a127f6022bf696fd
WORK_ORDER_HEAD = 4cd1e4aa5837d8f57e22ba510ca9d8b0942a4ccf
WORK_ORDER_SHA256 = 8BDB4B0266FF411B2530E5B12845BC3704B6CFEAB8E99635AFA10AF40A2D12B6
EXECUTION = LOCAL_ONLY
PUSH = NOT_AUTHORIZED
PR = NOT_AUTHORIZED
MERGE = NOT_AUTHORIZED
RELEASE = NOT_AUTHORIZED
B09 = PARKED_PRESERVED_LOCAL; BRIDGE_A_HOLD; NOT_PUSHED
Evidence: Work Order correction 01 at the exact governance head above; B09 local preservation commit 9bc64942f35c41d002ef80a74c7a02851422b0e8 contains only `src/qi_crawler/operational_update.py` and `tests/test_operational_update.py`.
Boundary: This decision authorizes only the bounded Agent Loop governance Work Order and its local stages. It does not claim B09/Bridge A completion or authorize B09 continuation, push, PR, merge, release, product changes, cleanup or scope expansion.
Response: Stage 0 records the active governance handoff and preserves the displaced B09 HOLD by exact Git locator; Stage 1/2 remain subject to the post-Stage-0 ROLE_ENTRY_GATE and the Work Order's exact allowlist.
Scope change required: NO
Disposition: ACCEPTED / ROUTED_TO_CURRENT_AND_AGENT_LOOP_GOVERNANCE_WP
Promoted to: docs/agent_handoff/CURRENT.md
```

### FB-0044 — Human A0 Stage 0 re-entry and local commit boundary

```text
State: ACCEPTED / ACTIVE_EXECUTION_BOUNDARY
Author: Human A0
Role: HUMAN_AUTHORITY
Authority: Direct Human A0 instruction dated 2026-09-25
Type: GOVERNANCE / HANDOFF / EXECUTION_ORDER
WP: WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01
Decision:
  Stage 0 local commit contains exactly:
    docs/agent_handoff/CURRENT.md
    docs/agent/FEEDBACK_LEDGER.md
  Commit message: docs(agent-loop): reconcile builder entry state
  After commit, rerun ROLE_ENTRY_GATE. Stage 1 and Stage 2 may continue only
  when that gate passes, using Work Order object
  4cd1e4aa5837d8f57e22ba510ca9d8b0942a4ccf and its recorded SHA-256.
  Execution remains local only. B09 stays parked.
Boundary: No B09 execution, untracked staging, cleanup, push, PR, merge or
release. This decision supersedes the prior direct-commit limit that applied
only to the two B09 source/test files, solely for this Stage 0 transition.
Disposition: ACCEPTED / ROUTED_TO_CURRENT_AND_AGENT_LOOP_EXECUTION
Promoted to: docs/agent_handoff/CURRENT.md
```
