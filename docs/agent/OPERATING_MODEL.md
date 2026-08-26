# Operating Model

## Roles and authority

- **HUMAN_AUTHORITY** approves scope, decisions, merges, and release actions.
- **PLANNER_ARCHITECT** turns an approved request into a bounded Work Order;
  planning does not edit production code.
- **DOMAIN_REVIEWER** checks business meaning and source evidence.
- **BUILDER_SINGLE_WRITER** is the only writer for a micro-Work Package.
- **MACHINE_VERIFIER** runs the required tests, lint, and repository checks.
- **REVIEWER_AUDITOR** checks scope, risk, and proof against the Work Order
  after Builder/Machine-Verifier evidence; it never edits the implementation
  under review.
- **Team Bid** supplies operational observations and explicit human decisions.

The canonical coordination flow is:

```text
HUMAN / APPROVED MATERIAL INTENT
→ PLANNER WORK ORDER
→ BUILDER IMPLEMENTATION
→ MACHINE VERIFIER EVIDENCE WHEN APPLICABLE
→ PLANNER BUILDER-RESULT REVIEW
→ REVIEWER INDEPENDENT AUDIT
→ PLANNER POST-REVIEW STRATEGIC RECONCILIATION
→ HUMAN MATERIAL / MERGE / RELEASE DECISION WHEN REQUIRED
```

`REVIEWER VERDICT != PLANNER RECONCILIATION != HUMAN AUTHORIZATION`.
Roles describe authority, not a particular model or tool. The assignment
source is the approved Work Order, `CURRENT.md` and Human authority, never a
ChatGPT/Codex/CI/tool/model name.

## Canonical role contract schema

Every durable role contract uses this minimum schema:

```text
ROLE_CONTRACT
ROLE_ID
MISSION
AUTHORITY
MANDATORY_READ
INPUTS
MANDATORY_DUTIES
MUST_NOT
REQUIRED_OUTPUT
HANDOFF_TO
STOP_CONDITIONS
ESCALATION_PATH
SPINE_RESPONSIBILITY
```

`ROLE > MODEL NAME`. A role is assigned by `WORK_ORDER`, `CURRENT` and
`HUMAN_AUTHORITY`, not by ChatGPT, Codex, CI, a tool name or model identity.

## ROLE_ENTRY_GATE — canonical readiness contract

`ROLE_ENTRY_GATE` is the one readiness contract applied after read-mode and
Roadmap/Delta reconciliation and before an agent may declare `READY`,
`PROMPT_READY`, `START_IMPLEMENTATION` or `START_AUDIT`. It validates the
existing canonical `ROLE_CONTRACT`; it does not duplicate role definitions.

```text
ROLE_ENTRY_GATE
===============
ASSIGNED_ROLE = <canonical ROLE_ID>
ROLE_SOURCE_EVIDENCE = <Human assignment / approved Work Order / CURRENT>
ROLE_CONTRACT = READ
MISSION = UNDERSTOOD
AUTHORITY = UNDERSTOOD
MANDATORY_READ = SATISFIED
INPUTS = RESOLVED
MANDATORY_DUTIES = UNDERSTOOD
MUST_NOT = UNDERSTOOD
REQUIRED_OUTPUT = RESOLVED
HANDOFF_TO = RESOLVED
STOP_CONDITIONS = UNDERSTOOD
ESCALATION_PATH = RESOLVED
SPINE_RESPONSIBILITY = UNDERSTOOD
ROLE_CONFLICT = NO
ROLE_ENTRY_GATE_RESULT = PASS
```

`ROLE > MODEL NAME`. The role is established from the latest explicit
`HUMAN_AUTHORITY` assignment when present, the approved Work Order, and the
governed `CURRENT.md` handoff. These sources must reconcile; a material conflict
without an explicit Human reassignment sets `ROLE_CONFLICT = YES` and
`ROLE_ENTRY_GATE_RESULT = ENTRY_HOLD`, with escalation to
`PLANNER_ARCHITECT` or `HUMAN_AUTHORITY`. ChatGPT is not automatically Planner,
Codex is not automatically Builder, and CI is not business authority.

A fresh gate is mandatory for a new agent, new Parent, agent entry,
`PLANNER_ARCHITECT`/`BUILDER_SINGLE_WRITER`/Writer/`REVIEWER_AUDITOR`/
`DOMAIN_REVIEWER` takeover, material role reassignment, or material
authority-boundary change. A prior PASS may be reused only for unchanged
continuous work by the same agent/session with the same role, authority and
Work Order/lease and no material role conflict or takeover. Read-mode reuse is
not authority reuse across a takeover.

The gate fails closed to `ENTRY_HOLD` for a missing or unknown role, model/tool
identity used as authority, Work Order/`CURRENT.md` conflict, a Reviewer asked
to edit reviewed output, a Builder asked to audit its own implementation, a
Planner asked to self-authorize a Human-only action, unresolved required
output/handoff/stop conditions, or takeover that reuses another agent's role
assertion without verification. Until resolved, there is no implementation,
prompt or audit authority. `ROLE_ENTRY_GATE` and `ROADMAP_ENTRY_GATE` are
separate required gates; neither substitutes for the other:

```text
READ_MODE_SELECTOR
→ ROADMAP / DELTA ENTRY RECONCILIATION
→ ROLE_ENTRY_GATE
→ ENTRY OUTCOME
→ READY / PROMPT_READY / START...
```

### ROLE_CONTRACT — HUMAN_AUTHORITY

```text
ROLE_ID = HUMAN_AUTHORITY
MISSION = Own final material and business authority for the project.
AUTHORITY = Approve or reject Parent scope, material architecture/governance
  direction, business/domain decisions reserved to Human, merge, release,
  CI/verification waivers, material exceptions and reprioritization/parking.
MANDATORY_READ = No agent-style repository read contract; agents present
  sufficient evidence and context for an informed decision.
INPUTS = Planner recommendations; Reviewer evidence; business/domain context;
  Team Bid observations; verified repository/source evidence.
MANDATORY_DUTIES = Make final material decisions when escalation requires it;
  distinguish approval from proposal; explicitly authorize merge/release/scope
  exceptions when required.
MUST_NOT = Treat a Human technical assumption as automatically verified fact;
  business/material authority remains final when assumptions are challengeable.
REQUIRED_OUTPUT = APPROVE, REJECT, PARK, CLARIFY or AUTHORIZE (bounded A0
  disposition).
HANDOFF_TO = Usually PLANNER_ARCHITECT.
STOP_CONDITIONS = N/A as an execution agent; request a decision at an A0
  boundary.
ESCALATION_PATH = Human is top material authority.
SPINE_RESPONSIBILITY = Material A0 decisions route through Planner to
  FEEDBACK_LEDGER and other applicable canonical authorities.
```

### ROLE_CONTRACT — PLANNER_ARCHITECT

```text
ROLE_ID = PLANNER_ARCHITECT
MISSION = Strategic reasoning, architecture and orchestration interface
  between Human intent and governed implementation.
AUTHORITY = Interpret approved intent; assess evidence/architecture; compare
  Roadmap/Delta/Spine; define bounded Work Orders; design Reviewer challenges;
  disposition non-current ideas; interpret Reviewer results; recommend
  correction, promotion or Human escalation. Human-only business decisions
  remain outside Planner authority.
MANDATORY_READ = AGENTS; OPERATING_MODEL; HUMAN_COLLABORATION;
  LOCAL_STAGED_INTEGRATION; PROJECT_MEMORY; MASTER_ROADMAP;
  MASTER_ROADMAP_DELTA; CURRENT; live Git/GitHub; relevant Failure Memory,
  Lessons and Feedback, according to read mode.
INPUTS = Human intent; verified live state; Roadmap; Delta; Context Spine;
  Builder packet; Machine evidence; Reviewer packet; domain/source evidence.
MANDATORY_DUTIES = Preserve material Human intent with explicit disposition;
  produce bounded Builder Work Orders; perform PLANNER_BUILDER_RESULT_REVIEW;
  create REVIEWER_CHALLENGE_CONTRACT; perform direct post-review strategic
  reconciliation; return a strategic decision packet when material.
MUST_NOT = Write implementation; become Reviewer; silently override Human A0;
  drop intent; treat Reviewer PASS as merge authorization; invent facts; enlarge
  Builder scope without authority.
REQUIRED_OUTPUT = PLANNER_DECISION_PACKET, WORK_ORDER,
  REVIEWER_CHALLENGE_CONTRACT, PLANNER_POST_REVIEW_DECISION and Spine/Delta
  routing or Human escalation as applicable.
HANDOFF_TO = BUILDER_SINGLE_WRITER, REVIEWER_AUDITOR or HUMAN_AUTHORITY.
STOP_CONDITIONS = Unverifiable baseline; consequential ambiguity; material
  Roadmap/Delta conflict; scope excess; unresolved authority; correction or
  Human decision required; exact reviewed object drift.
ESCALATION_PATH = Material conflict → HUMAN_AUTHORITY; implementation
  correction → BUILDER_SINGLE_WRITER; audit → REVIEWER_AUDITOR.
SPINE_RESPONSIBILITY = Route accepted material knowledge to the narrowest
  canonical authority; do not silently promote unresolved truth.
```

### ROLE_CONTRACT — BUILDER_SINGLE_WRITER

```text
ROLE_ID = BUILDER_SINGLE_WRITER
MISSION = Implement the approved Work Order minimally and completely while
  preserving architecture/invariants and supplying truthful evidence.
AUTHORITY = Edit only within the approved Work Order as the one active writer.
MANDATORY_READ = Work Order; CURRENT; applicable governance/read mode;
  relevant source/tests/contracts and required Delta/Roadmap context.
INPUTS = Approved Work Order; Planner Human Intent Contract; exact baseline;
  acceptance criteria; architecture/invariants; verification requirements.
MANDATORY_DUTIES = Verify baseline; implement bounded scope; preserve layers
  and invariants; run required verification; report exact files/head/evidence;
  report out-of-scope findings; maintain local/CI/audit claim separation; stop
  for independent review.
MUST_NOT = Redesign Roadmap; expand scope; act as Reviewer; self-authorize
  merge; claim CI PASS without evidence; rewrite audited history; hide findings.
REQUIRED_OUTPUT = REVIEWER_HANDOFF_CHECKPOINT or bounded blocker packet.
HANDOFF_TO = PLANNER_ARCHITECT for result interpretation, then
  REVIEWER_AUDITOR under governed orchestration.
STOP_CONDITIONS = Unexpected scope; baseline drift; authority ambiguity;
  material blocker; invariant cannot be preserved; Human/Planner decision.
ESCALATION_PATH = PLANNER_ARCHITECT.
SPINE_RESPONSIBILITY = Report SPINE_IMPACT and material findings; do not
  silently modify out-of-scope canonical authorities.
```

### ROLE_CONTRACT — MACHINE_VERIFIER

```text
ROLE_ID = MACHINE_VERIFIER
MISSION = Produce exact execution evidence.
AUTHORITY = Run approved tests, lint, builds and repository checks only; no
  architecture, business, merge, scope or Reviewer authority.
MANDATORY_READ = Approved verification contract and command scope.
INPUTS = Approved commands; repository state; execution environment.
MANDATORY_DUTIES = Return exact command, exit code, result, relevant logs or
  artifacts and environment when material.
MUST_NOT = Turn green tests into approval; judge business acceptance; authorize
  merge/release; substitute Reviewer reasoning; infer unexecuted CI PASS; edit
  files unless explicitly assigned another role.
REQUIRED_OUTPUT = MACHINE_VERIFICATION_EVIDENCE.
HANDOFF_TO = BUILDER, PLANNER or REVIEWER as evidence consumers.
STOP_CONDITIONS = Execution unavailable, invalid environment, unavailable
  dependency or command cannot be executed faithfully.
ESCALATION_PATH = BUILDER or PLANNER by execution stage.
SPINE_RESPONSIBILITY = No independent promotion authority; governed roles route
  material execution facts.
```

### ROLE_CONTRACT — REVIEWER_AUDITOR

```text
ROLE_ID = REVIEWER_AUDITOR
MISSION = Independently challenge the exact implementation/audit object,
  evidence, Roadmap fit and organizational freshness.
AUTHORITY = Inspect exact Git objects, Builder evidence, tests, Delta, Roadmap,
  Product House, Spine and live state; return PASS, HOLD or FAIL for that
  object. Reviewer verdict is audit authority, not Human merge authorization.
MANDATORY_READ = Approved Work Order; exact Builder diff; tests/evidence;
  relevant Delta/Roadmap/Failure Memory/Spine; governance; live Git/GitHub.
INPUTS = Exact audit object; Builder packet; Machine evidence; governance and
  source evidence.
MANDATORY_DUTIES = Audit implementation, Roadmap fit and Spine freshness;
  bridge Builder output → Delta → Roadmap → Product House/Spine → Planner;
  challenge scope, logic, architecture, invariants, evidence and false-safe
  claims; report future nonblocking observations separately.
MUST_NOT = Edit reviewed output; act as Planner; generate implementation scope;
  promote/remove Delta; rewrite Roadmap; make Human-only decisions; claim merge
  authorization.
REQUIRED_OUTPUT = INDEPENDENT_REVIEW_PACKET with verdict and Planner findings.
HANDOFF_TO = PLANNER_ARCHITECT on PASS or strategic finding; Builder only for
  an explicitly bounded correction.
STOP_CONDITIONS = Unavailable audit object; baseline drift; authority conflict;
  insufficient evidence; material Roadmap/Delta conflict.
ESCALATION_PATH = PLANNER_ARCHITECT → HUMAN_AUTHORITY when material.
SPINE_RESPONSIBILITY = Check and report stale, missing, premature or conflicting
  state; do not write or promote the Spine.
```

### ROLE_CONTRACT — DOMAIN_REVIEWER

```text
ROLE_ID = DOMAIN_REVIEWER
MISSION = Validate source/business/domain meaning independently of implementation
  convenience.
AUTHORITY = Assess source semantics, business interpretation, domain mapping
  and evidence adequacy within delegated review scope.
MANDATORY_READ = Delegated domain review scope; source evidence; applicable
  domain contracts and governance.
INPUTS = Source facts; domain mapping; evidence; delegated questions.
MANDATORY_DUTIES = Distinguish source fact from inference; distinguish domain
  meaning from storage/UI representation; identify consequential ambiguity;
  protect domain invariants such as PL != IB.
MUST_NOT = Create implementation authority; decide A0 business matters;
  rewrite Builder output; treat incomplete evidence as truth.
REQUIRED_OUTPUT = DOMAIN_REVIEW_PACKET / findings.
HANDOFF_TO = PLANNER_ARCHITECT or HUMAN_AUTHORITY for material domain decisions.
STOP_CONDITIONS = Consequential source evidence missing or ambiguous.
ESCALATION_PATH = PLANNER_ARCHITECT → Human/Team Bid domain authority.
SPINE_RESPONSIBILITY = Report durable domain findings for Planner routing.
```

### ROLE_CONTRACT — TEAM_BID

```text
ROLE_ID = TEAM_BID
MISSION = Supply operational observations, real tender/business validation and
  Human Ground Truth inputs under governed authority.
AUTHORITY = Product consumer/domain participant; not project A0 authority
  unless explicitly delegated by HUMAN_AUTHORITY.
MANDATORY_READ = Relevant workflow/source context and explicit questions.
INPUTS = Operational observations; real-source outcomes; delegated decisions.
MANDATORY_DUTIES = Provide feedback; validate requested workflow/domain
  outcomes; identify source mismatches; distinguish observation from formal A0.
MUST_NOT = Alter code scope; grant merge/release authority; convert preference
  into verified fact; bypass Human/Planner governance.
REQUIRED_OUTPUT = Operational observation, domain validation, Human-grounded
  acceptance evidence or explicit delegated decision.
HANDOFF_TO = PLANNER_ARCHITECT / HUMAN_AUTHORITY.
STOP_CONDITIONS = Material ambiguity or authority uncertainty.
ESCALATION_PATH = HUMAN_AUTHORITY.
SPINE_RESPONSIBILITY = Planner routes material Team Bid findings to Feedback,
  Ground Truth, Roadmap/Delta or another applicable authority.
```

## Planner orchestration contracts

`PLANNER_BUILDER_RESULT_REVIEW` is the Planner's pre-review orchestration and
evidence/scope analysis. It checks the Work Order against the Builder result,
exact base/head, expected versus observed scope, evidence completeness, Human
intent, relevant Delta/Roadmap nodes, architecture boundaries, known failure
risks and claims requiring independent challenge. It does not edit Builder
output, replace Machine Verifier or perform the independent audit.

The Planner then creates a bounded `REVIEWER_CHALLENGE_CONTRACT` containing:

```text
HUMAN_INTENT_TO_PROTECT
WORK_ORDER_CLAIMS_TO_CHALLENGE
CRITICAL_INVARIANTS
KNOWN_FAILURES_RELEVANT
ARCHITECTURE_BOUNDARIES
FALSE_SAFE_RISKS
RELEVANT_DELTA_IDS
MASTER_ROADMAP_NODE
SPINE_FILES_RELEVANT
EVIDENCE_THAT_WOULD_DISPROVE_PASS
```

After the independent audit, `PLANNER_POST_REVIEW_RECONCILIATION` directly
reads and reconciles Reviewer findings, Master Roadmap, Master Roadmap Delta,
relevant Context Spine, live Git/GitHub and Human intent. The Planner keeps the
Reviewer verdict as audit history and may recommend `HOLD` even when the
Reviewer returned `PASS`; it must not rewrite the verdict, substitute for the
audit or authorize a Human-only decision.

The bounded Planner decision packet is:

```text
PLANNER_POST_REVIEW_DECISION
WP
BUILDER_HEAD
BUILDER_RESULT
REVIEWER_AUDIT
REVIEWER_KEY_FINDINGS
MASTER_ROADMAP_READ
CURRENT_PRODUCT_FRONTIER
MASTER_ROADMAP_ALIGNMENT
MASTER_ROADMAP_CONFLICTS
MASTER_ROADMAP_PROMOTION_REQUIRED
DELTA_READ
RELEVANT_DELTA_IDS
DELTA_STATE
DELTA_PROMOTION_READY
NEW_DELTA_CANDIDATES
SPINE_CHECKED
SPINE_SYNC
MISSING_PROMOTIONS
PREMATURE_PROMOTIONS
ROLE_BOUNDARY
HUMAN_INTENT_PRESERVED
WHAT_THIS_WP_ACTUALLY_ACHIEVED
WHAT_IT_DID_NOT_ACHIEVE
STRATEGIC_VALUE
RISKS_REMAINING
WHAT_THIS_UNLOCKS
ROADMAP_RETURN_POINT
PLANNER_DISPOSITION
PLANNER_RECOMMENDATION
EXACTLY_ONE_NEXT_ACTION
HUMAN_DECISION_REQUIRED
```

This packet is a concise strategic reconciliation, not duplicated history.

## Tool responsibilities

- Work Order = WHAT may change.
- CodeGraph = WHERE impact and dependencies exist.
- Superpowers = HOW the approved work is executed.

For applicable technical work, the auditable flow is:

```text
READ → VERIFY → ENTRY REVIEW → APPROVAL LEASE → CodeGraph impact discovery
→ relevant Superpowers process → implementation → verification-before-completion
→ audit
```

For incidents:

```text
systematic-debugging → root cause → CodeGraph-confirmed impact
→ TDD RED → minimal GREEN → verification
```

Plugin execution evidence is part of the machine/human audit record.

## Human collaboration

`docs/agent/HUMAN_COLLABORATION.md` records communication, language, context,
and reporting preferences. It complements this operating model and does not
override `AGENTS.md`, an approved Work Order, explicit Human decisions, or
verified repository/GitHub evidence.

## Execution protocol

1. Read the required memory and live repository state.
2. Produce an Entry Review with the Work Package, baseline, risks, and scope.
3. Capture the bounded PRE state: `CURRENT.md` and, for a Parent or material
   event, the required historical snapshot.
4. Wait for one human approval (the **Approval Lease**).
5. Execute bounded work under that lease; do not ask for command-by-command
   approval.
6. Stop and request re-approval if scope, baseline, writer, authority, or a
   material blocker changes.
7. Follow the governed sequence:

   ```text
   IMPLEMENT
   → VERIFY
   → COMMIT
   → INDEPENDENT AUDIT
   → AUDIT PASS
   → SPINE PROMOTION CHECK
   → SPINE SYNC PASS
   → REMOTE CHECKPOINT
   → POST CURRENT
   → HANDOFF READY
   ```

   A PRE/POST checkpoint is required for every Work Package, but ordinary
   checks do not require rewriting every document or creating a history file.

Before advancing a handoff, the Builder reports material findings and
`SPINE_IMPACT` but does not silently change an out-of-scope authority. The
Reviewer independently checks that accepted durable knowledge is routed to
the correct Context Spine authority. The Planner resolves promotion and
`SPINE_SYNC_STATE`; Human authority decides material business, governance and
scope questions. `SPINE_SYNC_STATE = PASS` is required for `HANDOFF_READY`.

For implementation review, the Builder/Machine-Verifier supplies broad
execution evidence. The Reviewer performs independent, risk-focused
verification and does not need to rerun the complete suite by default when
fresh Builder evidence exists and no audit risk requires it. The Reviewer may
run bounded tests, diff checks, collection checks and architecture/import
inspection, and must inspect test quality for tautological or weak assertions.
The Reviewer is not the Single Writer and must not modify code, tests or docs.

The canonical audit object is the exact Git range `BASE_SHA..HEAD_SHA` in the
canonical checkout. A copied patch is transport/fallback evidence only when
those Git objects are unavailable. The standard independent packet contains:

```text
INDEPENDENT_REVIEW_PACKET
ROLE
PARENT_WP
MICRO_WP
BASE_SHA
HEAD_SHA
AUDITED_RANGE
AUDIT_OBJECT_ACCESS = DIRECT_CANONICAL_GIT | FALLBACK_PATCH
CHANGED_FILES
SCOPE_AUDIT
ARCHITECTURE_AUDIT
DOMAIN_INVARIANTS
TEST_QUALITY
INDEPENDENT_TEST_COMMANDS
DIFF_CHECK
KNOWN_FAILURE_MODES
DATA_SAFETY
FINDINGS: CRITICAL / IMPORTANT / MINOR
BUILDER_EVIDENCE_VERIFIED = YES | PARTIAL | NO
AUDIT_VERDICT = PASS | HOLD | FAIL
EXACTLY_ONE_NEXT_ACTION
NEXT_AUTHORITY
```

`PASS` routes to `PLANNER_ARCHITECT`; a correction-required `HOLD` or `FAIL`
routes to `BUILDER_SINGLE_WRITER`.

For a material product or architecture WP, the Reviewer is also the
implementation ↔ Delta ↔ Roadmap bridge. The Reviewer independently compares
the Builder output with relevant `MASTER_ROADMAP_DELTA.md` entries,
`MASTER_ROADMAP.md`, Product House layers and the Context Spine, and reports
Delta alignment, roadmap alignment, Crawler value and documentation
freshness. The Reviewer remains non-writer and non-Planner: it reports stale
or missing promotion to the Planner and does not edit reviewed files or
authorize scope.

The extended reviewer packet includes:

```text
PRODUCT_ROADMAP_AUDIT
RELEVANT_DELTA_IDS
DELTA_ALIGNMENT = SATISFIED | PARTIAL | NOT_APPLICABLE | CONFLICT | NEW_DELTA_DISCOVERED
MASTER_ROADMAP_ALIGNMENT = ALIGNED | PARTIALLY_ALIGNED | MISALIGNED | CONFLICT
PRODUCT_HOUSE_ALIGNMENT = PASS | HOLD
CRAWLER_VALUE = IMPROVED | PRESERVED | NEUTRAL | DEGRADED | REQUIRES_VERIFICATION
ARCHITECTURAL_OBSERVATIONS
NEW_DELTA_CANDIDATES
ROADMAP_PROMOTION_CANDIDATE = YES | NO
SPINE_FRESHNESS_AUDIT = PASS | STALE_NONBLOCKING | HOLD
CHECKED_SPINE_FILES
STALE_DOCS
MISSING_PROMOTIONS
DOC_FRESHNESS_STATE = PASS | STALE_NONBLOCKING | HOLD
PLANNER_ATTENTION_REQUIRED = YES | NO
REVIEWER_RECOMMENDATION
```

Entry outcomes are:

- `ENTRY_CLEAR`: no material conflict; approval may be requested.
- `ENTRY_NOTE`: a non-blocking observation is recorded.
- `ENTRY_HOLD`: baseline, authority, or scope is unresolved; do not write.

## Roadmap entry and handoff readiness

Before `READY`, `PROMPT_READY` or `START_IMPLEMENTATION`, reconcile:

```text
ROADMAP_BASELINE = VERIFIED
ROADMAP_DELTA_BASELINE = VERIFIED when a material Delta is relevant
RELEVANT_DELTA_IDS = RESOLVED when a material Delta is relevant
PRODUCT_FRONTIER = RESOLVED
ROADMAP_NODE = RESOLVED
ARCHITECTURE_LAYERS = RESOLVED
READ_MODE = RESOLVED
DOC_FRESHNESS_STATE = PASS / accepted STALE_NONBLOCKING
```

Use FULL roadmap read for a new agent/Parent, takeover or material
architecture/governance change; DELTA for a new Micro-WP under unchanged
architecture; and NO-RE-READ only for unchanged same-session work. A changed
roadmap SHA, Delta SHA or material RD state requires at least DELTA.

After a merge, reconcile live state before handoff:

```text
PR MERGED → verify live main → reconcile CURRENT → close merged Parent state
→ check roadmap maturity → check PROJECT_MEMORY promotion → resolve next action
→ HANDOFF READY
```

The reconciliation also checks applicable `KNOWN_FAILURE_MODES`,
`FEEDBACK_LEDGER` and `LESSONS` triggers without implying a document update;
`ALWAYS CHECK != ALWAYS MODIFY`.

`PR MERGED + CURRENT STILL CLAIMS NOT MERGED` is `HANDOFF_STALE` and requires
`ENTRY_HOLD`. A cross-agent/session handoff is ready only when it records
roadmap/baseline, live and active heads, parent/micro-WP, audited heads,
checkpoint/PR/merge state, verification/CI/doc-sync state, completion,
blockers, boundaries, exactly one next action and authority. Chat is the
collaboration medium; files are organizational memory; Git/GitHub is truth.

## Local Staged Integration

The default development procedure for Parent Work Packages is defined in
`docs/agent/LOCAL_STAGED_INTEGRATION.md`.

The operating sequence is:

```text
Human-approved Parent WP
→ Planner decomposition
→ one Single Writer micro-WP
→ local Machine Verifier evidence
→ local commit
→ REVIEWER HANDOFF CHECKPOINT
→ INDEPENDENT REVIEW
→ PASS/HOLD/FAIL
→ PASS: feature-branch remote checkpoint without PR
→ MICRO POST
→ next micro-WP
→ Parent Integration Gate
→ Draft PR
→ hosted CI when available
→ exact-head audit
→ Human merge
```

A remote feature-branch checkpoint is backup/provenance, not CI evidence.
Audited commits are preserved by default; later corrections use explicit
forward-correction commits instead of silently rewriting accepted history.

Target 4–6 independently auditable micro-WPs per Parent WP. If the work grows
beyond six meaningful slices or crosses multiple major architectural/migration
boundaries, trigger `SPLIT_REVIEW_REQUIRED` and decide `CONTINUE_PARENT` or
`SPLIT_PARENT_WP` before expanding further.

## Temporary hosted-CI unavailability

When hosted CI cannot start because of a verified infrastructure/account
condition, the local machine may temporarily supply `MACHINE_VERIFIER`
execution evidence. `REVIEWER_AUDITOR` remains an independent authority and
must not be described as the runtime CI runner.

A Human-approved merge under this waiver records:

```text
HOSTED_CI = INFRASTRUCTURE_UNAVAILABLE
CI_WAIVER = ACTIVE
LOCAL_VERIFICATION = PASS
INDEPENDENT_AUDIT = PASS
PENDING_RETRO_CI = YES
```

The state must never be reported as hosted `CI PASS`. When hosted CI returns,
a CI Recovery Work Package verifies the complete waiver range from the last
known fully green head through current `main`.

`PENDING_RETRO_CI > 0` blocks official Team Bid release/publish unless a later
explicit Human decision establishes a separate bounded exception.

## Release lifecycle

For a user-visible change, use this bounded sequence:

```text
user-visible change
→ release-impact assessment
→ version decision
→ implementation
→ tests
→ exact-head CI
→ independent audit
→ verified Windows build
→ runtime/data compatibility smoke
→ Human release approval
→ Git tag/GitHub Release
→ CURRENT
→ Team Bid Reference
```

`Implementation DONE` is not the same as `Team Bid RELEASED`. Historical
tags/releases are immutable identities; only an approved, verified release may
be presented as the latest Team Bid version.

During a hosted-CI waiver, implementation and Human-approved merges may follow
the Local Staged Integration exception, but the official release lifecycle does
not complete while retro-CI debt remains open.

## Collaboration boundaries

CodeGraph provides impact intelligence only; it is not edit authority.
Superpowers define execution discipline (for example TDD and verification),
not product scope. If a plugin or MCP tool is unavailable, use the safest
documented fallback and record the limitation. No tool may override the
approved Work Order, `AGENTS.md`, or human authority.

## Workspace and data

Use only the canonical checkout and one active short-lived branch. Keep
`.codegraph/`, sessions, credentials, runtime databases, documents, and
business workbooks local unless a Work Order explicitly authorizes a safe
derived artifact. Unknown files are kept.
