# GOLDEN_CANDIDATE_01 draft build plan

## Work Order

`WO-GT01-DRAFT-BUILD-01` builds a deterministic, reviewable draft workbook
from the exact TBMT source `TBMT_6_9_2026.xlsx`. The output is preparation
evidence only: no business profile, Team Bid labels, priority decisions,
Crawler predictions, S1, R2B, GUI, database, network, or product logic is
changed.

## Source contract

- Source: `D:/QI Technology/QI Crawler/business-data/TBMT_6_9_2026.xlsx`
- Type: TBMT workbook, sheet `Bản tin điện tử`
- Expected source SHA-256:
  `3FA652EBA17710647F29537D89A1B2C6E0F16660C7D0B0A5CCCEC05657B206D0`
- Expected data rows/imported rows: 11/11
- Expected unique identities: 11
- Source rows and SHA are rechecked before and after atomic output replacement.

## Draft workbook contract

The builder creates exactly four sheets, in this order:

1. `00_HUONG_DAN_PROFILE` — draft status, source identity, blank profile
   fields, blind-labeling instructions, documented aggregation rules, and
   the C01–C11 criterion catalog. Profile and Ground Truth remain
   `NOT_APPROVED`.
2. `01_NGUON_11_GOI` — source fields copied as literal values plus explicit
   QI identity/provenance columns (source sheet, source row, source SHA,
   observation key, and normalized selection method).
3. `02_TEAM_BID_GAN_NHAN` — one row per imported identity with blank expected
   screening, priority, and business labels and `LABEL_STATUS = DRAFT`.
4. `03_BANG_CHUNG_TIEU_CHI` — 11 criteria × 11 opportunities = 121 rows;
   objective source observations and coordinates only, with profile role
   `PENDING_PROFILE` and blank expected outcomes.

The output is written to a sibling temporary `.xlsx`, validated by reopening,
then installed with `os.replace`. Existing output files and source/output
collisions fail closed. Formula-like source strings are stored as literal text;
no formula cells are generated.

## Verification contract

- TDD focused tests cover workbook topology, row counts, provenance/anchor,
  label/prediction non-leakage, identity/output safety, formula safety, and
  no-partial-output behavior on validation failure.
- Run affected importer/radar/selection tests, then the full suite.
- Record collection count before and after; no unexpected decrease is allowed.
- Run Ruff and `git diff --check`.
- Reopen the real output and verify exact sheets, 11/11/121 row counts,
  source identity, blank answer/prediction fields, draft statuses, formula
  safety, and source hash/size invariance.
- Preserve the three pre-existing protected untracked artifacts exactly and
  keep `CURRENT.md` outside the implementation commit.

## Stop boundary

After Builder evidence is complete, stop with `STOP_FOR_INDEPENDENT_REVIEW`.
The draft is not Ground Truth approval and does not authorize S1 or any
runtime/product change.
