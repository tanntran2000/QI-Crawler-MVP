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
RELEVANT_CURRENT_WP = NONE_POST_MERGE_PARENT03
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
  Parent-03 adds merged controlled folder intake and operational revision
  transition evidence while genuine multi-revision and foreign-reference
  operational evidence remain explicit gaps. Remaining source-backed PL→IB
  relation, broader lifecycle and authority-class evidence determine promotion.
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

### RD-0004 — Basic Crawler first / real HSMT maturity

```text
ID = RD-0004
TITLE = BASIC CRAWLER FIRST / REAL HSMT MATURITY
STATUS = APPROVED_ACTIVE
ACTIVE_PRODUCT_PRIORITY = NONE / HUMAN_A0_CHECKPOINT
NEXT_PARENT_CANDIDATE = NONE
NEXT_WP_AUTHORIZED = NO_NEXT_PRODUCT_WP
WP_WH_COMPLETE_01 = CLOSED_POST_MERGE_VERIFIED
WP_WH_RECOVERY_01 = CLOSED_POST_MERGE_VERIFIED
SOURCE = Human A0 / product sequencing decision
CRAWLER_VALUE = CRITICAL
PRODUCT_AREA = Capability sequencing, Team Bid basic usability and HSMT maturity
PRODUCT_HOUSE_LAYERS = DOMAIN CORE; APPLICATION BACKEND; SOURCE ADAPTERS;
  INFRASTRUCTURE / PERSISTENCE; DELIVERY SURFACE; EVIDENCE; EXTRACTION
OBSERVATION = Near-term priority established a Minimum Safe Warehouse that can
  reliably intake, preserve, identify, organize, reopen and retrieve real Team
  Bid PDF, DOCX and XLSX tender documents before deep HSMT analysis. Parent-03
  now also proves bounded controlled-folder intake and operational revision
  transition mechanics without promoting deep HSMT maturity.
WHY_IT_MATTERS = Team Bid needs a usable vertical slice early, while HSMT
  extraction needs trustworthy package/revision/source boundaries before it can
  be treated as evidence for deeper reasoning. Building every Warehouse feature
  before operational evidence delays feedback; jumping directly to HSMT risks
  analyzing incomplete or contaminated packages.
ROADMAP_IMPACT = ROADMAP_STATUS_UPDATE
HISTORICAL_EXECUTION_SUMMARY = Source-integrity hardening and the Minimum Safe
  Warehouse/basic-crawler slices were merged and verified; Parent-03 later
  added bounded controlled-folder intake and forward-only revision mechanics.
  These completed execution details remain historical while the HSMT maturity
  gap stays active.
HISTORICAL_EVIDENCE_REFS = WP-HARDEN-SOURCE-INTEGRITY-01 merge
  bcf5ca60fe933a82c097c6575fd50de63acfca4c; source-child reconciliation merge
  823e33dd34c43dccece8a2d70d248db12c9ee516; WP-WH-OPS-01 merge
  fcb394a6ee0926c1a355c486a72dc001e07d0096 (PR72); Parent-03 merge
  3ebea845589fedf860afb94f69959413a819b176.
RELEVANT_CURRENT_WP = NONE / HUMAN_A0_DIRECTION_CHECKPOINT
CURRENT_PRODUCT_FRONTIER = Unified Tender Warehouse
WP_OBJECTIVE = Make existing TenderCase and exact tender revisions safely searchable,
  inspectable, maintainable and exportable for normal Team Bid operations while
  preserving source/revision/document authority.
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
  restart persistence, retrieval and SHA preservation; Parent-03 adds controlled
  folder intake, same-package DOCX/restart/export proof and revision-transition
  mechanism evidence. Later completeness accounting and bounded extraction
  regressions remain required for HSMT maturity.
REMOVE_FROM_DELTA_WHEN = Promoted to roadmap and the maturity gap is tracked by
  concrete approved capability WPs with verified advancement.
FUTURE_MATURITY_SEQUENCE_AFTER_HUMAN_REACTIVATION = `WP-WH-OPS-01 →
  WP-WH-COMPLETE-01 → WP-WH-RECOVERY-01 → Tender Package & HSMT Intelligence`
PLANNER_NOTES = The future maturity sequence is planning context, not current
  implementation authority. Minimum support targets the currently proven
  modern formats PDF/DOCX/XLSX (plus existing ZIP intake); legacy `.doc` is not
  silently assumed. Do not call deep HSMT analysis DONE merely because current
  samples parse. Human must select the next product priority after Parent-03.
SOURCE_CHILD_RECONCILIATION_BOUNDARY = SOURCE_CHILD_RECONCILIATION != TENDER_PACKAGE_COMPLETENESS_RECONCILIATION
NEXT_PRODUCT_CANDIDATE = NONE
NEXT_WP_AUTHORIZED = NO_NEXT_PRODUCT_WP
CURRENT_GOVERNED_NON_PRODUCT_ACTION = NONE
NEXT_GOVERNED_NON_PRODUCT_ACTION = NONE
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
EXECUTION_STATE = NO_ACTIVE_IMPLEMENTATION / HUMAN_A0_CHECKPOINT
ENTRY_DEPENDENCY = WP-WH-COMPLETE-01 CLOSED_AND_RECONCILED
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
RELEVANT_CURRENT_WP = NONE / HUMAN_A0_DIRECTION_CHECKPOINT
NEXT_PARENT_CANDIDATE = NONE
CURRENT_GOVERNED_NON_PRODUCT_ACTION = NONE
NEXT_GOVERNED_NON_PRODUCT_ACTION = NONE
NEXT_PRODUCT_CANDIDATE = NONE
HISTORICAL_EXECUTION_SUMMARY = Managed-source use, SHA integrity, external-source
  deletion survival, controlled retrieval/export and bounded recovery were
  merged and independently verified; safe real-specimen recovery remains an
  evidence gap.
HISTORICAL_EVIDENCE_REFS = WP-WH-RECOVERY-01 audited head
  8e6442a2d59d9dac83401e4592d15f9c7590d654; merge
  961498b49992376a9d2aef97daec9d40043fa5d0; PR99; post-merge CI
  34312849224; WP-WH-OPS-01 managed-source evidence.
BOUNDED_RECOVERY_CAPABILITY = MERGED_VERIFIED
INTEGRITY_SCAN = PROVEN_LOCAL
ORPHAN_RECONCILIATION = PROVEN_LOCAL_NO_AUTO_ADOPTION
EXACT_SHA_RECOVERY = PROVEN_LOCAL
QUARANTINE_BEFORE_REPLACE = PROVEN_LOCAL
RECOVERY_EVENT_HISTORY = PROVEN_LOCAL_APPEND_ONLY
RECOVERY_MIGRATION = 0022_add_tender_recovery_events
TEAM_BID_RECOVERY_ACTION = MERGED_VERIFIED_THIN_GUI_SURFACE
INDEPENDENT_REVIEW = PASS
PR99_HOSTED_CI = PASS
LOCAL_FULL_REGRESSION = PASS_1048
HISTORICAL_TDD_EVIDENCE = PARTIAL_PROCESS_EVIDENCE
PLUGIN_EVIDENCE = USAGE_NOT_PROVEN
REAL_RECOVERY_ACCEPTANCE = EVIDENCE_GAP
REAL_RECOVERY_SPECIMEN = EVIDENCE_GAP
STILL_OUTSTANDING = archive lifecycle; retention cleanup; capacity management;
  disaster recovery; safe real-specimen recovery evidence
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
ACTIVE_PARENT_WP = NONE_POST_MERGE_PARENT03
MINIMUM_SAFE_WORKSPACE = PROVEN
BASIC_WAREHOUSE_OPERATIONS = PROVEN
HISTORICAL_EXECUTION_SUMMARY = The three Basic Crawler slices and the FM-009
  test-harness correction were merged and verified; Parent-03 preserves the
  controlled-intake and forward-only revision evidence gaps recorded below.
HISTORICAL_EVIDENCE_REFS = Basic Crawler 01 PR79 merge
  5e4c1ad682e62b29077f5a67954c65caf8d07746 (audited head
  89259fcba223084eb4ef2651ce1e675b342ac15b); Basic Crawler 02 merge
  54a0c53fdb5d38e208c4fd66d126b20e971f00f5 (head
  03056fe147c3263cf8fb2ea39e63dc239e35fffe); Parent-03 PR83 merge
  3ebea845589fedf860afb94f69959413a819b176 (audited heads
  d7a2cfdeb68f08a558a1f4cc165d0a8ad7b0ab34 and
  0d48abc87693643fb668fd8900c970d7b3315620); FM-009 correction merge
  c4e08558f54274cf6115f0bf4e966c44edcdff33; initial B2 failed audited head
  6b71180c3f1c9c0c5cfbe93558bcb0f4cd204be8 and corrected audited head
  f15f96d62eefd6d858dbcc55cb43f385d52d9119 (correction TDD evidence PASS).
CURRENT_VERIFIED_PRODUCT_GAP = REAL_MULTI_REVISION_OPERATIONAL_PROOF; REAL_REFERENCE_OPERATIONAL_EVIDENCE
ROADMAP_MATURITY_STATE = UNIFIED_TENDER_WAREHOUSE_PARTIAL_UNCHANGED
MASTER_ROADMAP_WRITE = NO_CHANGE_REQUIRED_QUALITATIVE_STATE_UNCHANGED
DESIGN_APPROVAL = HUMAN_A0_APPROVED
SOURCE_REVISION = CĐT_EGP_PUBLISHED_PACKAGE_REVISION
IB_00 = FIRST_CDT_EGP_PUBLISHED_REVISION
IB_01_PLUS = LATER_CDT_EGP_PUBLISHED_REVISIONS
SOURCE_REVISION != CRAWLER_VERSION
SOURCE_REVISION != FILE_VERSION
CRAWLER_MUST_NOT_INVENT_REVISION
LATEST_OPERATIONAL_REVISION = LATEST_KNOWN_REVISION_EXPLICITLY_ACCEPTED_FOR_TEAM_BID_USE
LATEST_DIRECTION = FORWARD_ONLY
DOWNGRADE = FORBIDDEN
REVISION_MISMATCH = HOLD_AND_REQUIRE_TEAM_BID_CONFIRMATION
NEWER_ACCEPTED_REVISION = PRESERVE_PREVIOUS → INGEST_NEW → COMPARE_PREVIOUS_VS_LATEST → ADVANCE_LATEST
NEWER_REJECTED_REVISION = NO_WAREHOUSE_STATE_CHANGE
OLDER_THAN_LATEST = NO_DOWNGRADE; HISTORICAL_REVISION_READABLE
COMPARE_WINDOW = PREVIOUS_OPERATIONAL_REVISION ↔ LATEST_OPERATIONAL_REVISION
SOURCE_DIFF_STATES = UNCHANGED; CHANGED; ADDED; REMOVED_FROM_NEW_REVISION; UNKNOWN_RELATION
SOURCE_DIFF != BUSINESS_DECISION
POTENTIAL_WORK_IMPACT != WORK_INVALID
TEAM_BID = FINAL_REWORK_AUTHORITY
FOLDER_MODE = SELECT_FOLDER_AUTO_SCAN_ONCE
MANUAL_RESCAN = YES
REALTIME_WATCHER = NO
AUTO_SCAN = READ_ONLY
AUTO_SCAN != AUTO_IMPORT
FILE_DISCOVERED != PACKAGE_MEMBER
PARSER_ROLE_DETECTED != SOURCE_AUTHORITY
WAREHOUSE_INGEST = HUMAN_FILE_CONFIRMATION_REQUIRED
FOREIGN_PACKAGE_CANDIDATE = HOLD / HUMAN_CORRECTION / REFERENCE_ONLY
REFERENCE_ONLY != SOURCE_MEMBERSHIP
PACKAGE_FOLDER = EXACT_IB_REVISION
ORIGINAL_FILENAME = PRESERVED_METADATA
MANAGED_FILENAME != DOCUMENT_IDENTITY
FILENAME != PACKAGE_IDENTITY
DOCUMENT_ROLE != PACKAGE_MEMBERSHIP
TARGET_INCREMENT = HUMAN_CONFIRMED_OPPORTUNITY → SAFE_TENDERCASE_WORKSPACE_HANDOFF
IB_RULE = EXACT_IB_REVISION_ONLY
PL_RULE = PL_CONTEXT_MAY_CREATE_OR_OPEN_PROVISIONAL_CASE BUT MUST_NOT_FABRICATE_IB
NEXT_PARENT_CANDIDATE = WP-WH-COMPLETE-01
NEXT_PARENT = WP-WH-COMPLETE-01
NEXT_WP_AUTHORIZED = YES_HUMAN_A0
WP_MAP = MICRO-A_REAL_REVISION_ACCEPTANCE → MICRO-B1_CONTROLLED_INTAKE_AND_NAMING → MICRO-B2_REVISION_TRANSITION_AND_DIFF → MICRO-C_OPERATIONAL_CLOSURE
MICRO_A = INDEPENDENT_AUDIT_PASS
MICRO_A_AUDITED_HEAD = 818945f2d7f4dce6b3791c94ca6dfe8c5ebd96d2
MICRO_A_REAL_LINEAGE = IB2600462391
MICRO_A_REAL_REVISION = IB2600462391-00
REAL_MULTI_REVISION_EVIDENCE = EVIDENCE_GAP
REAL_DOCX_AUTHORITY_EVIDENCE = PROVEN
REAL_REFERENCE_OPERATIONAL_EVIDENCE = EVIDENCE_GAP
REAL_MULTI_REVISION_OPERATIONAL_PROOF = EVIDENCE_GAP
SYNTHETIC_MECHANISM_PROOF = PROVEN
MATERIAL_PRODUCT_BLOCKERS:
  BC03-B01 = CLOSED_INDEPENDENT_AUDIT_PASS
  BC03-B02 = CLOSED_INDEPENDENT_AUDIT_PASS
  BC03-B03 = CLOSED_INDEPENDENT_AUDIT_PASS
  BC03-B04 = CLOSED_INDEPENDENT_AUDIT_PASS
  BC03-B05 = CLOSED_INDEPENDENT_AUDIT_PASS
AVAILABLE_REVISIONS_NOT_AUTHORITY = PROVEN
INITIAL_HUMAN_ACCEPTANCE = PROVEN
OPERATIONAL_LATEST_PERSISTED = PROVEN
LATEST_RESTART_PERSISTENCE = PROVEN
MIGRATION = 0020_add_tender_operational_revision_events
MIGRATION_FABRICATES_AUTHORITY = NO
ACCEPTED_PENDING_NE_ACTIVATED = PROVEN
HUMAN_ACCEPT_IS_PENDING = PROVEN
ACCEPT_DOES_NOT_ADVANCE_LATEST = PROVEN
PENDING_RESTART = PROVEN
HUMAN_REJECT = PROVEN
NO_DOWNGRADE = PROVEN
NUMERIC_REVISION_ORDER = PROVEN
ACTIVATION_REQUIRES_ADJACENT_COMPARISON = PROVEN
EXPLICIT_ACTIVATION_ADVANCES = PROVEN
NO_MEMBERSHIP_INHERITANCE = PROVEN
NO_REVIEW_INHERITANCE = PROVEN
PREVIOUS_REVISION_PRESERVED = PROVEN
ADJACENT_DIFF_ONLY = PROVEN
UNCHANGED = PROVEN
CHANGED = PROVEN
ADDED = PROVEN
UNKNOWN_RELATION = PROVEN
REMOVED_FROM_NEW_REVISION_REQUIRES_COMPLETENESS_EVIDENCE = PROVEN
ABSENCE_FROM_INCOMPLETE_OBSERVATION_NE_REMOVAL = PROVEN
COMPARISON_ZERO_PRODUCT_MUTATION = PROVEN
POTENTIAL_WORK_IMPACT_NE_WORK_INVALID = PROVEN
TEAM_BID_OPERATIONAL_INTEGRATION = PROVEN
B1_CONTROLLED_INTAKE_REUSED = PROVEN
AUTO_FOLDER_IMPORT_BYPASS = ABSENT
CORRECTION_TDD_EVIDENCE = PASS
CORRECTED_B2_AUDIT = PASS
CORRECTED_B2_AUDITED_HEAD = f15f96d62eefd6d858dbcc55cb43f385d52d9119
PLANNER_WRITE_SET_SPECIFICATION_DEFECT = HISTORICAL_FORWARD_CORRECTED
EXACT_RELEASE_IDENTITY = PROVEN
OLD_REVISION_APPEND_ONLY_MECHANISM = PROVEN
DOCUMENT_FORMAT_AUTHORITY_MEMBERSHIP_SEPARATION = PROVEN
REFERENCE_ONLY_STRUCTURAL_GUARD = PROVEN
MICRO_A_DEFAULT = NO PRODUCT CODE CHANGE
MICRO_A_FLOW = CONFIRMED OPPORTUNITY → EXACT TENDERCASE / REVISION → REAL PDF/DOCX/XLSX → AUTHORITY + ZONE → MANAGED COPY → RESTART → SEARCH / REOPEN → RETRIEVE / SHA VERIFY → CONTROLLED EXPORT
MICRO_A_EXIT = BLOCKER EVIDENCE OR EXPLICIT NO-BLOCKER EVIDENCE
MICRO_B = CONDITIONAL_NOT_AUTHORIZED
MICRO_B_ENTRY = MATERIAL BLOCKER PROVEN BY MICRO_A_AND_PLANNER_AUTHORIZATION
MICRO_B1 = CONTROLLED_FOLDER_INTAKE_AND_PACKAGE_SCOPED_NAMING
MICRO_B1_TARGET_BLOCKERS = BC03-B01; BC03-B05
MICRO_B1_STATE = INDEPENDENT_AUDIT_PASS
MICRO_B1_AUDITED_HEAD = 552eabb23f82407c38074b312c5ecb2e38d1ed86
MICRO_B2 = OPERATIONAL_REVISION_TRANSITION_AND_ADJACENT_DIFF
MICRO_B2_TARGET_BLOCKERS = BC03-B02; BC03-B03; BC03-B04
MICRO_B2_STATE = CLOSED_INDEPENDENT_AUDIT_PASS
MICRO_C = CLOSED_INDEPENDENT_AUDIT_PASS
MICRO_C_STATE = CLOSED_INDEPENDENT_AUDIT_PASS
MICRO_C_AUTHORIZED = YES_REAL_EVIDENCE_ONLY_CLOSED
MICRO_C_TARGETS = REAL_MULTI_REVISION_EVIDENCE; REAL_DOCX_AUTHORITY_EVIDENCE; REAL_REFERENCE_OPERATIONAL_EVIDENCE; SAME_PACKAGE_END_TO_END; REAL_REVISION_00_PRESERVED; REAL_REVISION_01_ISOLATED; REAL_PREVIOUS_LATEST_COMPARE; REAL_RESTART_REOPEN; REAL_CONTROLLED_EXPORT
GROUND_TRUTH_TO_EXACT_IB_HANDOFF = PROVEN
REAL_PDF_MANAGED_DOCUMENT_LIFECYCLE = PROVEN
CONTROLLED_EXPORT = PROVEN
CROSS_TENDER_ISOLATION = PROVEN
SAME_PACKAGE_END_TO_END = PROVEN
DOCX_ROLE_AUTHORITY = PROVEN
REFERENCE_AUTHORITY_SEPARATION = EVIDENCE_GAP
MULTI_REVISION_OPERATIONAL_PROOF = EVIDENCE_GAP
NO_GENUINE_SECOND_REVISION_VERIFIED != NO_SECOND_REVISION_EXISTS
EVIDENCE_GAP != PRODUCT_DEFECT
FALSE_SAFE = 0
FABRICATED_IDENTITY = 0
CROSS_TENDER_SOURCE_CONTAMINATION = 0
RD-0008 = AUTHORIZED_NEXT_PARENT
DEEP_HSMT = NOT_AUTHORIZED
API_EVOLUTION = HOLD
SOURCE_CRAWLER_REWRITE = NOT_AUTHORIZED
PACKAGE_COMPLETENESS = OUT
REQUIREMENT_REGISTER_AUTOMATION = OUT
REALTIME_FOLDER_WATCHER = OUT
RELEASE = NO
TEAM_BID_PILOT = NO
PROCESS_FINDINGS = PLANNER_WRITE_SET_SPECIFICATION_DEFECT; TDD_BEHAVIORAL_RED_EVIDENCE_PARTIAL
PROCESS_FINDINGS_PRODUCT_BLOCKING = NO
MICRO_B2_TDD_EVIDENCE_REQUIREMENT = EACH_BEHAVIOR_MUST_RECORD_RED_COMMAND_EXPECTED_FAILURE_AND_REASON_BEFORE_GREEN
BOUNDARIES = NOT_SOURCE_CRAWLER_REWRITE; NOT_BROAD_GUI_REDESIGN;
  NOT_API_EVOLUTION; NOT_LEGACY_GO_HOLD_AUTHORITY; NOT_PACKAGE_COMPLETENESS;
  NOT_VAULT_RECOVERY; NOT_DEEP_HSMT; NOT_RELEASE
OBSERVATION = The merged Warehouse and Basic Crawler slices now prove the
  minimum Team Bid workspace portion plus controlled folder intake and bounded
  revision-transition mechanics. Team Bid still needs Human authority at intake
  and revision activation, and broader Warehouse automation is incomplete.
WHY_IT_MATTERS = A technically correct storage backend that cannot be used in
  daily Team Bid flow delays defect discovery and operational value. Conversely,
  encoding business rules only in GUI folders would make the frontend the
  authority. The system therefore keeps the thin SOP workspace backed by Core
  and Backend contracts.
ROADMAP_IMPACT = ROADMAP_STATUS_UPDATE
RELEVANT_CURRENT_WP = NONE_POST_MERGE_PARENT03
MINIMUM_SAFE_WAREHOUSE_PORTION = PROVEN_AND_MERGED
DAILY_HANDOFF_INCREMENT = PROVEN_AND_MERGED
CONFIRMED_OPPORTUNITY_TO_WORKSPACE = PROVEN
IB_EXACT_REVISION_HANDOFF = PROVEN
KHMT_PROVISIONAL_PL_NO_FABRICATED_IB = PROVEN
AMBIGUOUS_MAPPING = FAIL_CLOSED_PROVEN
CONTROLLED_FOLDER_INTAKE = PROVEN_AND_MERGED
OPERATIONAL_REVISION_TRANSITION = PROVEN_AND_MERGED
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
 with unchanged SHA and the minimum seven-zone workspace. Parent-03 adds
 controlled folder intake, same-package DOCX role/authority, restart/reopen,
 controlled export, and audited synthetic mechanism proof for forward-only
 revision transitions. Genuine multi-revision operational proof and foreign-
 reference operational evidence remain EVIDENCE_GAP and require no speculative
 fixture.
STORAGE_LAYOUT_NAMING = manual_upload/unlinked
REMOVE_FROM_DELTA_WHEN = Basic Team Bid Warehouse usability and the SOP
  workspace model are promoted to the Roadmap with verified operational evidence
  sufficient to close the remaining material evidence gaps.
PLANNER_NOTES = Seven folders are the canonical business/logical workspace
  view, not the database identity model and not necessarily the physical storage
  layout. `01_Source_E-HSMT` is source authority; `02_Requirement_Register` is a
  derived/controlled bridge; `03-05` are QI working E-HSDT material;
  `06_Submission_FINAL` must evolve toward immutable submission snapshots;
  `07_Evidence_Archive` is post-bid evidence, not a trash/cleanup target.
  Frontend collects commands and displays authoritative state; Domain Core and
  Application Backend own package/revision/membership/completeness semantics.
  Parent-03 is merged, but RD-0010 stays active because genuine multi-revision
  and foreign-reference operational evidence remain unresolved. No next WP is
  authorized until Human selects priority.
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
BOUNDARY_ONLY_DELTA_IDS = NONE
OUT_OF_PARENT_DELTA_IDS = RD-0007
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
## Storage Relief Sequencing Delta — WP-ENG-QI-CRAWLER-STORAGE-RELIEF-01A

PHASE-GUARD COMPLETE
→ STORAGE RELIEF HOLD
→ RESUME AT SANDBOX REARM
→ FRESH PRETRIAL PREFLIGHT
→ ONE REALF5
→ FINAL A3 AUDIT
→ HUMAN A0
→ A3 CLOSED

This sequencing does not change product architecture or authorize deletion.

## v0.10.0 cumulative candidate preparation delta

```text
DELTA_ID = RD-0011
STATE = BUILD_PARENT_INDEPENDENT_AUDIT_PASS_GOVERNANCE_CLOSEOUT_PENDING
TARGET_VERSION = 0.10.0
V091_TARGET = SUPERSEDED_BEFORE_OPERATIONAL_RELEASE
PRIMARY_GOAL = CUMULATIVE_INTERNAL_USE_RELEASE
NEW_PRODUCT_FEATURES = HOLD
ACTIVE_PARENT = WP-REL-V010-CANDIDATE-BUILD-01
PR116_PARENT = CLOSED_POST_MERGE_VERIFIED

SEQUENCE =
  RELEASE_IDENTITY_AND_INSTALLED_METADATA
  → ISOLATED_CANDIDATE_DATA_CLONE_REBASE
  → INDEPENDENT_PARENT_AUDIT
  → READINESS_RECEIPT_AND_FIRST_START_GATES
  → READINESS_MERGE
  → FREEZE_EXACT_MAIN_SHA
  → CANDIDATE_BUILD
  → PACKAGING_ACCEPTANCE
  → REAL_ISOLATED_CLONE
  → MIGRATION_ON_COPY
  → PRE_FIRST_BUSINESS_STARTUP_ACCEPTANCE
  → OPERATIONAL_ACCEPTANCE_WITH_SUCCESSOR_V010_LEDGER
  → HUMAN_PROMOTION_DECISION

BOUNDARIES =
  BUILD_ACCEPTANCE_ONLY;
  NO_OPERATIONAL_ACCEPTANCE;
  NO_DESTRUCTIVE_RECOVERY_TEST_ON_PRIMARY_CANDIDATE;
  NO_INSTALL_OR_PUBLISH;
  NO_NEW_PRODUCT_FEATURE;
  A3_F5_HISTORICAL_HOLD_PRESERVED

OPEN_PROMOTION_GATE = B09_FORWARD_ONLY_UNLESS_SEPARATELY_PROVEN
INSTALLER_GATE = B02_ISCC_DEFERRED_TO_INSTALLER_PHASE

PR116_AUDIT_CORRECTION = F01_WAL_COHERENCE_AND_F02_PROVENANCE_REAUDIT_PASS_MERGED
CANDIDATE_BUILD_ATTEMPT_01 = RETAINED_HOLD_EVIDENCE
CANDIDATE_BUILD_ATTEMPT_02 = RETAINED_HOLD_EVIDENCE
CANDIDATE_BUILD_ATTEMPT_02_B04 = PASS_FOR_ATTEMPT_02_ONLY
CANDIDATE_BUILD_ATTEMPT_02_REAL_CLONE = PASS_FOR_ATTEMPT_02_ONLY
CANDIDATE_BUILD_ATTEMPT_02_MIGRATION = NOT_EXECUTED_BINDING_HOLD
CANDIDATE_BUILD_ATTEMPT_02_STAGE3 = NOT_RUN
CANDIDATE_BUILD_ATTEMPT_02_STARTUP = NOT_RUN
CANDIDATE_BUILD_ATTEMPT_02_RETRY = NO
CANDIDATE_BUILD_ATTEMPT_03 = INDEPENDENT_AUDIT_PASS
CANDIDATE_BUILD_ATTEMPT_03_SOURCE_SHA = f6782d7eefb292870f8c78404e6c3e83f5fab1e2
CANDIDATE_BUILD_ATTEMPT_03_BUILD_ID = 20260919T013001Z
CANDIDATE_BUILD_ATTEMPT_03_CANDIDATE = D:\QI-Crawler-Candidates\v0.10.0-f6782d7e-20260919T013001Z
CANDIDATE_BUILD_ATTEMPT_03_B04 = PASS
CANDIDATE_BUILD_ATTEMPT_03_REAL_CLONE = PASS
CANDIDATE_BUILD_ATTEMPT_03_MIGRATION = PASS_0020_TO_0022
CANDIDATE_BUILD_ATTEMPT_03_STAGE3 = PASS
CANDIDATE_BUILD_ATTEMPT_03_INITIAL_START = PASS
CANDIDATE_BUILD_ATTEMPT_03_RESTART = PASS
CANDIDATE_BUILD_ATTEMPT_03_AUDIT = PASS_CANDIDATE_BUILD_ATTEMPT_03_AUDIT
WP_REL_V010_CANDIDATE_BUILD_01 = INDEPENDENT_CANDIDATE_BUILD_AUDIT_PASS
BUILD_IMPLEMENTATION_STATE = ATTEMPT_03_INITIAL_CANDIDATE_ACCEPTANCE_COMPLETE
OPEN_PARENT_IMPLEMENTATION_BLOCKERS = NONE
PARENT_VERDICT = PASS_BUILD_PARENT_CLOSEOUT
SOURCE_CORRECTION = WP-REL-V010-CANDIDATE-CLONE-COMPAT-01
SOURCE_CORRECTION_STATE = MERGED_AND_INHERITED_BY_ATTEMPT_02
SOURCE_CORRECTION_AUDIT = PASS_LEGACY_SOURCE_CONFIG_COMPAT_AUDIT
SOURCE_CORRECTION_BLOCKERS = NONE
FROZEN_EXECUTION_EOL_CORRECTION = AUDITED_AND_MERGED
FROZEN_EXECUTION_EOL_AUDIT = PASS_FROZEN_EXECUTION_EOL_COMPAT_AUDIT
FROZEN_EXECUTION_EOL_MERGED_MAIN_SHA = f6782d7eefb292870f8c78404e6c3e83f5fab1e2
FROZEN_EXECUTION_BINDING_MODES = RAW_EXACT; CRLF_WORKTREE_EQUIVALENT
ATTEMPT_02_RETRY = FORBIDDEN
READINESS_IMPLEMENTATION = INDEPENDENT_AUDIT_PASS
READINESS_BLOCKERS = NONE
CANDIDATE_EVIDENCE_LIFECYCLE =
  CLONE_RECEIPT
  → MIGRATION_RECEIPT
  → PORTABLE_ARTIFACT_RECEIPT
  → PRE_FIRST_BUSINESS_STARTUP_ACCEPTANCE
CLONE_RECEIPT_AUTHORITY = PRE_MIGRATION_CAPTURE_ONLY
MIGRATION_RECEIPT_REQUIRED_FIELDS = INPUT_CLONE_RECEIPT_SHA256; INPUT_DB_SHA256; FROM_REVISION; TO_REVISION; OUTPUT_DB_SHA256; MIGRATION_SOURCE_SHA; MIGRATION_RESULT; MANAGED_DOCUMENT_MAPPING_DIGEST
PRE_FIRST_BUSINESS_STARTUP_GATE = ACCEPTED_BUILD_IDENTITY; FROZEN_SOURCE_SHA; MIGRATED_DB_IDENTITY; SCHEMA_0022; MANAGED_DOCUMENT_MAPPING_DIGEST; ISOLATED_CONFIG_AND_ROOTS; COMPLETE_CLONE_AND_MIGRATION_LINEAGE
MANAGED_DOCUMENT_MAPPING_DIGEST_MODEL = SORTED_DOCUMENT_ID_PLUS_CANDIDATE_RELATIVE_PATH_PLUS_SHA256_PLUS_COUNT
CLONE_DB_HASH_PERMANENT_RUNTIME_INVARIANT = NO
FROZEN_SOURCE_SHA_MATCH = MANDATORY_BEFORE_CANDIDATE_ACCEPTANCE
FROZEN_MIGRATION_EXECUTION_BINDING = INDEPENDENTLY_AUDITED_PASS
PORTABLE_ARTIFACT_IDENTITY = INDEPENDENTLY_AUDITED_PASS
DIRECT_CANDIDATE_STARTUP = INDEPENDENTLY_AUDITED_FAIL_CLOSED
EFFECTIVE_CANDIDATE_DATABASE_TARGET = INDEPENDENTLY_AUDITED_CANDIDATE_ONLY
POST_ACCEPTANCE_RUNTIME = CANDIDATE_ROOT_AND_DATABASE_BOUND_WITH_MUTABLE_OPERATIONAL_DB_SUPPORTED
PREACCEPTANCE_SMOKE = EXPLICIT_ISOLATED_ROOT_ONLY
WORKING_SOURCE_MATERIAL_MUTATION = NO_OBSERVED_MATERIAL_MUTATION
WORKING_SOURCE_OBSERVATION_BASIS = HASH; SIZE; MTIME; READ_ONLY_SQLITE_VERIFICATION
OS_LEVEL_WORKING_DB_HANDLE_PROOF = NOT_AVAILABLE
BUILD_AUDIT_NOTE_01 = NONBLOCKING
CAPABILITIES_TOTAL = 66
VERIFIED_ON_BUILD_CANDIDATE = 4
NOT_VERIFIED = 57
DEFERRED_ENGINEERING_CAPABILITY = 5
CAPABILITY_TRUTH_ACCOUNTING = 66_OF_66_DISPOSITIONED
OPERATIONAL_ACCEPTANCE = NOT_COMPLETE
RECOVERY_ACCEPTANCE = NOT_COMPLETE
B02 = DEFER_INSTALLER_GATE
B04 = PASS_ATTEMPT_03
B06 = OPEN_ISOLATED_COPY_RECOVERY_ACCEPTANCE_GATE
B09 = OPEN_PROMOTION_GATE
PROJECT_MEMORY_UPDATE_THIS_WP = NO
PROJECT_MEMORY_PROMOTION = DEFER_TO_OPERATIONAL_ACCEPTANCE_CLOSEOUT
PROJECT_MEMORY_PROMOTION_CONDITION = OPERATIONAL_ACCEPTANCE_VERDICT_AND_B06_VERDICT_MERGED
OPERATIONAL_LEDGER_POLICY = DERIVE_SUCCESSOR_V010_LEDGER_LINKED_TO_IMMUTABLE_BUILD_LEDGER
OPERATIONAL_LEDGER_COLUMNS = HISTORICAL_REQUIREMENT; CURRENT_V010_EXPECTATION; OPERATIONAL_RESULT
NEXT_PARENT_CANDIDATE = WP-REL-V010-OPERATIONAL-ACCEPTANCE-01
NEXT_PARENT_PURPOSE = BOUNDED_TEAM_BID_WORKFLOW_ACCEPTANCE_AND_B06_RECOVERY_ACCEPTANCE
NEXT_PARENT_EXECUTION_AUTHORITY = NOT_GRANTED_BY_THIS_DOCS_MERGE
RECOVERY_TEST_TARGET = SEPARATELY_IDENTIFIED_RECOVERY_TEST_COPY
PRIMARY_CANDIDATE_DESTRUCTIVE_RECOVERY_TEST = FORBIDDEN
ROOT_BOUND_ACCEPTANCE_RECEIPT_REUSE_ON_RECOVERY_COPY = FORBIDDEN
AUDIT_F01 = RESOLVED_REAUDIT_PASS
AUDIT_F02 = RESOLVED_REAUDIT_PASS
AUDIT_F03 = RESOLVED_REAUDIT_PASS_WITH_F05_RUNTIME_HARDENING
AUDIT_F04 = RESOLVED_REAUDIT_PASS
AUDIT_F05 = RESOLVED_REAUDIT_PASS
NEXT = PLANNER_SEMANTIC_REVIEW_AFTER_GOVERNANCE_PR_EXACT_HEAD_HOSTED_CHECKS
```

This delta records a built and independently audited Build-scope candidate. It
does not grant Operational Acceptance, recovery acceptance, installation,
promotion, publication or release authority.

## v0.10.0 Team Bid UI correction delta

```text
DELTA_ID = RD-0012
STATE = CLOSED_POST_MERGE_VERIFIED
ACTIVE_PARENT = WP-REL-V010-TEAM-BID-UI-CORRECTION-01
AUDIT_TARGET_CODE_HEAD = 118d025601460f0bd411f7b26ee4b9740c25cad0
PREVIOUS_AUDIT_CODE_HEAD = 4a729d364ab5afbbd2da37cac555769a8526af23
PREVIOUS_AUDIT_DISPOSITION = HISTORICAL_PASS_SUPERSEDED_FOR_MERGE_AUTHORITY
NEW_HUMAN_FINDING = OA05_GUI_RECOVERY_CHAIN_LONG_OPERATION_LOCK
NEW_FINDING_CORRECTION = SOURCE_LEVEL_AUDITED_PASS

OA02 = SOURCE_LEVEL_AUDITED_PASS
OA04 = SOURCE_LEVEL_AUDITED_PASS
OA05 = SOURCE_LEVEL_AUDITED_PASS
OA06 = SOURCE_LEVEL_AUDITED_PASS
OA07 = SOURCE_LEVEL_AUDITED_PASS
PACKAGED_RUNTIME_ACCEPTANCE = NOT_PERFORMED

PR = 121
MERGED_PR_HEAD = de6f54059f14e01a8dc7ee18ef7bacc86752e00f
MERGE_COMMIT = 86fc5d239c19ebad7bc39fd02befe4f3657c6eef
POST_MERGE_PYTHON_CI = 35484375162_SUCCESS
POST_MERGE_CODEQL = 35484374723_SUCCESS

LOCAL_FOCUSED_GUI = 97_PASS
LOCAL_TEAM_BID_UI = 196_PASS
LOCAL_B06_ADJACENT = 18_PASS
LOCAL_CANONICAL_FULL = 1507_PASS_1_TRANSIENT_NATIVE_A3_FAIL
LOCAL_A3_CMD_PATH_AUTHORIZED_RETRY = 1_PASS
LOCAL_FULL_GATE = PASS_WITH_BOUNDED_TRANSIENT_INFRA_RETRY
LOCAL_RUFF = PASS
LOCAL_DIFF_CHECK = PASS

A3_VERIFICATION_OBSERVATION = TRANSIENT_NATIVE_ROUTE_STATE_NOT_REPRODUCED_ON_SINGLE_AUTHORIZED_RETRY
A3_PRODUCT_CORRECTION = NO

OLD_CANDIDATE = HISTORICAL_OPERATIONAL_ACCEPTANCE_HOLD
OLD_CANDIDATE_SOURCE = f6782d7eefb292870f8c78404e6c3e83f5fab1e2
OLD_CANDIDATE_MUTATED = NO
OPERATIONAL_ACCEPTANCE = HOLD
NEW_CANDIDATE = NOT_BUILT
B06_PREVIOUS_CANDIDATE = PASS_ISOLATED_MANAGED_SOURCE_RECOVERY_ACCEPTANCE
PR121_B06_IMPACT = ADJACENT_NO_RECOVERY_SEMANTIC_CHANGE
B06_NEW_CANDIDATE_BINDING = PENDING
B09 = OPEN
PROMOTION = NOT_AUTHORIZED

SCHEMA_CHANGE = NO
DOMAIN_ENUM_CHANGE = NO
RECOVERY_SEMANTIC_CHANGE = NO
PRODUCT_CHANGE = NO
TEST_CHANGE = NO
PROJECT_MEMORY_UPDATED = NO
PROJECT_MEMORY_PROMOTION = DEFERRED_UNTIL_OPERATIONAL_ACCEPTANCE_CLOSEOUT

NEXT_PARENT_CANDIDATE = WP-GOV-QI-WORKBENCH-ACTIVATION-01
NEXT_PARENT_PURPOSE = ACTIVATE_AND_STANDARDIZE_EXISTING_QI_AGENT_WORKBENCH_BASELINE_FOR_PLANNER_BUILDER_REVIEWER
NEXT_PARENT_PRODUCT_CHANGE = NO
NEXT_PARENT_RUNTIME_CHANGE = NO
WORKBENCH_BASELINE = EXISTING_DO_NOT_REBUILD
WORKBENCH_EXISTING_PILOT = 7_OF_7_PASS
NEXT = PLANNER_ISSUE_QI_WORKBENCH_ACTIVATION_01_WORK_ORDER
```

The corrections are merged, independently audited at source level and verified
by exact merge-head CI. Packaged-runtime acceptance remains unproven: no new
candidate was built, B06 binding for a successor candidate is pending, B09 is
open and promotion is unauthorized. The next governed lane activates the
existing QI Agent Workbench baseline; it does not rebuild the Workbench or
change product/runtime behavior.
