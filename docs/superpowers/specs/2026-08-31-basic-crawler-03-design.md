# WP-TB-BASIC-CRAWLER-03 — Real Revision Transition & Controlled Folder Intake

## 1. Mission and scope

This Parent defines a bounded design for real tender-package revision
transitions and controlled folder intake. It extends the proven Team Bid
Warehouse boundary without changing source crawlers, schemas, APIs, release
behavior or the existing Minimum Safe Warehouse implementation. The design is
planning authority only; no implementation is claimed.

## 2. Human Ground Truth revision semantics

`base_id` identifies tender lineage. An `IB...-00` suffix denotes the first
CĐT/e-GP published package revision; `IB...-01`, `-02` and later suffixes denote
later published revisions. Source revision is not a crawler version or file
version. The crawler recognizes explicit source evidence and never invents a
revision. Team Bid normally supplies the newest package known to them, but that
observation is not a claim of absolute latest e-GP publication.

## 3. Latest-forward-only / no-downgrade transition gate

The operational latest is the newest revision explicitly accepted for Team Bid
use. A newer accepted revision preserves the previous state, ingests the new
revision, compares previous versus latest and advances the operational latest.
A newer rejected revision causes no Warehouse state change. Input older than
the operational latest never downgrades it; the historical revision remains
readable. A revision mismatch places intake on HOLD and asks Team Bid whether
to continue. Downgrade is forbidden.

## 4. Previous-vs-latest comparison

Comparison is bounded to `PREVIOUS_OPERATIONAL_REVISION` versus
`LATEST_OPERATIONAL_REVISION`; arbitrary all-history comparison is not part of
this Parent. Source differences are represented as `UNCHANGED`, `CHANGED`,
`ADDED`, `REMOVED_FROM_NEW_REVISION` or `UNKNOWN_RELATION`. A source diff is
evidence, not a business decision.

## 5. Work-impact boundary

The system may surface potential work impact when source content changes, but
potential impact is not the same as invalid work. Team Bid remains the final
authority for rework, acceptance and continuation. The crawler does not infer
legal, commercial or bid decisions from a diff.

## 6. Read-only folder auto-scan + manual rescan

Selecting a folder triggers one automatic recursive read-only scan. The scan
does not import, rename, move or delete files. Team Bid may invoke a manual
rescan. A realtime watcher is not included. A discovered file is a candidate,
not a package member; parser-detected role is not source authority.

## 7. Human-controlled candidate-file intake

Every candidate file requires explicit Team Bid confirmation before Warehouse
ingest. Ambiguous or foreign-package candidates are held for Human correction
or retained as `REFERENCE_ONLY`; they are never silently promoted to source
membership. The source package and exact revision remain authoritative through
the domain, application and persistence contracts.

## 8. Cross-package / reference authority separation

Chapter III, Chapter V and similar names can occur in many tenders. Filename,
folder location, document role or parser output alone cannot establish package
membership. `REFERENCE_ONLY` is not source membership. Source E-HSMT,
working E-HSDT, final submission and reference material remain distinct
authority classes.

## 9. Short managed naming and metadata identity

The managed package folder carries the exact IB revision identity. Managed child
names may be short, such as `C3_01.docx`, `C5_01.docx`, `PL_01.xlsx`,
`REF_01.pdf` and `OTH_01.ext`. The original user filename is preserved as
metadata and is not the document identity. Managed naming, document ID,
document role and package membership remain separate concepts.

## 10. Micro-A/B/C architecture

Micro-A is real revision acceptance and defaults to no product-code change.
Micro-B is a conditional product correction lane opened only when Micro-A
proves a material blocker and Planner authorizes it. Micro-C is operational
closure after the bounded behavior is implemented and independently audited.
The sequence is `MICRO_A_REAL_REVISION_ACCEPTANCE →
CONDITIONAL_MICRO_B_PRODUCT_CORRECTION → MICRO_C_OPERATIONAL_CLOSURE`.

## 11. Acceptance contract

Acceptance must prove exact `(base_id, revision)` identity, preserved prior
revisions, latest-forward-only behavior, no downgrade, mismatch HOLD with
Human continuation, previous-versus-latest comparison, one-shot read-only
folder scan, manual rescan, candidate confirmation before ingest and
cross-package/reference separation. Evidence must distinguish source,
working, final and reference material and must not fabricate package or
revision facts.

## 12. Explicit exclusions

This design does not authorize source crawler rewrites, package completeness,
Vault or recovery/archive work, deep HSMT extraction, API evolution, CLI work,
realtime folder watching, automatic PL-to-IB inference, automatic ambiguous
case guessing, broad GUI redesign, release publication or Team Bid pilot.
Schema and migration changes are outside the PRE phase.

## 13. Roadmap/Delta/Product-House alignment

The design advances existing RD-0010 with supporting RD-0001 lifecycle and
RD-0004 sequencing context. RD-0008 and RD-0009 remain parked and
unauthorized. Product House ownership remains: Domain Core owns revision and
identity invariants; Application Backend owns folder discovery, confirmation
and comparison orchestration; Source Adapters read metadata without granting
authority; Persistence preserves revisions and managed naming; Delivery
Adapters provide thin wiring only when an audited blocker requires it. The
Unified Tender Warehouse remains the product capability and folders remain a
presentation/workspace surface rather than a database authority.
