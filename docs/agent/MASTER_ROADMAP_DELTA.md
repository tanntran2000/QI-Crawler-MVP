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

## 7A. Post-merge lifecycle check

At each Parent merge or post-merge reconciliation, check applicable
`KNOWN_FAILURE_MODES`, `FEEDBACK_LEDGER` and `LESSONS` triggers before
selecting the next governed action. `ALWAYS CHECK != ALWAYS MODIFY`: the
check updates a file only when its lifecycle trigger is actually met.

## 8. Initial approved active entries

### RD-0001 — Tender lifecycle and Warehouse shelf enrichment

```text
ID = RD-0001
TITLE = TENDER LIFECYCLE & WAREHOUSE SHELF ENRICHMENT
STATUS = APPROVED_ACTIVE
SOURCE = Human A0 / product architecture decision / Team Bid working-model evidence
CRAWLER_VALUE = CRITICAL
PRODUCT_AREA = Tender lifecycle, TenderCase identity and Warehouse organization
PRODUCT_HOUSE_LAYERS = DOMAIN CORE; APPLICATION BACKEND; SOURCE ADAPTERS;
  INFRASTRUCTURE / PERSISTENCE; DELIVERY SURFACE
OBSERVATION = The merged Minimum Safe Warehouse now proves the minimum
  TenderCase, exact revision, membership and seven-zone shelf semantics.
  KHLCNT/TBMT planning supplies PL identity and package context;
  the formal tender stage adds official IB identity and exact revision while
  retaining lineage. The Warehouse must carry the full tender case from plan
  context through source E-HSMT, QI working bid materials, final submission and
  post-bid evidence without collapsing those authority classes.
WHY_IT_MATTERS = PL and IB are separate namespaces; one TenderCase may link
  them without renaming either. A business folder, filename or document role
  is not package identity. E-HSMT source material, QI-created E-HSDT material,
  final submission snapshots, post-bid evidence and reference examples must
  remain distinguishable or the system can contaminate source truth and later
  analysis.
ROADMAP_IMPACT = ROADMAP_UPGRADE
RELEVANT_CURRENT_WP = WP-WH-OPS-01 / VERIFIED MERGED PARTIAL ADVANCEMENT
TARGET_STATE = A stage-aware TenderCase / Warehouse Shelf with explicit PL→IB
  relation, `base_id` lineage, exact `(base_id, revision)` identity, retained
  revision history and a logical Team Bid workspace with seven SOP zones:
  `01_Source_E-HSMT`, `02_Requirement_Register`, `03_Legal_Capability`,
  `04_Technical_Vendor`, `05_Commercial_Price`, `06_Submission_FINAL`, and
  `07_Evidence_Archive`.
PROMOTION_TARGET = MASTER_ROADMAP
PROMOTION_CONDITION = The broader TenderCase/lifecycle model, authority classes,
  revision semantics and SOP workspace contract are implemented, independently
  audited and proven against real Team Bid package evidence.
COMPLETION_EVIDENCE = Merged WP-WH-MIN-01 evidence proves the minimum
  TenderCase / exact revision / membership / seven-zone shelf semantics.
  Remaining source-backed PL→IB relation tests; revision-preservation
  regressions; source-vs-working-vs-final-vs-reference authority tests; real
  package acceptance showing reopen/retrieve behavior without identity loss.
REMOVE_FROM_DELTA_WHEN = Promoted to MASTER_ROADMAP and no active TenderCase /
  lifecycle / shelf semantic gap remains.
PLANNER_NOTES = Preserve `PL != IB`; `base_id = lineage`; `(base_id, revision)`
  is exact revision identity; new revision never overwrites the old revision.
  `BUSINESS_FOLDER != DATABASE_IDENTITY`; `DOCUMENT_ROLE != PACKAGE_MEMBERSHIP`;
  `REFERENCE_EXAMPLE != SOURCE_AUTHORITY`; `E-HSMT != E-HSDT`;
  `SOURCE_PACKAGE != WORKING_BID_WORKSPACE`; `FINAL_SUBMISSION != WORKING_FILES`.
  Chapter III/V are not expected before HSMT stage; missing Chapter III/V before
  HSMT is `NOT_YET_APPLICABLE`, not failure. At HSMT stage,
  `SOURCE_DOCUMENT_MISSING` differs from crawler failure. The Human-supplied
  Chapter III/V examples from another HSMT may be used as reference specimens
  but must never be auto-promoted into the active tender's source bundle.
  No implementation is authorized by this Delta alone.
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
SOURCE_INTEGRITY_HARDENING = MERGED_CLOSED / WP-HARDEN-SOURCE-INTEGRITY-01
SOURCE_INTEGRITY_MERGE = bcf5ca60fe933a82c097c6575fd50de63acfca4c
RELIABILITY_INTERLUDE = CLOSED
SOURCE_CHILD_RECONCILIATION = MERGED_CLOSED
SOURCE_CHILD_RECONCILIATION_MERGE = 823e33dd34c43dccece8a2d70d248db12c9ee516
POST_MERGE_CI = PASS
HUMAN_PRIORITY_AFTER_RELIABILITY_INTERLUDE = RETURN_TO_TEAM_BID_BASIC_CRAWLER_UPDATE
WP-WH-COMPLETE-01 = PARKED_NOT_AUTHORIZED
WP-WH-RECOVERY-01 = PARKED_NOT_AUTHORIZED
SOURCE = Human A0 / product sequencing decision
CRAWLER_VALUE = CRITICAL
PRODUCT_AREA = Capability sequencing, Team Bid basic usability and HSMT maturity
PRODUCT_HOUSE_LAYERS = DOMAIN CORE; APPLICATION BACKEND; SOURCE ADAPTERS;
  INFRASTRUCTURE / PERSISTENCE; DELIVERY SURFACE; EVIDENCE; EXTRACTION
OBSERVATION = Near-term priority is a Minimum Safe Warehouse that can reliably
  intake, preserve, identify, organize, reopen and retrieve real Team Bid PDF,
  DOCX and XLSX tender documents before deep HSMT analysis. Existing working
  samples and extraction code do not prove stable complete HSMT intelligence.
WHY_IT_MATTERS = Team Bid needs a usable vertical slice early, while HSMT
  extraction needs trustworthy package/revision/source boundaries before it can
  be treated as evidence for deeper reasoning. Building every Warehouse feature
  before pilot use delays operational feedback; jumping directly to HSMT risks
  analyzing incomplete or contaminated packages.
ROADMAP_IMPACT = ROADMAP_STATUS_UPDATE
RELEVANT_CURRENT_WP = WP-WH-OPS-01 / MERGED_CLOSED
WP_WH_OPS_01_STATE = MERGED_CLOSED
WP_WH_OPS_01_MERGED_FEATURE_HEAD = 196a693e4765be0bcde7460a27685d031553c92d
WP_WH_OPS_01_MERGE_COMMIT = fcb394a6ee0926c1a355c486a72dc001e07d0096
WP_WH_OPS_01_PR = 72
WP_WH_OPS_01_HOSTED_CI = PASS_EXACT_HEAD
WP_WH_OPS_01_MAIN_POST_MERGE_CI = PASS / 33156777447
CURRENT_PRODUCT_FRONTIER = Unified Tender Warehouse
WP_OBJECTIVE = Make existing TenderCase and exact tender revisions safely searchable,
  inspectable, maintainable and exportable for normal Team Bid operations while
  preserving source/revision/document authority.
WP_EXECUTION_MAP = OPS-A → OPS-B → OPS-C → OPS-D → OPS-E → OPS-F
OPS_A = VERIFIED
OPS_B = VERIFIED
OPS_C = VERIFIED
OPS_D = VERIFIED
OPS_E = VERIFIED
OPS_F = VERIFIED
REAL_BAI2 = PASS / IB2500585490-00
FULL_LOCAL_REGRESSION = 677 PASSED
INDEPENDENT_AUDIT = PASS
MINIMUM_SAFE_WAREHOUSE_MILESTONE = SATISFIED
REAL_HSMT_BAI2 = PASS
TARGET_STATE = `Minimum Safe Warehouse → Team Bid real pilot → basic Warehouse
  operations → package completeness/reconciliation → integrity/recovery
  hardening → real HSMT maturity`. Deep HSMT analysis remains explicitly
  unproven until package completeness and evidence gates pass.
PROMOTION_TARGET = MASTER_ROADMAP
PROMOTION_CONDITION = Roadmap maturity and dependency text reflects the staged
  vertical strategy and real Team Bid acceptance demonstrates safe Warehouse
  usability without claiming deep HSMT analysis DONE.
COMPLETION_EVIDENCE = Real-package acceptance with PDF/DOCX/XLSX intake,
  restart persistence, retrieval and SHA preservation; later completeness
  accounting and bounded extraction regressions for HSMT maturity.
REMOVE_FROM_DELTA_WHEN = Promoted to roadmap and the maturity gap is tracked by
  concrete approved capability WPs with verified advancement.
PLANNER_NOTES = Minimum Safe Warehouse is proven; remaining candidate
  sequencing is `WP-WH-OPS-01 → WP-WH-COMPLETE-01 → WP-WH-RECOVERY-01 → Tender
  Package & HSMT Intelligence`. This sequence is planning context, not
  implementation authority. Minimum support targets the
  currently proven modern formats PDF/DOCX/XLSX (plus existing ZIP intake);
  legacy `.doc` is not silently assumed in the minimum contract and requires a
  later explicit need/evidence decision. Do not call deep HSMT analysis DONE
  merely because current samples parse.
SOURCE_CHILD_RECONCILIATION_BOUNDARY = SOURCE_CHILD_RECONCILIATION != TENDER_PACKAGE_COMPLETENESS_RECONCILIATION
NEXT_PRODUCT_CANDIDATE = TEAM_BID_BASIC_CRAWLER_UPDATE
WP_WH_COMPLETE_01 = PARKED_NOT_AUTHORIZED
WP_WH_RECOVERY_01 = PARKED_NOT_AUTHORIZED
NEXT_WP_AUTHORIZED = NO
PARKED != CANCELLED
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

### RD-0008 — Protected managed source authority, Vault and recovery

```text
ID = RD-0008
TITLE = PROTECTED MANAGED SOURCE AUTHORITY / VAULT / RECOVERY
STATUS = APPROVED_ACTIVE
SOURCE = Human A0 / Team Bid storage-risk requirement / existing managed-store evidence
CRAWLER_VALUE = CRITICAL
PRODUCT_AREA = Managed tender source preservation, retrieval and recovery
PRODUCT_HOUSE_LAYERS = APPLICATION BACKEND; INFRASTRUCTURE / PERSISTENCE;
  DOMAIN CORE; DELIVERY SURFACE
OBSERVATION = Merged Minimum Safe Warehouse evidence proves managed source
  preservation and SHA-verified retrieval. QI-Crawler already preserves
  immutable original document bytes,
  SHA/version and tender/bundle metadata, but the broader Vault/recovery
  component remains partial. Team Bid operationally needs a
  protected managed copy that survives source-file moves/deletion, supports
  safe retrieval/export and can be reconciled/recovered when Shelf state is
  missing or damaged.
WHY_IT_MATTERS = A database record pointing at an unavailable file, a file that
  disappears because the user's source copy moved, or uncontrolled cleanup can
  make a tender package unusable precisely when Team Bid needs sudden source
  comparison. Source authority must therefore belong to the managed copy after
  successful intake, not to the user's original path.
ROADMAP_IMPACT = ROADMAP_UPGRADE
RELEVANT_CURRENT_WP = WP-WH-OPS-01 / MERGED MANAGED-SOURCE OPERATIONAL GUARDS
WP_WH_OPS_01_VERIFIED = managed-source use; SHA integrity projection;
  external-source deletion survival; controlled retrieval/export
STILL_OUTSTANDING = full recovery; archive lifecycle; retention cleanup;
  capacity management; disaster recovery
MANAGED_COPY_SURVIVAL = PROVEN
SHA_RETRIEVAL = PROVEN
FULL_VAULT_RECOVERY_ARCHIVE = NOT_COMPLETE
TARGET_STATE = `External file → staging/validation → SHA-256 → immutable managed
  Vault → Package/Revision Shelf membership → retrieval/export`, with integrity
  states for missing/orphaned/corrupt objects and an explicit recovery path.
  Storage-pressure handling routes `HOT → COLD/ARCHIVE` under policy instead of
  destructive age-based deletion.
PROMOTION_TARGET = MASTER_ROADMAP
PROMOTION_CONDITION = Managed source authority, Vault/Shelf boundary,
  retrieval/export, integrity checking and bounded recovery behavior are
  implemented and independently verified.
COMPLETION_EVIDENCE = Real and regression evidence proving source deletion or
  move does not destroy the managed copy; byte-identical retrieval by SHA;
  missing-Shelf/Vault reconciliation; no silent overwrite; backup/recovery
  evidence where required by the approved WP.
REMOVE_FROM_DELTA_WHEN = The managed source authority and recovery model is
  promoted to the Roadmap and the material preservation gap is closed.
PLANNER_NOTES = `ORIGINAL USER FILE DELETED != MANAGED COPY LOST`;
  `DATABASE RECORD EXISTS + STORED FILE MISSING = INTEGRITY FAILURE`;
  `STORED FILE EXISTS + DATABASE RECORD MISSING = ORPHAN / RECONCILIATION`.
  Internal machine-safe filenames are not business identity; controlled Team
  Bid export may use an appropriate business filename while preserving bytes
  and SHA. Do not equate the existing analytical `warehouse.py` DuckDB manager
  with the Unified Tender Warehouse product capability.
```

### RD-0009 — Tender Package completeness and source reconciliation

```text
ID = RD-0009
TITLE = TENDER PACKAGE COMPLETENESS & SOURCE RECONCILIATION
STATUS = APPROVED_ACTIVE
SOURCE = Human A0 / HSMT workflow evidence / false-complete risk analysis
CRAWLER_VALUE = CRITICAL
PRODUCT_AREA = E-HSMT source bundle integrity and completeness
PRODUCT_HOUSE_LAYERS = DOMAIN CORE; APPLICATION BACKEND; SOURCE ADAPTERS;
  INFRASTRUCTURE / PERSISTENCE; EVIDENCE; DELIVERY SURFACE
OBSERVATION = A set of stored files is not proof that a tender revision's
  source package is complete. HSMT chapters may be embedded or separate;
  amendments/clarifications may supersede earlier material; some attachments
  lack self-identifying IB text; and reference specimens may have the same
  document role while belonging to another package.
WHY_IT_MATTERS = Deep extraction or Requirement Register generation over an
  incomplete, wrong-revision or contaminated source package can yield a
  false-safe answer despite green parsers. Completeness must be an explicit
  accounted state rather than inferred from file count.
ROADMAP_IMPACT = ROADMAP_UPGRADE
RELEVANT_CURRENT_WP = WP-WH-COMPLETE-01 / FUTURE
TARGET_STATE = For each exact package revision, reconcile expected versus
  observed source material using explicit states `EXPECTED`, `FOUND`, `MISSING`,
  `CONFLICT`, `UNKNOWN`, `SUPERSEDED`, `QUARANTINED`; retain evidence/provenance
  for membership and distinguish `SOURCE_DOCUMENT_MISSING` from extraction or
  crawler failure.
PROMOTION_TARGET = MASTER_ROADMAP
PROMOTION_CONDITION = Package completeness/reconciliation semantics and their
  evidence contract are implemented, independently audited and exercised on
  real HSMT package specimens.
COMPLETION_EVIDENCE = Real-package accounting where every expected source item
  has an explicit outcome; cross-revision and foreign-package contamination
  regressions; source-missing versus extraction-failed tests; evidence locators
  for membership/reconciliation decisions.
REMOVE_FROM_DELTA_WHEN = Completeness/reconciliation is promoted to the Roadmap
  and HSMT work consumes the verified contract rather than inferring complete.
PLANNER_NOTES = `FILE STORED != PACKAGE COMPLETE`; `DOCUMENT_ROLE !=
  PACKAGE_MEMBERSHIP`; `REFERENCE_EXAMPLE != SOURCE_AUTHORITY`. The supplied
  Chapter III and Chapter V examples are valuable structure/evidence specimens
  but, because Human identified them as belonging to another HSMT, they must not
  become members of the current PL2600272581 source package. A future parser may
  identify their role, but package membership requires separate evidence.
```

### RD-0010 — Team Bid SOP workspace and minimum operational usability

```text
ID = RD-0010
TITLE = TEAM BID SOP WORKSPACE & MINIMUM OPERATIONAL USABILITY
STATUS = APPROVED_ACTIVE
SOURCE = Human A0 / SOP V2.2 working-structure decision / Team Bid real workflow
CRAWLER_VALUE = CRITICAL
PRODUCT_AREA = Team Bid Warehouse delivery and tender working lifecycle
PRODUCT_HOUSE_LAYERS = DELIVERY SURFACE; APPLICATION BACKEND; DOMAIN CORE;
  INFRASTRUCTURE / PERSISTENCE
OBSERVATION = The merged Minimum Safe Warehouse proves the minimum Team Bid
  workspace portion: TenderCase intake, restart/reopen, retrieval and seven
  logical zones with controlled derived export. Team Bid needs to start real work
  before every future Warehouse
  automation is complete. The existing PySide6 document workspace already has
  manual workspace creation, file/folder intake and manifest-oriented views,
  while the Human operational model uses seven standard zones covering source
  E-HSMT through final submission and evidence archive.
WHY_IT_MATTERS = A technically correct storage backend that cannot be used in
  daily Team Bid flow delays defect discovery and operational value. Conversely,
  encoding business rules only in GUI folders would make the frontend the
  authority. The system therefore needs a thin SOP workspace backed by Core and
  Backend contracts.
ROADMAP_IMPACT = ROADMAP_STATUS_UPDATE
RELEVANT_CURRENT_WP = NONE
MINIMUM_SAFE_WAREHOUSE_PORTION = PROVEN_AND_MERGED
TARGET_STATE = A Team Bid user can create/open a TenderCase, add PDF/DOCX/XLSX
  files or a supported folder, see package/revision/document state, close and
  reopen the app, find the same case, retrieve/export immutable originals and
  organize working material in seven logical SOP zones:
  `01_Source_E-HSMT`, `02_Requirement_Register`, `03_Legal_Capability`,
  `04_Technical_Vendor`, `05_Commercial_Price`, `06_Submission_FINAL`,
  `07_Evidence_Archive`.
PROMOTION_TARGET = MASTER_ROADMAP
PROMOTION_CONDITION = The remaining SOP workspace behavior is implemented and
  independently verified through real operational acceptance.
COMPLETION_EVIDENCE = Merged Bài 2 real TenderCase acceptance proves intake,
  restart, search/reopen, stable package/revision identity, retrieve originals
  with unchanged SHA and the minimum seven-zone workspace. A later real
  acceptance must cover the remaining SOP behavior: intake PDF/DOCX/XLSX,
  QI working DOCX remains non-source, foreign HSMT reference samples remain
  non-members, source deletion does not destroy the managed copy, and later OPS
  evidence covers search/dashboard, version semantics, controlled package
  export, final snapshots and archive behavior.
REMOVE_FROM_DELTA_WHEN = Basic Team Bid Warehouse usability and the SOP
  workspace model are promoted to the Roadmap with verified operational evidence.
PLANNER_NOTES = Seven folders are the canonical business/logical workspace
  view, not the database identity model and not necessarily the physical storage
  layout. `01_Source_E-HSMT` is source authority; `02_Requirement_Register` is a
  derived/controlled bridge; `03-05` are QI working E-HSDT material;
  `06_Submission_FINAL` must evolve toward immutable submission snapshots;
  `07_Evidence_Archive` is post-bid evidence, not a trash/cleanup target.
  Frontend collects commands and displays authoritative state; Domain Core and
  Application Backend own package/revision/membership/completeness semantics.
```

### RD-0011 — Template-Driven Controlled Document Generation

```text
ID = RD-0011
TITLE = TEMPLATE-DRIVEN CONTROLLED DOCUMENT GENERATION
STATUS = APPROVED_ACTIVE
SOURCE = Human A0 + reviewed architecture/reference evidence
CRAWLER_VALUE = HIGH
PRODUCT_AREA = Bid Assistant / Controlled Output
PRODUCT_HOUSE_LAYERS = APPLICATION BACKEND; DOMAIN CORE; DELIVERY / OUTPUT;
  VERIFICATION
OBSERVATION = Reviewed document-generation workflows support a reusable
  template-driven architecture in which one canonical data model feeds
  multiple repeated template locations while preserving template structure
  and Human authority.
WHY_IT_MATTERS = QI-Crawler will eventually need controlled DOCX/forms/
  contracts/other approved outputs without allowing AI, filenames, reference
  samples or generated documents to become source or business authority.
ROADMAP_IMPACT = ROADMAP_UPGRADE
NEW_LANE = NO
RELEVANT_CURRENT_WP = NONE
IMPLEMENT_NOW = NO
TARGET_STATE = immutable approved original template
  → versioned instrumented template
  → canonical document data model
  → SOURCE_BACKED / HUMAN_INPUT / DERIVED authority
  → readiness validation
  → repeated/conditional structures
  → template-preserving renderer
  → post-render linter
  → output manifest
  → Human review
  → final snapshot
PROMOTION_TARGET = MASTER_ROADMAP / PROJECT_MEMORY when implemented
PROMOTION_CONDITION = future approved Output WP + Golden Template acceptance
  + independent audit + merged-main evidence
PLANNER_NOTES = This Delta does NOT authorize implementation now, autonomous
  legal drafting, literal-text replacement architecture, reference sample as
  authority or AI-generated business truth. Use normal Delta schema and
  lifecycle conventions.
```

## 8A. Warehouse execution blueprint — pre-WP comparison baseline

This section is a Human-approved planning baseline for agents to compare before
opening or reviewing Warehouse/HSMT Work Packages. It is not an implementation
lease and does not override the Master Roadmap.

### Master Roadmap compatibility

```text
MASTER_ROADMAP_COMPARISON = ALIGNED
ROADMAP_CONFLICT = NO
CURRENT_PRODUCT_FRONTIER = Unified Tender Warehouse
```

The Master Roadmap already establishes:

- the primary route `Opportunity Intelligence → Unified Tender Warehouse →
  Tender Package & HSMT Intelligence`;
- the vertical Product House dependency `Delivery Surface → Application Backend
  → Domain Core`, served by Source Adapters and Infrastructure/Persistence;
- Domain invariants `PL != IB`, `base_id = lineage`, `(base_id, revision) = exact
  revision identity`, `FILE STORED != PACKAGE COMPLETE`;
- Source Adapters for manual HSMT and PDF/DOCX/XLSX tender documents;
- Infrastructure/Persistence concepts including managed filesystem, Source Vault,
  Package Shelf, archive and backup/recovery;
- the rule `BACKEND FIRST != FRONTEND NEVER` and the prohibition on putting
  material business rules only in PySide6 handlers.

This Delta does not replace those rules. It adds the unresolved operational
shape needed to convert the `PARTIAL` Warehouse frontier into an auditable
Team Bid vertical slice.

### Warehouse layer ownership

```text
DOMAIN CORE
  owns TenderCase, PL/IB/revision identity, document authority class,
  membership, version and completeness semantics.

APPLICATION BACKEND
  owns create/open case, add documents, manifest, link/reconcile membership,
  list/search/retrieve/export and later submission/completeness use cases.

INFRASTRUCTURE / PERSISTENCE
  owns immutable managed bytes, SHA, database persistence, Vault/Shelf,
  integrity, backup/recovery/archive mechanisms.

THIN FRONTEND / DELIVERY
  collects Team Bid commands and renders authoritative backend state;
  it does not own package identity, revision, completeness or business truth.
```

### Tender lifecycle and authority flow

```text
KHMT / PL
→ Opportunity / Human shortlist
→ TenderCase
→ explicit PL→IB relationship
→ exact IB base + revision
→ 01_Source_E-HSMT
→ 02_Requirement_Register
→ 03_Legal_Capability
→ 04_Technical_Vendor
→ 05_Commercial_Price
→ 06_Submission_FINAL
→ 07_Evidence_Archive
```

Authority separation:

```text
E-HSMT = OWNER / BMT / CĐT source material
E-HSDT = QI-created bid material
REFERENCE_EXAMPLE = reference only; never source authority by role alone
```

### WP_WH_MIN_01_DELTA_ANCHOR

```text
ARCHITECTURE_OPTION = B_DOMAIN_FIRST_TENDERCASE
PRIMARY_DELTA_IDS = RD-0001; RD-0004; RD-0010
PRIMARY_PARTIAL_DELTA_IDS = RD-0008
BOUNDARY_ONLY_DELTA_IDS = RD-0009
OUT_OF_PARENT_DELTA_IDS = RD-0003; RD-0007
EXECUTION_MODEL = 2_LARGE_BOUNDED_BATCHES

BATCH_A = CORE
  TenderCase/lifecycle/revision Domain Contract
  managed-source reuse
  persistence
  Package/Revision Shelf membership
  reopen
  integrity-checked retrieval core

BATCH_B = MERGED_MINIMUM_SAFE_WAREHOUSE_SLICE
  operational retrieval/export
  seven logical SOP zones
  thin Team Bid delivery wiring
  restart/reopen UX
  real Bài 2 operational acceptance

DEFERRED = full completeness/reconciliation; full backup/recovery/archive;
  deep HSMT; SOP evaluation; AI; API redesign; broad GUI redesign
```

This anchor preserves the earlier Warehouse M1–M6 concepts while separating
the approved core Batch A from the later operational Batch B. It does not
authorize either batch beyond the active Human-approved Work Order.

### Candidate Parent-WP sequence

No Parent below is authorized merely by appearing here. Before each Parent,
Planner must re-run Roadmap/Delta/Spine/live-state reconciliation and obtain the
applicable Human approval.

```text
WP-WH-MIN-01 — Minimum Safe Tender Package Warehouse
  M1 TenderCase / lifecycle / revision Domain Contract
  M2 Managed Document Store / immutable source integrity
  M3 Package / Revision Shelf + manifest backend
  M4 Retrieval / original export + bounded recovery
  M5 Thin Team Bid SOP Workspace GUI
  M6 Real operational acceptance

  EXIT:
  MINIMUM_SAFE_WAREHOUSE = OPERATIONAL
  TEAM_BID_PILOT_ALLOWED = NO_PENDING_HUMAN_BUSINESS_DECISION

WP-WH-OPS-01 — Basic Team Bid Warehouse Operations
  search / dashboard / add-replace semantics / controlled package export /
  SOP workspace operational hardening

WP-WH-COMPLETE-01 — Package Completeness & Source Reconciliation
  expected-vs-observed source inventory, missing/conflict/unknown/superseded /
  quarantine accounting and evidence

WP-WH-RECOVERY-01 — Warehouse Integrity, Backup & Recovery
  integrity scan / orphan detection / SHA revalidation / recovery / archive /
  storage-pressure policy

RETURN TO ROADMAP:
  Tender Package & HSMT Intelligence
```

### Minimum Safe Warehouse boundary

Required for the first real Team Bid pilot:

```text
PDF intake
DOCX intake
XLSX intake
supported folder / existing ZIP intake
immutable managed original
SHA-256
safe duplicate handling
TenderCase / package identity
exact revision identity
manual Team Bid workspace
document membership
persistent state across restart
package manifest
original retrieval / controlled export
thin GUI workflow
```

Not required to declare the minimum vertical slice operational:

```text
legacy .doc support
deep HSMT analysis
full semantic Requirement Register automation
cold archive automation
DuckDB analytics completion
Ground Truth expansion
SOP evaluation engine
API redesign
GUI redesign
Controlled Learning
Mini AI
```

### Cross-WP invariants that must not be forgotten

```text
PL != IB
base_id = lineage
(base_id, revision) = exact revision identity
NEW REVISION != OVERWRITE OLD REVISION
E-HSMT != E-HSDT
BUSINESS_FOLDER != DATABASE_IDENTITY
FILENAME != DOCUMENT_IDENTITY
DOCUMENT_ROLE != PACKAGE_MEMBERSHIP
REFERENCE_EXAMPLE != SOURCE_AUTHORITY
SOURCE_PACKAGE != WORKING_BID_WORKSPACE
FINAL_SUBMISSION != WORKING_FILES
FILE STORED != PACKAGE COMPLETE
ORIGINAL USER FILE DELETED != MANAGED COPY LOST
MACHINE READINESS != HUMAN BUSINESS DECISION
```

Any Warehouse/HSMT Work Order that contradicts these invariants, silently skips
an earlier dependency, or claims maturity beyond its verified vertical slice
returns to Planner/Human reconciliation instead of being inferred complete from
WP length or green tests.

## 9. Non-authority boundary

This companion stages unresolved evolution; it does not authorize production
implementation, override `MASTER_ROADMAP.md`, replace `CURRENT.md`, change
Human authority, or close a failure. Promotion/removal requires the applicable
Planner/Human decision and independent evidence.
