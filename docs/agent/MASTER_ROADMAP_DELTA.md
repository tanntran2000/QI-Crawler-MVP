# QI-CRAWLER MASTER ROADMAP DELTA
# ACTIVE PRODUCT & ARCHITECTURE EVOLUTION COMPANION

`MASTER_ROADMAP.md` is the durable canonical Product House and strategic
architecture blueprint. `MASTER_ROADMAP_DELTA.md` is its mandatory companion:
the staging authority for active, unresolved, materially useful product or
architecture evolution that is not yet fully absorbed into the Master Roadmap.

```text
READ IMPORTANCE = MANDATORY ALONGSIDE MASTER_ROADMAP
AUTHORITY TYPE = COMPANION / STAGING AUTHORITY
DELTA DOES NOT SILENTLY OVERRIDE MASTER ROADMAP
```

If the two documents conflict materially:

```text
ROADMAP_CONFLICT = YES
ENTRY_HOLD
NEXT_AUTHORITY = PLANNER_ARCHITECT / HUMAN_AUTHORITY
```

## 1. Delta purpose and admission

An entry qualifies only when it materially affects one or more of product
understanding, Crawler usefulness, domain semantics, architecture, Warehouse
organization, package/revision identity, HSMT lifecycle, completeness,
failure classification, capability maturity, roadmap sequencing, or agent
governance affecting product alignment.

The Delta is not a chat dump or TODO list. Do not admit ordinary typos,
temporary CI status, isolated trivial bugs, UI cosmetics, routine test output,
or conversation narration.

## 2. Required active-entry schema

Each active entry has a unique ID (`RD-0001`, `RD-0002`, ...):

```text
ID
TITLE
STATUS = CAPTURED | TRIAGED | APPROVED_ACTIVE | IN_IMPLEMENTATION |
         VERIFIED_READY_TO_PROMOTE
SOURCE = Human / verified evidence / Reviewer observation / failure evidence
CRAWLER_VALUE = CRITICAL | HIGH | MEDIUM | LOW | NONE
PRODUCT_AREA
PRODUCT_HOUSE_LAYERS
OBSERVATION
WHY_IT_MATTERS
ROADMAP_IMPACT = ROADMAP_UPGRADE | ROADMAP_STATUS_UPDATE | SPINE_ONLY |
                 REQUIRES_MORE_EVIDENCE | NO_ACTION
RELEVANT_CURRENT_WP = <WP / NONE>
TARGET_STATE
PROMOTION_TARGET = MASTER_ROADMAP | PROJECT_MEMORY | FAILURE_MEMORY |
                    LESSONS | FEEDBACK | GOVERNANCE | MULTIPLE
PROMOTION_CONDITION
COMPLETION_EVIDENCE
REMOVE_FROM_DELTA_WHEN
PLANNER_NOTES
```

## 3. Fingerprint and lifecycle

The logical fingerprint is:

```text
DELTA_FINGERPRINT = PRODUCT_AREA + DOMAIN_CONCEPT + DESIRED_CHANGE
```

Later evidence for the same concept updates the existing entry; it does not
create a duplicate Delta item.

The canonical lifecycle is:

```text
CHAT / HUMAN / VERIFIED OBSERVATION
→ DELTA CAPTURE
→ TRIAGE
→ APPROVED ACTIVE
→ WP IMPLEMENTATION
→ INDEPENDENT REVIEW
→ VERIFIED READY TO PROMOTE
→ PROMOTE TO CORRECT AUTHORITY
→ REMOVE ACTIVE DELTA ENTRY
```

Git history retains evidence. This file is not a permanent DONE archive.
Roadmap upgrades go to `MASTER_ROADMAP.md`; status updates adjust roadmap
maturity/frontier; Spine-only entries go to the narrowest authority and are
removed when resolved.

## 4. Mandatory read and reconciliation triggers

Read this companion with `MASTER_ROADMAP.md` at PRE-WP for every new Parent,
Micro-WP, Agent, Planner/Builder/Reviewer takeover. Reconcile it MID-WP when
there is unexpected domain behavior, a new Human clarification, a source-model
fit problem, package ambiguity, implementation/roadmap disagreement, a new
material document type, an architecture-gap failure, scope drift, or behavior
that looks wrong despite green tests.

Before `HANDOFF_READY` or Parent closeout, answer:

```text
Which RD entries were relevant?
Were they satisfied, partially satisfied, or invalidated?
Did this WP discover a new Delta?
Does any completed Delta require promotion/removal?
```

## 5. Roadmap entry gate

The gate extends the normal roadmap gate with:

```text
ROADMAP_BASELINE = VERIFIED
ROADMAP_DELTA_BASELINE = VERIFIED
RELEVANT_DELTA_IDS = RESOLVED
PRODUCT_FRONTIER = RESOLVED
ROADMAP_NODE = RESOLVED
ARCHITECTURE_LAYERS = RESOLVED
READ_MODE = RESOLVED
DOC_FRESHNESS_STATE = PASS
```

No `READY`, `PROMPT_READY` or `START_IMPLEMENTATION` is valid until these
answers are resolved. A changed Delta SHA or material RD state invalidates
`NO_RE_READ`.

## 6. Reviewer alignment bridge

The Reviewer remains an independent, non-writing bridge:

```text
BUILDER OUTPUT → DELTA → MASTER ROADMAP → SPINE → PLANNER
```

The Reviewer independently checks implementation scope, evidence, invariants,
safety and architecture, then performs a roadmap-fit audit against relevant RD
entries, the Master Roadmap and Product House. Required classifications are:

```text
DELTA_ALIGNMENT = SATISFIED | PARTIAL | NOT_APPLICABLE | CONFLICT |
                   NEW_DELTA_DISCOVERED
MASTER_ROADMAP_ALIGNMENT = ALIGNED | PARTIALLY_ALIGNED | MISALIGNED | CONFLICT
PRODUCT_HOUSE_ALIGNMENT = PASS | HOLD
CRAWLER_VALUE = IMPROVED | PRESERVED | NEUTRAL | DEGRADED | REQUIRES_VERIFICATION
```

The Reviewer also performs a Spine freshness audit. Always inspect CURRENT,
this Delta and the Master Roadmap; inspect Project Memory, Failure Memory,
Lessons, Feedback, Changelog and applicable governance contracts when relevant.
The Reviewer reports stale or missing promotion to the Planner, may report
`PLANNER_ATTENTION_REQUIRED = YES`, and never edits reviewed implementation,
promotes a Delta, becomes Planner, or enlarges Builder scope.

Required reviewer extension:

```text
PRODUCT_ROADMAP_AUDIT
RELEVANT_DELTA_IDS:
DELTA_ALIGNMENT:
MASTER_ROADMAP_ALIGNMENT:
PRODUCT_HOUSE_ALIGNMENT: PASS / HOLD
CRAWLER_VALUE:
ARCHITECTURAL_OBSERVATIONS:
NEW_DELTA_CANDIDATES:
ROADMAP_PROMOTION_CANDIDATE: YES / NO
SPINE_FRESHNESS_AUDIT: PASS / STALE_NONBLOCKING / HOLD
CHECKED_SPINE_FILES:
STALE_DOCS:
MISSING_PROMOTIONS:
DOC_FRESHNESS_STATE: PASS / STALE_NONBLOCKING / HOLD
PLANNER_ATTENTION_REQUIRED: YES / NO
REVIEWER_RECOMMENDATION:
AUDIT_VERDICT: PASS / HOLD / FAIL
NEXT_AUTHORITY: PLANNER_ARCHITECT
```

Stale documentation is `HOLD` when it could cause the next agent to build the
wrong WP, use the wrong baseline, misunderstand capability, violate an
invariant, duplicate work, miss a failure, promote an obsolete Delta, or
contradict Human authority. Purely historical wording may be
`STALE_NONBLOCKING`.

## 7. Planner responsibility

The Planner receives the Reviewer report and decides no action, forward
correction, Spine/Delta update, roadmap promotion, a bounded WP, or Human
escalation. Reviewer recommendations are evidence/advice; they do not
authorize implementation scope.

## 8. Initial approved active entries

### RD-0001 — Tender lifecycle and Warehouse shelf enrichment

```text
ID = RD-0001
TITLE = TENDER LIFECYCLE & WAREHOUSE SHELF ENRICHMENT
STATUS = APPROVED_ACTIVE
SOURCE = Human / product architecture decision
CRAWLER_VALUE = CRITICAL
PRODUCT_AREA = Tender lineage and Warehouse organization
PRODUCT_HOUSE_LAYERS = SOURCE ADAPTERS; DOMAIN CORE; WAREHOUSE
OBSERVATION = KHLCNT/TBMT stage supplies initial PL identity and package
  information; formal HSMT stage adds official IB identity, retained lineage,
  carried-forward package information and HSMT documents.
WHY_IT_MATTERS = PL and IB remain separate namespaces while one Tender
  Lineage / Warehouse Shelf can carry both stages.
ROADMAP_IMPACT = ROADMAP_UPGRADE
RELEVANT_CURRENT_WP = NONE
TARGET_STATE = Stage-aware shelf with explicit PL→IB relation and package continuity.
PROMOTION_TARGET = MASTER_ROADMAP
PROMOTION_CONDITION = Planner accepts the durable lifecycle/shelf model and
  reconciles it into the strategic blueprint.
COMPLETION_EVIDENCE = Approved domain contract plus source-backed package,
  revision and stage regression evidence.
REMOVE_FROM_DELTA_WHEN = Promoted to MASTER_ROADMAP and no active gap remains.
PLANNER_NOTES = Chapter III/V are not expected before HSMT stage; missing
  Chapter III/V before HSMT is NOT_YET_APPLICABLE, not failure. At HSMT stage,
  SOURCE_DOCUMENT_MISSING differs from crawler failure. No implementation is
  authorized by this Delta alone.
```

### RD-0002 — Reviewer implementation/Delta/Roadmap bridge

```text
ID = RD-0002
TITLE = REVIEWER IMPLEMENTATION ↔ DELTA ↔ ROADMAP BRIDGE
STATUS = APPROVED_ACTIVE
SOURCE = Human / governance decision
CRAWLER_VALUE = HIGH
PRODUCT_AREA = Review continuity and roadmap alignment
PRODUCT_HOUSE_LAYERS = GOVERNANCE; ALL AFFECTED PRODUCT HOUSE LAYERS
OBSERVATION = Reviewer checks Builder output against relevant Delta, Master
  Roadmap, Product House alignment and Spine freshness.
WHY_IT_MATTERS = A green implementation can still be stale, misaligned or
  missing promotion context.
ROADMAP_IMPACT = ROADMAP_UPGRADE
RELEVANT_CURRENT_WP = NONE
TARGET_STATE = Every relevant review reports Delta alignment and document freshness.
PROMOTION_TARGET = GOVERNANCE
PROMOTION_CONDITION = Durable reviewer contract is present in AGENTS and
  supporting governance documents.
COMPLETION_EVIDENCE = Reviewer packet fields and independent stale-state tests
  or document checks demonstrate the bridge.
REMOVE_FROM_DELTA_WHEN = Promoted to durable governance and no open contract gap remains.
PLANNER_NOTES = Core Reviewer Bridge is merged and active, but remaining
  governance read-path cleanup includes stale prompt/read sequences that do not
  explicitly include MASTER_ROADMAP_DELTA. Keep RD-0002 active until
  WP-GOV-PLANNER-CONTINUITY-01 resolves that contract gap. Reviewer remains
  non-writer and non-Planner; strategic observations may be non-blocking with
  PLANNER_ATTENTION_REQUIRED = YES.
```

### RD-0003 — Canonical failure deduplication

```text
ID = RD-0003
TITLE = CANONICAL FAILURE DEDUPLICATION
STATUS = APPROVED_ACTIVE
SOURCE = Human / failure-memory design decision
CRAWLER_VALUE = HIGH
PRODUCT_AREA = Failure classification and prevention
PRODUCT_HOUSE_LAYERS = GOVERNANCE; INFRASTRUCTURE; VERIFICATION
OBSERVATION = ONE ROOT CAUSE = ONE CANONICAL FAILURE RECORD; many occurrences
  do not create many records.
WHY_IT_MATTERS = Dynamic filename/package/page/path/timestamp values must not
  fragment one systemic failure or hide recurrence.
ROADMAP_IMPACT = ROADMAP_STATUS_UPDATE
RELEVANT_CURRENT_WP = NONE
TARGET_STATE = Fingerprint on layer + capability + symptom class + root-cause
  class + affected contract; reopen the canonical record on recurrence.
PROMOTION_TARGET = FAILURE_MEMORY
PROMOTION_CONDITION = Planner accepts the fingerprint and recurrence contract
  and routes it to KNOWN_FAILURE_MODES.
COMPLETION_EVIDENCE = Canonical FM occurrence updates and recurrence regression
  evidence without duplicate root-cause records.
REMOVE_FROM_DELTA_WHEN = Failure-memory contract is promoted and verified.
PLANNER_NOTES = Same symptom with unresolved root cause remains
  REQUIRES_VERIFICATION; no implementation is authorized here.
```

### RD-0004 — Basic Crawler first / real HSMT maturity

```text
ID = RD-0004
TITLE = BASIC CRAWLER FIRST / REAL HSMT MATURITY
STATUS = APPROVED_ACTIVE
SOURCE = Human / product sequencing decision
CRAWLER_VALUE = CRITICAL
PRODUCT_AREA = Capability sequencing and HSMT maturity
PRODUCT_HOUSE_LAYERS = SOURCE ADAPTERS; WAREHOUSE; EVIDENCE; EXTRACTION
OBSERVATION = Near-term priority is reliable intake, storage, retrieval,
  identity, evidence, persistence and basic HSMT handling before deep analysis.
WHY_IT_MATTERS = Working samples do not prove stable deep HSMT analysis or
  complete real-package coverage.
ROADMAP_IMPACT = ROADMAP_STATUS_UPDATE
RELEVANT_CURRENT_WP = NONE
TARGET_STATE = Real Human-supplied HSMT packages are acceptance specimens and
  defect-discovery evidence; deep analysis remains explicitly unproven until
  completeness and evidence gates pass.
PROMOTION_TARGET = MASTER_ROADMAP
PROMOTION_CONDITION = Roadmap maturity and dependency text reflects this
  sequencing without claiming HSMT deep analysis DONE.
COMPLETION_EVIDENCE = Real-package acceptance evidence, completeness accounting
  and bounded extraction regressions.
REMOVE_FROM_DELTA_WHEN = Promoted to roadmap and the maturity gap is tracked by
  a concrete approved capability WP.
PLANNER_NOTES = Do not call deep HSMT analysis DONE merely because current
  samples parse.
```

### RD-0005 — Planner Human Intent & Strategic Continuity

```text
ID = RD-0005
TITLE = PLANNER HUMAN INTENT & STRATEGIC CONTINUITY
STATUS = APPROVED_ACTIVE
SOURCE = Human A0
CRAWLER_VALUE = HIGH
PRODUCT_AREA = Agent governance / strategic continuity / Human intent preservation
PRODUCT_HOUSE_LAYERS = GOVERNANCE; ALL MATERIAL PRODUCT HOUSE LAYERS
OBSERVATION = Human and Planner need a stable strategic collaboration contract
  so material Human intent is transformed into bounded Builder instructions,
  durable Spine routing, strategic handoff context and Reviewer challenge
  criteria.
WHY_IT_MATTERS = Without explicit Planner responsibility, Human intent may
  remain chat-only, Builder prompts may lose rationale or constraints, future
  agents may lack strategic context, and Reviewer findings may be consumed
  superficially.
ROADMAP_IMPACT = ROADMAP_UPGRADE / GOVERNANCE
RELEVANT_CURRENT_WP = WP-GOV-PLANNER-CONTINUITY-01
TARGET_STATE = Planner owns strategic synthesis, Human-intent reconciliation,
  Builder contract generation, Reviewer challenge design, Reviewer-result
  reconciliation and strategic handoff preparation while preserving role
  boundaries.
OPERATING_LOOP = BUILDER REPORT → PLANNER RESULT ANALYSIS → REVIEWER CHALLENGE
  CONTRACT → REVIEWER RESULT → PLANNER DIRECT MASTER ROADMAP / DELTA / SPINE
  RECONCILIATION → HUMAN DECISION PACKET
PROMOTION_TARGET = GOVERNANCE
PROMOTION_CONDITION = Human-approved Planner Continuity contract is durably
  present in AGENTS and supporting governance files and independently audited.
COMPLETION_EVIDENCE = Exact-head independent governance audit proves Human
  intent preservation, Builder/Reviewer separation, strategic handoff behavior
  and Planner authority boundaries.
REMOVE_FROM_DELTA_WHEN = Planner Continuity governance is merged, post-merge
  promoted and no material contract gap remains.
PLANNER_NOTES = Planner is strategic synthesis authority, not Human authority,
  Builder, Reviewer or Source Truth.
```

### RD-0006 — Role Contract Continuity & Role Entry Gate

```text
ID = RD-0006
TITLE = ROLE CONTRACT CONTINUITY & ROLE ENTRY GATE
STATUS = APPROVED_ACTIVE
SOURCE = Human A0
CRAWLER_VALUE = HIGH
PRODUCT_AREA = Agent governance / role authority / new-agent continuity
PRODUCT_HOUSE_LAYERS = GOVERNANCE; ALL MATERIAL PRODUCT HOUSE LAYERS
OBSERVATION = Current governance names the major roles but does not yet
  provide a complete, uniform role contract plus mandatory ROLE_ENTRY_GATE for
  every new agent or takeover.
WHY_IT_MATTERS = An agent that understands product context but misunderstands
  its authority can still corrupt scope, evidence, review independence or the
  Human decision flow.
ROADMAP_IMPACT = ROADMAP_UPGRADE / GOVERNANCE
RELEVANT_CURRENT_WP = WP-GOV-PLANNER-CONTINUITY-01
TARGET_STATE = All major roles have explicit durable contracts in
  mandatory-read Spine files, and every new agent or takeover verifies its
  role before READY.
PROMOTION_TARGET = GOVERNANCE
PROMOTION_CONDITION = Role contracts, ROLE_ENTRY_GATE and role-boundary audit
  are durably implemented and independently verified.
COMPLETION_EVIDENCE = Exact-head independent governance audit proves role
  mission, authority, duties, boundaries, handoff and stop conditions are
  understood before READY.
REMOVE_FROM_DELTA_WHEN = Promoted to durable governance, merged, post-merge
  reconciled and no material role-readiness gap remains.
PLANNER_NOTES = Do not implement role contracts in M0.
```

### RD-0007 — Builder Implementation Integrity & Evidence Discipline

```text
ID = RD-0007
TITLE = BUILDER IMPLEMENTATION INTEGRITY & EVIDENCE DISCIPLINE
STATUS = APPROVED_ACTIVE
SOURCE = Human A0
CRAWLER_VALUE = HIGH
PRODUCT_AREA = Builder governance / implementation evidence / test integrity
PRODUCT_HOUSE_LAYERS = GOVERNANCE; VERIFICATION; ALL AFFECTED PRODUCT HOUSE LAYERS
OBSERVATION = Builder work needs durable preflight and evidence discipline so
  authoritative layers, realistic tests and claim boundaries are preserved.
WHY_IT_MATTERS = Mock evidence, weak traceability or conflating local PASS
  with CI PASS can make an incomplete implementation appear verified and can
  bypass Reviewer authority.
ROADMAP_IMPACT = ROADMAP_UPGRADE / GOVERNANCE
RELEVANT_CURRENT_WP = WP-GOV-BUILDER-INTEGRITY-01 / FUTURE
TARGET_STATE = Builder preflight, authoritative-layer defense, TDD RED/GREEN
  traceability, realistic tests, claim discipline and Builder-done versus
  Reviewer-PASS separation are explicit and auditable.
PROMOTION_TARGET = GOVERNANCE
PROMOTION_CONDITION = Human-approved Builder Integrity contract is durably
  implemented and independently verified.
COMPLETION_EVIDENCE = Exact-head governance audit proves evidence provenance,
  realistic regression coverage, local/CI claim separation and Reviewer
  independence.
REMOVE_FROM_DELTA_WHEN = Promoted to durable governance, merged, post-merge
  reconciled and no material Builder evidence gap remains.
PLANNER_NOTES = No implementation in Planner Continuity M0.
```

## 9. Non-authority boundary

This companion stages unresolved evolution; it does not authorize production
implementation, override `MASTER_ROADMAP.md`, replace `CURRENT.md`, change
Human authority, or close a failure. Promotion/removal requires the applicable
Planner/Human decision and independent evidence.
