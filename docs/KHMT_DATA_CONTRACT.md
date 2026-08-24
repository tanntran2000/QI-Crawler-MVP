# KHMT Data Contract — MI-0

```text
DOCUMENT_CLASS = DURABLE DATA / DOMAIN CONTRACT
HISTORICAL_NOTES = MI-0 / MI-2 chronology below
```

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

The existing application uses SQLite for persisted runtime records; Excel
remains a source or derived artifact. This MI-0 contract introduces no MI
persistence schema. Any dedicated MI persistence boundary requires a separate,
migration-backed Work Package and is `REQUIRES_VERIFICATION` here.

## Historical MI-0 / MI-2 chronology

The sections below record the implementation phase in which these contracts
were introduced; they do not replace the durable rules above or the active
handoff.

### MI-2 discovery and targeted search

Discovery summarizes every normalized `PlanPackage` row without applying a
business preference. Province/city results retain `CONFIRMED`, `INFERRED`, and
`NEEDS_REVIEW` counts. Budget buckets are mutually exclusive: `<=100M`,
`>100M..<=300M`, `>300M..<=500M`, `>500M..<=1B`, `>1B`, and `UNKNOWN_PRICE`.
Location, budget, and selection-method totals must each reconcile to the input
package-row count; PL revisions and repeated rows are never collapsed.

Targeted search converts its request into the MI-1 `FilterProfile` and delegates
every package evaluation to `evaluate_plan_package`. It preserves stable input
order, provenance, the full `FilterEvaluation`, and the distinction between
matched and nonmatched rows. It does not score, rank, confirm, or reject a bid.

## Golden fixture

`tests/fixtures/khmt/khmt_sanitized_golden.json` is synthetic and safe for CI.
It is a contract fixture, not a real KHMT workbook and not an importer input.
