HISTORICAL / NON-NORMATIVE

# CURRENT PRE — WP-WH-MIN-01

Captured at exact Parent entry base:

```text
PARENT_WP = WP-WH-MIN-01 — Minimum Safe Tender Package Warehouse
ENTRY_BASE = 74c5430f7188f29f26b88c6f20052b52aa0a3f70
ARCHITECTURE_OPTION = B_DOMAIN_FIRST_TENDERCASE
PRODUCT_FRONTIER = Unified Tender Warehouse
```

Human A0 selected Option B: TenderCase/domain/database identity remains
authoritative; filesystem and folder presentation may be added later but must
not become identity authority. The protected invariants are:

```text
BUSINESS_FOLDER != DATABASE_IDENTITY
FILENAME != DOCUMENT_IDENTITY
DOCUMENT_ROLE != PACKAGE_MEMBERSHIP
PL != IB
base_id = lineage
(base_id, revision) = exact revision identity
```

Relevant Delta entries are `RD-0001`, `RD-0004`, `RD-0008`, `RD-0009` and
`RD-0010`; `RD-0003` and `RD-0007` remain outside this Parent. The approved
execution model is two large bounded batches:

```text
BATCH A — CORE
TenderCase/lifecycle/revision domain contract; managed-source reuse;
persistence; Package/Revision Shelf membership; reopen; integrity-checked
retrieval core.

BATCH B — OPERATIONAL
Operational retrieval/export; seven logical SOP zones; thin Team Bid delivery
wiring; restart/reopen UX; real operational acceptance.
```

At this capture, Warehouse implementation was not yet proven. Stage 0
materialized the Parent PRE authority and Batch A entry; technical execution
remains bounded by the approved Work Order, its exclusions and independent
review gate.
