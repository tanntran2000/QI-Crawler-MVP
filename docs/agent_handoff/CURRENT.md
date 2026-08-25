# QI-Crawler Agent Handoff

## HANDOFF_ID

POST — WP-MI-TBMT-02B / FULL-REPO-AUDIT-HOLD

## Status

PARENT LOCAL AUDIT PASS /
PARENT POST FINAL-STATE AUDIT PASS /
EXACT PARENT POST REMOTE CHECKPOINT VERIFIED /
FULL REPOSITORY AUDIT HOLD FOR OUT-OF-SCOPE FINDINGS /
DRAFT PR INTEGRATION AWAITS HUMAN AUTHORITY

## Active machine-readable checkpoint

```text
ACTIVE_PARENT_WP = WP-MI-TBMT-02B
ACTIVE_MICRO_WP = NONE
ACTIVE_BRANCH = wp/mi-tbmt-02b
PARENT_STATE = PASS_LOCAL_AUDITED_REMOTE_CHECKPOINTED_PENDING_PR_AUTHORITY
02B_1 = MERGED
02B_2 = MERGED
02B_3 = PASS_LOCAL_AUDITED
FULL_REPO_AUDIT = HOLD
FULL_REPO_AUDIT_HEAD = 4acd2f1b69d3ad5a700d4a287ee5588e6337c4c5
PARENT_CODE_HEAD = b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a
MAIN_BASE = 5deaab424ed691ffbc227830a230edfb54ff9d2f
PARENT_POST_HEAD = b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a
OLD_PARENT_POST_HEAD = 9d93cecbf43e9de2d450546cc09bb17d4801b829
PARENT_POST_STATUS = FINAL_STATE_AUDITED_REMOTE_CHECKPOINTED
OLD_PARENT_POST_STATUS = HISTORICAL_SUPERSEDED
CRITICAL_BLOCKER = NONE_FOR_02B
02B_BLOCKER = NONE
IMPORTANT_FOLLOWUP_BLOCKERS = WINDOWS_PUBLISHER_SCHEMA_DRIFT; LEGACY_BID_AUTHORITY_QUARANTINE; API_LAYER_BYPASS; BID_RADAR_SOURCE_INTEGRITY_BACKEND_ENFORCEMENT; TEST_CREATE_ALL_SHIM
PRODUCTION_MIGRATION = BLOCKED
FINAL_REMOTE_PUSH = COMPLETE_EXACT_HEAD
MERGE_STATE = PENDING_HUMAN_AUTHORITY
LAST_COMPLETED_MICRO_WP = WP-MI-TBMT-02B-3
LAST_PARENT_AUDIT = PARENT_CUMULATIVE_REVERIFICATION_PASS
PARENT_AUDIT_FINDINGS = NONE_FOR_02B
REMOTE_02B_BRANCH_STATE = VERIFIED_EXACT_PARENT_POST_CHECKPOINT
REMOTE_02B_HEAD = 2e079cf39f131973ebbd0a981bac4f1558238135
REMOTE_CHECKPOINT = 2e079cf39f131973ebbd0a981bac4f1558238135
REMOTE_CHECKPOINT_VERIFICATION = EXACT_HEAD_MATCH
02B3_REMOTE_CHECKPOINT = 4feb3654b1f1ae3a88706e2b1ae3cf9c0d2b529e
POST_STATE = FINAL_STATE_AUDITED_REMOTE_CHECKPOINTED_PENDING_PR_AUTHORITY
APPROVED_DESIGN = BACKEND_FIRST_OPTION_C
IMPLEMENTATION_AUTHORITY = HUMAN_APPROVED
02B3_BASE_IMPLEMENTATION_HEAD = 0d8461873eda483a28f6d2968c6a8be644a4cfd9
02B3_FC1_IMPLEMENTATION_HEAD = 047ddf076b9d48ca996b374b59bdeab356c3ca91
LAST_IMPLEMENTATION_HEAD = b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a

ENTRY_MAIN_HEAD = 5deaab424ed691ffbc227830a230edfb54ff9d2f
ENTRY_HEAD = 5deaab424ed691ffbc227830a230edfb54ff9d2f
PRODUCT_FRONTIER = Opportunity Intelligence
ARCHITECTURE_LAYER_CONTRACT = DOMAIN_CORE -> APPLICATION_BACKEND -> REPOSITORY_PORT -> INFRASTRUCTURE_PERSISTENCE

LAST_AUDITED_CODE_HEAD = b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a
PARENT_TARGETED_TEST_STATE = 153 passed / 0 failures
PARENT_LEGACY_TEST_STATE = 66 passed / 0 failures
COLLECTION_STATE = 609 collected / 0 errors
FULL_TEST_STATE = 609 passed / 0 failures
ALEMBIC_HEAD = 0015_add_opportunity_review_events
MIGRATION_INTEGRITY = PASS
RUFF_STATE = PASS
DIFF_CHECK_STATE = PASS
CODEGRAPH_STATE = PASS
PARENT_INDEPENDENT_AUDIT = PASS
PARENT_POST_AUDIT = PASS
PARENT_POST_FINAL_STATE_AUDIT = PASS
PARENT_CUMULATIVE_REVERIFICATION = PASS
PARENT_INTEGRATION_BLOCKERS = NONE
LAST_02B3_AUDIT_HEAD = 90351694d44aa7467f078017e90f17b150f2aaac
LAST_02B3_AUDIT = LOCAL_02B3_FC1_DELTA_AUDIT_PASS
AUDIT_FINDINGS = NONE
HISTORICAL_02B_HEAD = 3e27c9c17d257cd91c544eaf6e5bb201087c0729
SCOPE_BOUNDARIES = 02B-3 source-neutral Human Review backend and persistence only; no GUI; no CLI wiring; no API; no export wiring; no Tender Package creation; no scoring; no autonomous decision; legacy CandidateReviewService semantics unchanged
SCHEMA_CANDIDATE = 0015_add_opportunity_review_events
BACKEND_DEPENDENCY_DIRECTION = APPLICATION_BACKEND -> DOMAIN_REPOSITORY_PORT -> PERSISTENCE_ADAPTER
LEGACY_CANDIDATE_REVIEW = UNCHANGED
LAYER_BOUNDARY_STATE = PASS
02B3_DOMAIN_CORE_OWNER = src/qi_crawler/market_intelligence/opportunity_review_contract.py
02B3_APPLICATION_BACKEND_OWNER = src/qi_crawler/market_intelligence/opportunity_review.py
02B3_REPOSITORY_PORT_OWNER = src/qi_crawler/market_intelligence/opportunity_review.py
02B3_PERSISTENCE_OWNER = src/qi_crawler/opportunity_review_persistence.py
FRONTEND != BACKEND
BACKEND != DATABASE
DATABASE != DOMAIN
SOURCE FORMAT != DOMAIN MODEL
PL != IB
BASE_ID = LINEAGE
(BASE_ID, REVISION) = EXACT_REVISION_IDENTITY
IB...-00 HUMAN CONFIRMED DOES NOT IMPLY IB...-01 HUMAN CONFIRMED
IMPORT != HUMAN CONFIRMED
SEARCH != HUMAN CONFIRMED
FILTER MATCH != HUMAN CONFIRMED
RADAR PROJECTION != HUMAN CONFIRMED

CURRENT_SCHEMA_REVISION = 0015_add_opportunity_review_events
P0_WAL_BACKUP = RESOLVED_LOCAL_AUDITED
P0_BACKUP_MECHANISM = SQLITE_CONNECTION_BACKUP
FC2_DOMAIN_APPLICATION_BOUNDARY = RESOLVED_LOCAL_AUDITED
FC2_ARCHITECTURE_GUARD = RESOLVED_LOCAL_AUDITED
DOMAIN_BACKEND_SEPARATION = PASS
REVIEW_INHERITANCE = FORBIDDEN
OPEN_BLOCKERS = WINDOWS_PUBLISHER_SCHEMA_DRIFT; LEGACY_BID_AUTHORITY_QUARANTINE; API_LAYER_BYPASS; BID_RADAR_SOURCE_INTEGRITY_BACKEND_ENFORCEMENT; TEST_CREATE_ALL_SHIM
FULL_REPO_AUDIT_DIRECT_02B_BLOCKERS = NONE
EXACTLY_ONE_NEXT_ACTION = HUMAN AUTHORITY DECIDE DRAFT PR INTEGRATION
NEXT_AUTHORITY = HUMAN_AUTHORITY
STOP_STATE = STOP_FOR_HUMAN_PR_INTEGRATION_AUTHORITY
PUSH = NO
PR = NO
MERGE = NO
ACTIVE_DUPLICATE_KEYS = NONE

HOSTED_CI_MODE = TEMPORARY_UNAVAILABLE_QUOTA
HOSTED_CI_STATE = UNAVAILABLE_QUOTA
CI_PASS_CLAIMED = NO
PENDING_RETRO_CI = YES
OFFICIAL_TEAM_BID_RELEASE = BLOCKED

HISTORICAL_02B_HEAD_IN_MAIN_ANCESTRY = YES
LAST_MERGED_GOVERNANCE_PARENT_WP = WP-GOV-DOC-LIFECYCLE-SYNC
LAST_MERGED_GOVERNANCE_PR = 53
LAST_GOVERNANCE_BRANCH_HEAD = 514d8c3537dbda15c3b306d72e86306c3d1d0033
LAST_GOVERNANCE_AUDITED_HEAD = 17ec744cd594fd8cefec52dfde8fa39406b8f652
LAST_GOVERNANCE_MERGE_COMMIT = 9d76ca0f7ce0aba60e49a134e9a2a2d9825ac9e2
PARENT_FINAL_STATE_DOC_SYNC = REMOTE_FINAL_STATE_CHECKPOINTED_AND_MERGED

LAST_AUDITED_DOC_HEAD = 5b5fe9163096a9c9c8c0eb5f4ab615d6cfae4882
LAST_COMPLETED_MICRO_POST_HEAD = 4feb3654b1f1ae3a88706e2b1ae3cf9c0d2b529e
LAST_COMPLETED_MICRO_REMOTE_STATE = CHECKPOINTED
OBJECTIVE = exact Parent POST remote checkpoint verified; Draft PR integration awaits Human authority; full-repository audit remains HOLD for out-of-scope findings

PROVEN_COMPLETE = 02B-1 and 02B-2 source-neutral Opportunity contract/filter/search; 02B-3 Human Review backend/persistence; P0 WAL-safe backup; FC2 layer correction and architecture guard hardening.
PRODUCT_HOUSE_LAYERING = PASS
02B_DOMAIN_CORE = opportunity_contract.py; opportunity_radar.py; opportunity_review_contract.py
02B_APPLICATION_BACKEND = filter_engine.py; search.py; opportunity_review.py
02B_REPOSITORY_PORT = opportunity_review.py
02B_SOURCE_ADAPTER = TBMT/KHMT source adapters remain source-fact intake boundaries
02B_PERSISTENCE = opportunity_review_persistence.py; models.py; db.py; Alembic 0015
FRONTEND != BACKEND
BACKEND != DATABASE
DATABASE != DOMAIN
SOURCE FORMAT != DOMAIN MODEL
GOV_DOC_2_REMOTE_CHECKPOINT = 5b5fe9163096a9c9c8c0eb5f4ab615d6cfae4882
GOV_DOC_2_POST_REMOTE_HEAD = 000842c4475e2712a65555b542e0ab33162cc1b4
LAST_MICRO_POST_REMOTE_HANDOFF = PASS

GOV_DOC_1 = PASS
GOV_DOC_1_AUDITED_DOC_HEAD = 88feb4f86e0a4372aaa26f3ba094cd69c2db7ff6
GOV_DOC_2 = PASS
GOV_DOC_2_IMPLEMENTATION_HEAD = 1e59cd4991f8992629dfa54924f185bca46d05dd
GOV_DOC_2_FINAL_AUDITED_DOC_HEAD = 5b5fe9163096a9c9c8c0eb5f4ab615d6cfae4882
PR52_STATE = MERGED
PR52_MERGE_SHA = d2aa8a9bded931d54aaa50c398b701b1598024ec
02B3_FC1_FOCUSED_TESTS = 19 passed
02B3_COMPATIBILITY_TESTS = 67 passed
VERIFICATION_STATE = Parent cumulative re-verification: 153 targeted passed / 66 legacy passed / 609 full passed / 609 collected / Ruff PASS / pip check PASS / diff-check PASS
GOV_DOC_2_PRE_CORRECTION_REMOTE_HEAD = 6415fe8fe38e0bc5218976269d0995195ec9fd0e
LAST_AUDITED_CODE_HEAD != later handoff/docs HEAD

LAST_MERGED_PARENT_WP = WP-MI-TBMT-02A
LAST_MERGED_PR = 47
LAST_AUDITED_FEATURE_HEAD = c89ccdf1ef5a35e70b534354fca2a155ce83d9a6
LAST_PRODUCT_MERGE_COMMIT = 8e6184bc2baadb9e8b7f4056f7e104247201197c

PR_STATE = NOT_OPENED_FOR_CURRENT_PARENT_HEAD
LAST_MERGED_PR_HOSTED_CI_STATE = INFRASTRUCTURE_UNAVAILABLE
PR_CI_RUN = 32643886740
PR_CI_EXECUTION = PRE_EXECUTION_FAILURE
PR_CI_JOB_STEPS = NULL_FOR_ALL_4_JOBS
CI_WAIVER = ACTIVE

PROJECT_CONTEXT_MAP = docs/agent/MASTER_ROADMAP.md
ROADMAP_CONTEXT_REQUIRED = YES
```

## Main truth after merge

- WP-MI-TBMT-02A / PR #47 was merged at
  `8e6184bc2baadb9e8b7f4056f7e104247201197c`.
- Live `main` HEAD must be verified from Git/GitHub at handoff entry; this
  document does not attempt to predict its future docs-merge SHA.
- Runtime/package version remains `0.8.0`.
- Hosted CI remains unavailable because the recorded run failed before job
  execution; this is infrastructure evidence, not a product-test failure.
- `PENDING_RETRO_CI = YES`; no official Team Bid release is authorized while
  this debt remains open.

## Completed Parent WP — WP-MI-TBMT-02A

### 02A-1 — Source-neutral Opportunity identity/candidate contract

Introduced `OpportunitySourceType` (`KHMT`/`TBMT`), separate `PL`/`IB`
identity namespaces, source-backed identity/import-batch/candidate contracts,
raw/base/revision consistency, positive source-row and SHA checks, and
authoritative provenance consistency. `PL != IB`; no PL↔IB conversion.

### 02A-2 — TBMT schema + conservative IB parser/normalization

Implemented the observed TBMT schema and fail-closed revisioned IB parsing,
including the distinction between an identity revision delimiter and a title
delimiter. Ambiguous or extended identity-like tokens remain rejected.

### 02A-3 — TBMT workbook importer → OpportunityCandidate

Added bounded read-only `.xlsx` import with header scanning, SHA-256/sheet/time/
schema provenance, IB-only identity construction, complete raw-field retention,
conservative price parsing, issue reporting, and no silent source-row
deduplication. TBMT does not enter the KHMT `PlanPackage` path.

### 02A-4 — Real-file/read-only acceptance + Parent Integration Gate

The protected real workbook was read only. Acceptance recorded:

```text
source rows = 72
candidates = 72
issues = 0
SHA-256 = E4B8FF62D8FF979BD646287EB7C894B9F03D089691B9122A6A96847457A1CDB4
size = 120194 bytes
source bytes/size unchanged = YES
```

The final local regression evidence was 532 passed; latest collection after
the revision-domain contract was 534; Ruff and diff-check passed. This is
real-file/read-only acceptance, not a `Golden` label.

## CodeGraph evidence

Queries executed in the merged checkout:

```text
codegraph explore "Merged TBMT facts for OpportunityIdentity, OpportunityCandidate, import_tbmt_workbook, and parse_tbmt_notice_identity; confirm source-neutral TBMT importer, IB namespace, PL != IB, and provenance fields"
codegraph explore "import_tbmt_workbook"
codegraph explore "parse_tbmt_notice_identity"
codegraph explore "OpportunityIdentity"
```

The graph returned the relevant source/caller graph and confirmed the merged
source-neutral contract boundary: TBMT importer/normalization produces IB
opportunity identities with source provenance; it is distinct from KHMT
`PlanPackage` and does not authorize review/export/GUI behavior.

## Active Parent — WP-MI-TBMT-02B / 02B-3 implementation checkpoint

02B-1 and 02B-2 are complete and remotely checkpointed. 02B-2 provides the
source-neutral filter/search projection and preserves legacy KHMT exclude-keyword
compatibility at its adapter boundary. 02B-3 adds only the source-neutral review
backend, repository port, persistence adapter, and migration; export, GUI, and
API behavior remain out of scope and unauthorized.

Hard invariant:

```text
IB...-00 Human Review does NOT automatically confirm IB...-01.
same base_id = same lineage, not same exact reviewed identity.
```

No automatic review inheritance is designed or authorized in this handoff.

## Data / release safety

- Do not access or mutate protected business data or `%LOCALAPPDATA%\QI-Crawler`.
- No production DB migration/downgrade/stamp/repair is authorized here.
- Version remains `0.8.0`; known-good release artifacts remain immutable.
- Retro-CI debt remains open.

## Delivery authority

This file is the active handoff snapshot, not an alternative source of live Git
or GitHub truth. Before designing or executing 02B:

- fetch live Git/GitHub;
- resolve the live `main` HEAD;
- reconcile it with the recorded historical merge ancestry;
- do not treat `CURRENT.md` as live Git authority;
- define the design scope and obtain explicit Human implementation approval.
