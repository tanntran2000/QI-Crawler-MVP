# QI-Crawler Agent Handoff

## HANDOFF_ID

POST-MERGE — WP-MI-TBMT-02B / MAIN-TRUTH-SYNC

## Status

WP-MI-TBMT-02B MERGED / MAIN TRUTH SYNCHRONIZED /
FULL REPOSITORY AUDIT HOLD FOR OUT-OF-SCOPE FINDINGS /
HOSTED CI PRE-EXECUTION FAILURE / RETRO-CI DEBT OPEN

## Active machine-readable checkpoint

```text
ACTIVE_PARENT_WP = NONE
ACTIVE_MICRO_WP = NONE
ACTIVE_BRANCH = main
PARENT_STATE = MERGED_MAIN_TRUTH
02B_1 = MERGED
02B_2 = MERGED
02B_3 = MERGED
FULL_REPO_AUDIT = HOLD
FULL_REPO_AUDIT_HEAD = 4acd2f1b69d3ad5a700d4a287ee5588e6337c4c5
FULL_REPO_AUDIT_DIRECT_02B_BLOCKERS = NONE
LAST_MERGED_PARENT_WP = WP-MI-TBMT-02B
LAST_MERGED_PR = 55
LAST_PRODUCT_MERGE_COMMIT = cbda73692dfe6b99c6a2045b2306b57e1e4136fb
LAST_MERGED_FEATURE_HEAD = 6513acfe7397467d1588fb3d404938ac04c8c00c
LAST_AUDITED_CODE_HEAD = b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a
PRODUCT_FRONTIER = Opportunity Intelligence
CURRENT_SCHEMA_REVISION = 0015_add_opportunity_review_events
P0_WAL_BACKUP = RESOLVED_LOCAL_AUDITED
P0_BACKUP_MECHANISM = SQLITE_CONNECTION_BACKUP
FC2_DOMAIN_APPLICATION_BOUNDARY = RESOLVED_LOCAL_AUDITED
FC2_ARCHITECTURE_GUARD = RESOLVED_LOCAL_AUDITED
PRODUCT_HOUSE_LAYERING = PASS
DOMAIN_BACKEND_SEPARATION = PASS
PARENT_CUMULATIVE_REVERIFICATION = PASS
PARENT_INDEPENDENT_AUDIT = PASS
PARENT_INTEGRATION_BLOCKERS = NONE
LAST_PARENT_TARGETED = 153 passed
LAST_LEGACY = 66 passed
COLLECTION = 609
FULL = 609 passed
RUFF = PASS
PIP_CHECK = PASS
DIFF_CHECK = PASS
CODEGRAPH = PASS
REVIEW_INHERITANCE = FORBIDDEN
IMPLICIT_HUMAN_REVIEW = ABSENT
LEGACY_KHMT_COMPATIBILITY = PASS
IMPORTANT_FOLLOWUP_BLOCKERS = WINDOWS_PUBLISHER_SCHEMA_DRIFT; LEGACY_BID_AUTHORITY_QUARANTINE; API_LAYER_BYPASS; BID_RADAR_SOURCE_INTEGRITY_BACKEND_ENFORCEMENT; TEST_CREATE_ALL_SHIM
PR_CI_RUN = 32803714442
PR_CI_EXECUTION = PRE_EXECUTION_FAILURE
MAIN_POST_MERGE_CI_RUN = 32804235113
MAIN_POST_MERGE_CI_EXECUTION = PRE_EXECUTION_FAILURE
MAIN_POST_MERGE_CI_JOB_STEPS = ZERO_FOR_ALL_4_JOBS
HOSTED_CI_MODE = TEMPORARY_UNAVAILABLE_QUOTA
HOSTED_CI_STATE = UNAVAILABLE_QUOTA
CI_PASS_CLAIMED = NO
PENDING_RETRO_CI = YES
OFFICIAL_TEAM_BID_RELEASE = BLOCKED
OPEN_BLOCKERS = WINDOWS_PUBLISHER_SCHEMA_DRIFT; LEGACY_BID_AUTHORITY_QUARANTINE; API_LAYER_BYPASS; BID_RADAR_SOURCE_INTEGRITY_BACKEND_ENFORCEMENT; TEST_CREATE_ALL_SHIM
MERGE_STATE = MERGED_MAIN
PUSH = NO
PR = NO
MERGE = MERGED_MAIN
NEXT_PARENT_OR_MICRO_WP = WP-GOV-FAILURE-MEMORY-01
NEXT_STATE = NOT_STARTED
EXACTLY_ONE_NEXT_ACTION = PLANNER DESIGN WP-GOV-FAILURE-MEMORY-01
NEXT_AUTHORITY = PLANNER_ARCHITECT
ACTIVE_DUPLICATE_KEYS = NONE
PROJECT_CONTEXT_MAP = docs/agent/MASTER_ROADMAP.md
ROADMAP_CONTEXT_REQUIRED = YES
```

## Main truth after merge

- WP-MI-TBMT-02B / PR #55 was merged at
  `cbda73692dfe6b99c6a2045b2306b57e1e4136fb`.
- The merged feature head was
  `6513acfe7397467d1588fb3d404938ac04c8c00c`; the audited code head was
  `b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a`.
- Live `main` HEAD must be verified from Git/GitHub at handoff entry; this
  document records the verified merge ancestry but does not replace live Git
  authority.
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

## Merged Parent — WP-MI-TBMT-02B

02B-1, 02B-2, and 02B-3 are merged. 02B-2 provides the source-neutral
filter/search projection and preserves legacy KHMT exclude-keyword compatibility
at its adapter boundary. 02B-3 provides the source-neutral review backend,
repository port, persistence adapter, and migration; export, GUI, and API
integration remain future work.

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
or GitHub truth. Before designing or executing the next Work Package:

- fetch live Git/GitHub;
- resolve the live `main` HEAD;
- reconcile it with the recorded historical merge ancestry;
- do not treat `CURRENT.md` as live Git authority;
- reconcile the live state with this historical merge evidence;
- define the design scope and obtain explicit Human implementation approval.

## Next governed action

The only next candidate is `WP-GOV-FAILURE-MEMORY-01`, not started and awaiting
Planner/Architect design.
