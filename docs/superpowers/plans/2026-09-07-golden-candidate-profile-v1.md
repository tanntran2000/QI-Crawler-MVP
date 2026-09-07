# GOLDEN_CANDIDATE_01 Profile v1 build plan

## Scope

`WO-GT01-PROFILE-V1-01` creates a separate
`GOLDEN_CANDIDATE_01_DRAFT_PROFILE_V1.xlsx` from the exact TBMT source and
leaves the historical `GOLDEN_CANDIDATE_01_DRAFT.xlsx` unchanged. The change
is limited to preparation tooling, tests, this plan, and a factual handoff
update. It does not change Bid Radar, filtering, GUI, database, migrations,
network behavior, S1, or package labels.

## Approved profile contract

- `PROFILE_ID = QI_TBMT_OPPORTUNITY_SCREENING`
- `PROFILE_VERSION = 1.0`
- `PROFILE_STATUS = APPROVED`
- `GROUND_TRUTH_STATUS = NOT_APPROVED`
- `C07 TECHNOLOGY_SCOPE = HARD`
- `C09 BUDGET = PREFERENCE`, preferred maximum `2,000,000,000 VND`
- `C10 EXECUTION_LOCATION = PREFERENCE`, using the exact Human-maintained
  region list `TP.HCM; Cần Giờ; Vũng Tàu; Bình Dương; Tây Ninh; Long An;
  Đồng Nai; Lâm Đồng; Phan Thiết`.
- C01, C02, C03, C04, C05, C06, C08, and C11 are `INACTIVE`.

The region list is a business list, not a radius or distance calculation.
Execution location is separate from the procuring entity address. Missing or
ambiguous evidence remains `UNKNOWN`.

## Workbook behavior

The profile sheet records screening, preference, priority, labeling order,
exclude-preservation, source authority, and the downstream solution-approval
gate. The label sheet keeps all 11 package decisions blank. The evidence sheet
keeps all 121 criterion rows, marks exactly 33 active rows (`C07`, `C09`,
`C10`) and 88 inactive rows, and leaves all expected outcomes blank.

Documented policy only:

- `C07 PASS → SELECT`, `UNKNOWN → NEEDS_REVIEW`, `FAIL → EXCLUDE`.
- `C09/C10 PASS` together with `C07 PASS` supports `HIGH`.
- A `SELECT` with either preference `FAIL` or `UNKNOWN` is `MEDIUM`.
- `NEEDS_REVIEW` and `EXCLUDE` are `UNRANKED`; excluded rows remain in audit
  evidence and are not deleted.

No package or criterion answer is calculated by the builder.

## Verification

Use TDD focused tests first, then affected importer/radar/selection/schema
tests, then the full suite. Record collection before and after, run Ruff and
`git diff --check`, generate the new artifact atomically, reopen it, and verify
source and historical-draft hashes before and after. Preserve the protected
untracked artifacts and keep the new workbook outside the implementation
commit unless repository policy requires otherwise.

## Stop boundary

Builder completion stops at `STOP_FOR_INDEPENDENT_REVIEW`. Profile approval
does not approve package-level Ground Truth and does not authorize S1.
