# HISTORICAL SNAPSHOT

HISTORICAL SNAPSHOT / NON-NORMATIVE

Captured at WP-GOV-DOC-LIFECYCLE-SYNC Parent POST closeout candidate
before final independent integration audit.
LIVE AUTHORITY = docs/agent_handoff/CURRENT.md + live Git/GitHub

# QI-Crawler Agent Handoff

## HANDOFF_ID

POST — WP-GOV-DOC-LIFECYCLE-SYNC

## Status

PARENT CLOSEOUT CANDIDATE /
GOV-DOC-1 PASS /
GOV-DOC-2 PASS /
FINAL INTEGRATION AUDIT PENDING /
NO MERGE AUTHORIZED

## Active machine-readable checkpoint

```text
ACTIVE_PARENT_WP = WP-GOV-DOC-LIFECYCLE-SYNC
ACTIVE_MICRO_WP = NONE
ACTIVE_BRANCH = wp/gov-doc-lifecycle-sync

ENTRY_MAIN_HEAD = a44d365b48ad291aaa6e86c50adc72ed7318b883
ENTRY_HEAD = c9cb0d833a3432773d7940cc0252e8e3ac07f3c4
MICRO_STATE = PASS
LAST_AUDITED_DOC_HEAD = 5b5fe9163096a9c9c8c0eb5f4ab615d6cfae4882
LAST_COMPLETED_MICRO_WP = WP-GOV-DOC-LIFECYCLE-SYNC-2
LAST_COMPLETED_MICRO_POST_HEAD = 000842c4475e2712a65555b542e0ab33162cc1b4
LAST_COMPLETED_MICRO_REMOTE_STATE = CHECKPOINTED
PARENT_STATE = CLOSEOUT_PENDING_FINAL_INTEGRATION_AUDIT
OBJECTIVE = classify and repair stale operational/historical documentation without changing runtime behavior
PRODUCT_FRONTIER = Opportunity Intelligence
ARCHITECTURE_LAYER_CONTRACT = GOVERNANCE_DOCUMENTATION_ONLY

PAUSED_FEATURE_BRANCH = wp/mi-tbmt-02b
PAUSED_FEATURE_BRANCH_HEAD = 3e27c9c17d257cd91c544eaf6e5bb201087c0729
PAUSED_FEATURE_AUDITED_CODE_HEAD = 9db2ea8ee0876eae90ac0fbf9c8b495422d99611

HOSTED_CI_MODE = TEMPORARY_UNAVAILABLE_QUOTA
IMPLEMENTATION_HEAD = 1e59cd4991f8992629dfa54924f185bca46d05dd
RECONCILED_MAIN_HEAD = d2aa8a9bded931d54aaa50c398b701b1598024ec
OPEN_BLOCKERS = Final independent Parent governance integration audit required
PRE_WP_DOC_SYNC = CURRENT_PRE_COMMITTED_LOCAL
SCOPE_BOUNDARIES = GOV-DOC-2 six-document documentation classification/revalidation only; no runtime/test/migration/CI/release/product implementation; 02B-3 review persistence / migration / export / GUI / API remain outside this governance micro and remain HOLD
PROVEN_COMPLETE = Operational/historical documentation classification and currentness repair; PR52 baseline reconciliation; KHMT and technical-status delta revalidation; active checkpoint key normalization.
LAST_AUDIT = LOCAL_AUDIT_PASS + FC2 LOCAL_DELTA_AUDIT_PASS
GOV_DOC_2_REMOTE_CHECKPOINT = 5b5fe9163096a9c9c8c0eb5f4ab615d6cfae4882
GOV_DOC_2_POST_REMOTE_HEAD = 000842c4475e2712a65555b542e0ab33162cc1b4
LAST_MICRO_POST_REMOTE_HANDOFF = PASS
PARENT_POST_DOC_SYNC = LOCAL_PARENT_POST_COMMITTED_PENDING_FINAL_AUDIT
EXACTLY_ONE_NEXT_ACTION = INDEPENDENT REVIEWER FINAL AUDIT WP-GOV-DOC-LIFECYCLE-SYNC
NEXT_AUTHORITY = REVIEWER_AUDITOR

GOV_DOC_1 = PASS
GOV_DOC_1_AUDITED_DOC_HEAD = 88feb4f86e0a4372aaa26f3ba094cd69c2db7ff6
GOV_DOC_2 = PASS
GOV_DOC_2_IMPLEMENTATION_HEAD = 1e59cd4991f8992629dfa54924f185bca46d05dd
GOV_DOC_2_FINAL_AUDITED_DOC_HEAD = 5b5fe9163096a9c9c8c0eb5f4ab615d6cfae4882
PR52_STATE = MERGED
PR52_MERGE_SHA = d2aa8a9bded931d54aaa50c398b701b1598024ec
02B_1 = MERGED
02B_2 = MERGED
02B_3 = NOT_IMPLEMENTED / HOLD
LAST_AUDITED_02B_CODE_HEAD = 9db2ea8ee0876eae90ac0fbf9c8b495422d99611
VERIFICATION_STATE = 02B-2: 25 source-neutral targeted passed / 24 legacy KHMT passed / 583 full passed / 583 collected / Ruff PASS / diff-check PASS; GOV-DOC-2 independent audit PASS / FC2 duplicate-key delta re-audit PASS / diff-check PASS / pytest NOT_REQUIRED_DOCS_ONLY
PAUSED_FEATURE_REMOTE_CHECKPOINT = 9db2ea8ee0876eae90ac0fbf9c8b495422d99611
HOSTED_CI_STATE = UNAVAILABLE_QUOTA
CI_PASS_CLAIMED = NO
GOV_DOC_2_PRE_CORRECTION_REMOTE_HEAD = 6415fe8fe38e0bc5218976269d0995195ec9fd0e
LAST_AUDITED_CODE_HEAD != later handoff/docs HEAD

LAST_MERGED_PARENT_WP = WP-MI-TBMT-02A
LAST_MERGED_PR = 47
LAST_AUDITED_FEATURE_HEAD = c89ccdf1ef5a35e70b534354fca2a155ce83d9a6
LAST_PRODUCT_MERGE_COMMIT = 8e6184bc2baadb9e8b7f4056f7e104247201197c

PR_STATE = MERGED
LAST_MERGED_PR_HOSTED_CI_STATE = INFRASTRUCTURE_UNAVAILABLE
PR_CI_RUN = 32643886740
PR_CI_EXECUTION = PRE_EXECUTION_FAILURE
PR_CI_JOB_STEPS = NULL_FOR_ALL_4_JOBS
CI_WAIVER = ACTIVE
PENDING_RETRO_CI = YES
OFFICIAL_TEAM_BID_RELEASE = BLOCKED

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

## Active Parent — WP-MI-TBMT-02B / 02B-2 checkpoint

02B-1 and 02B-2 are complete and remotely checkpointed. 02B-2 provides the
source-neutral filter/search projection and preserves legacy KHMT exclude-keyword
compatibility at its adapter boundary. Review persistence, migration, export,
GUI, and API behavior are not implemented by 02B-2. 02B-3 remains held pending
Documentation Lifecycle Sync.

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
