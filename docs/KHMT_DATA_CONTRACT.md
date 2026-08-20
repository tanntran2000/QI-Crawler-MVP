# KHMT Data Contract — MI-0

This contract defines source facts for future procurement-plan (KHMT) intake.
It does not implement workbook import, filtering, scoring, or decisions.

## Namespace and relationship rules

- `PL` procurement-plan identifiers and `IB` tender-notice identifiers are
  separate namespaces.
- An `IB` relation exists only when the source explicitly supplies it. It is
  never derived by changing an identifier prefix.
- One `(plan_base_id, plan_revision)` can contain several `PlanPackage` rows.
- Investor and bidding party are separate source facts unless a source states a
  relationship explicitly.

## Contract

`KHMTImportBatch` preserves source filename, SHA-256, sheet, import time, and
schema version. `ProcurementPlan` preserves `plan_id_raw`, `plan_base_id`, and
`plan_revision` separately. Each `PlanPackage` preserves its source row, raw
and normalized values, total investment, approval content, contract type,
execution duration, pricing, investor, project, method, schedule, and
provenance.

Province/city is the sole MI MVP geography. The observed KHMT source has no
dedicated location column, so MI-0 only preserves location evidence from an
actual source field (for example `NỘI DUNG PHÊ DUYỆT`). Resolution is not part
of MI-0; unresolved locations remain `NEEDS_REVIEW` and are never guessed.

SQLite will be the future system of record. Excel remains a source or derived
artifact. No MI persistence schema is introduced by MI-0.

## Golden fixture

`tests/fixtures/khmt/khmt_sanitized_golden.json` is synthetic and safe for CI.
It is a contract fixture, not a real KHMT workbook and not an importer input.
