HISTORICAL SNAPSHOT
NON-NORMATIVE
Captured before WP-GOV-DOC-LIFECYCLE-SYNC began.
Live execution authority is CURRENT.md + live Git/GitHub.

# QI-Crawler Agent Handoff

## HANDOFF_ID

POST-MERGE — WP-MI-TBMT-02A CLOSED / WP-MI-TBMT-02B DESIGN NEXT

## Status

WP-MI-TBMT-02A MERGED / PR #47 MERGED /
HOSTED CI INFRASTRUCTURE UNAVAILABLE / PENDING RETRO-CI /
NO OFFICIAL RELEASE / WP-MI-TBMT-02B NOT YET IMPLEMENTATION-AUTHORIZED

## Active machine-readable checkpoint

```text
ACTIVE_PARENT_WP = NONE
ACTIVE_BRANCH = NONE

LAST_MERGED_PARENT_WP = WP-MI-TBMT-02A
LAST_MERGED_PR = 47
LAST_AUDITED_FEATURE_HEAD = c89ccdf1ef5a35e70b534354fca2a155ce83d9a6
LAST_PRODUCT_MERGE_COMMIT = 8e6184bc2baadb9e8b7f4056f7e104247201197c

PR_STATE = MERGED
HOSTED_CI_STATE = INFRASTRUCTURE_UNAVAILABLE
PR_CI_RUN = 32643886740
PR_CI_EXECUTION = PRE_EXECUTION_FAILURE
PR_CI_JOB_STEPS = NULL_FOR_ALL_4_JOBS
CI_WAIVER = ACTIVE
PENDING_RETRO_CI = YES
OFFICIAL_TEAM_BID_RELEASE = BLOCKED

NEXT_PARENT_WP = WP-MI-TBMT-02B
NEXT_AUTHORITY = PLANNER_DESIGN_THEN_HUMAN_APPROVAL
STOP_STATE = READY_FOR_02B_DESIGN
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

## Next Parent — WP-MI-TBMT-02B planning boundary

WP-MI-TBMT-02B — Bid Radar Integration is **DESIGN NEXT**, not implementation-
authorized. A future approved Work Order may address:

1. source-neutral filter/search integration;
2. revision-specific Human Review persistence;
3. DB model/migration if separately approved;
4. confirmed-export integration;
5. Bid Radar GUI integration;
6. revision supersession/history policy.

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
