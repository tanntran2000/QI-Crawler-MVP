# QI-Crawler Master Work Package

**Version:** `MASTER-WP-2026.08.19`

**Program name:** QI-Crawler → Internal Bid Operating Assistant

**Status:** `MASTER BLUEPRINT / ACTIVE ROADMAP`

**Execution rule:** This document is a program blueprint, not a single implementation Work Order. All implementation must be decomposed into bounded micro-WPs under `AGENTS.md` governance.

---

## 1. Product mission

QI-Crawler is not only a website crawler or Excel exporter. The long-term operating model is:

```text
EARLY DISCOVERY
      ↓
PL / KHLCNT
      ↓
FILTER / WATCHLIST
      ↓
IB / TBMT
      ↓
HSMT / ATTACHMENTS
      ↓
WAREHOUSE
      ↓
EXTRACTION
      ↓
FACT + EVIDENCE
      ↓
COMPLETENESS / CHECKER
      ↓
HUMAN REVIEW
      ↓
GROUND TRUTH
      ↓
BID WORKFLOW / INTELLIGENCE
```

North Star:

> QI-Crawler reads, extracts, organizes, locates and surfaces information. Team Bid validates, calculates, evaluates and decides.

QI-Crawler may:

- crawl and download;
- parse PDF/DOCX/XLSX/ZIP;
- manage SHA, document identity, package and revision;
- store source documents in a crawler-managed warehouse;
- extract Source Facts and typed values;
- attach Evidence Locators;
- detect missing sources, conflicts, partial coverage and `NEEDS_REVIEW`;
- organize information for Team Bid.

QI-Crawler must not:

- auto-add quantities or perform business derivation/conversion;
- create the final BOM/BOQ;
- calculate waste;
- select vendor, brand, model, SKU or replacement material;
- make final equivalence/compliance/legal conclusions;
- issue GO/HOLD/NO-GO business decisions;
- approve Ground Truth.

`Machine Verified != Human Approved`.

---

## 2. Source-of-truth hierarchy

When information conflicts, use the following order:

1. latest explicit Human instruction;
2. current approved Work Order;
3. `AGENTS.md`;
4. this Master Work Package / currently locked roadmap;
5. `docs/agent_handoff/CURRENT.md`;
6. Git/code/tests/migrations actually present;
7. GitHub PR/CI evidence;
8. historical handoffs and chat summaries.

Historical notes never override current Git evidence.

---

## 3. Core architecture boundary

Two capabilities are independent and may run separately.

### Capability A — Crawl HSMT

```text
website / e-GP
→ discovery
→ download
→ validate
→ Document Intake
→ SHA / identity / revision
→ Warehouse
→ STOP
```

### Capability B — Extract HSMT

```text
Warehouse document
or Team Bid manual upload
→ Native Extraction
→ Candidate
→ Structured Source Fact
→ Evidence
→ Completeness / Conflict
→ Human Review
```

They connect only through a document/artifact contract.

Forbidden coupling:

- Extractor calling an e-GP adapter directly;
- crawler creating semantic HSMT facts;
- parser depending on `source_url`;
- separate parser pipelines for web and manual documents.

SQLite is the System of Record. Excel is derived/export output only.

---

## 4. Procurement lifecycle identity model

`PL...` and `IB...` are different namespaces and must never be converted by replacing the prefix.

```text
PROCUREMENT PLAN
PL...
   ↓ explicit source relationship
PLAN PACKAGE
   ↓ may later produce
TENDER NOTICE
IB...
   ↓
HSMT / E-HSMT
```

Example of a forbidden assumption:

```text
PL2600263247
→ IB2600263247   ❌
```

The relationship must be captured from explicit e-GP/source fields.

Plan revision and notice revision are independent first-class values. Identical suffixes such as `-00` do not imply a shared revision chain.

---

## 5. Phase 0 — Crawler Core

The historical crawler foundation includes:

- baseline and Golden Dataset;
- source adapter, parser and idempotency;
- retry, crawl task, checkpoint/resume;
- Alembic / DB lifecycle;
- TBMT Excel export;
- FTS/search;
- list discovery, pagination and batch crawl;
- Windows operator/GUI/runtime foundation.

Authenticated e-GP access remains an external-capability lane and must not block manual HSMT intake/extraction.

---

## 6. Phase 1 — Document Foundation

Two intake paths are first-class:

```text
WEB DOWNLOAD ─┐
              ├→ DOCUMENT INTAKE
TEAM BID ADD ─┘
```

Supported input classes include PDF, DOCX, XLSX and ZIP.

Identity policy:

- content identity is primary when the document states it;
- filename is metadata only;
- a supporting attachment may legitimately contain no `IB...` code;
- Document Identity and Bundle Membership are separate concepts;
- Package and Revision remain first-class fields.

A manual Team Bid package is a valid package workspace even when no public source URL is present.

---

## 7. Phase 2 — Warehouse Trusted Core

Canonical intake path:

```text
EXTERNAL FILE
     ↓
STAGING
     ↓
validation
     ↓
SHA-256
     ↓
DOCUMENT IDENTITY
     ↓
BUNDLE GUARD
     ↓
ROLE CLASSIFICATION
     ↓
VAULT
     ↓
PACKAGE SHELF
     ↓
SQLite COMMIT
```

Logical document roles include:

- `PRIMARY_HSMT`;
- `CHAPTER_III`;
- `CHAPTER_V`;
- `SOURCE_BOQ`;
- `TECHNICAL_APPENDIX`;
- `PRICE_SCHEDULE`;
- `CONTRACT_DRAFT`;
- `AMENDMENT`;
- `CLARIFICATION`;
- `OTHER`.

Warehouse rules:

- external user paths are input only and never long-term authoritative storage;
- Vault is immutable SHA-backed source/backup storage;
- Package Shelf is the operational working copy;
- original filename remains preserved in the DB;
- internal filenames may be machine-oriented;
- exported packages reconstruct human/business-friendly names with the correct HSMT/E-TBMT code.

Missing Shelf behavior:

```text
Shelf missing
→ verify Vault SHA
→ MISSING / RECOVERABLE
→ explicit safe Restore
→ byte-identical copy
```

No silent automatic restore.

### Warehouse execution roadmap

```text
P0-A Bundle Guard                         ✅ CLOSED
P0-B1 Managed Storage Independence       FUNCTIONAL VERIFIED / MERGE HOLD
P0-B2 SHA Vault                          NEXT AFTER P0-B1
P0-B3 Canonical Package Shelf            AFTER P0-B2
P0-B4 Missing / Recoverable / Restore    AFTER P0-B3
        ↓
PIC-1 Warehouse Integrity
```

---

## 8. Phase 3 — Bundle Completeness

### P0-C — Bundle Completeness

The system must determine whether the package has the relevant sources required to support extraction.

Examples:

- a referenced Chapter V is missing → `SOURCE_DOCUMENT_MISSING`;
- missing source must never be interpreted as “0 requirements” or “complete”;
- supporting files with no embedded tender ID can still be valid via proven/human-linked bundle membership;
- conflicting source documents are retained independently.

---

## 9. Phase 4 — Extraction Integrity

Golden Tender invariant from `IB2600163730`, revision `00`:

```text
source Mẫu 01A = 13 supply rows
historical crawler result = 8 rows
```

Five rows were missed in a multi-page/page-boundary structure.

Critical invariant:

> `FOUND != COMPLETE`.

```text
source = 13
crawler = 8
→ COMPLETE is forbidden
```

When reliable sequential STT exists, gaps can be used as a completeness signal. When it does not, use other fail-closed signals such as:

- `COVERAGE_SUSPECT`;
- `PARTIAL`;
- `NEEDS_REVIEW`.

Cross-source rule:

```text
Mẫu 01A = 13
Chapter V = 14
→ retain both
→ SOURCE_CONFLICT
→ Human review
```

Never silently auto-merge/select.

### P0-D / R4.3B scope

- multi-page table continuity;
- page-boundary row fragmentation;
- exact package/revision extraction;
- source coverage;
- completeness status;
- source conflict;
- uncertainty propagation;
- false-safe prevention.

---

## 10. Phase 5 — Semantic Source Fact

Semantic extraction begins only after trusted document and completeness contracts are mature enough.

```text
Native Evidence
      ↓
Candidate
      ↓
Validate
      ↓
Structured Source Fact
```

Forbidden pattern:

```text
keyword hit
→ Fact   ❌
```

Representative Source Fact fields include:

- package identity and deadlines;
- selection/procedure/contract fields;
- eligibility, financial, experience, personnel and equipment requirements;
- bid security;
- supply item name, quantity and unit;
- material, dimensions, specifications, tolerances and standards;
- scope, schedule, warranty/SLA and documentary requirements;
- declared alternative/equivalence policy.

Typed parsing is allowed. Business derivation is not.

Example:

```text
source raw: "01 bộ"
→ quantity = 1
→ unit = "bộ"              ✅ typed parsing

1 bộ × 4 module
→ 4 module                  ❌ business derivation
```

---

## 11. Phase 6 — Requirement & Replacement Contract

### R5

A technical requirement must distinguish:

```text
TECHNICAL_REQUIREMENT_TYPE
+
REPLACEMENT_POLICY
```

Crawler may extract an equivalence/alternative policy explicitly stated by the HSMT, but may not decide that a proposed QI model/material is equivalent or compliant.

---

## 12. Phase 7 — Evidence Locator

### R6

Every important Fact must be traceable to its source.

Evidence should support as applicable:

- `document_id`;
- document SHA;
- page;
- sheet;
- section;
- table/row/cell/range;
- source text span / raw evidence.

UI principle:

```text
Fact
↓
[XEM EVIDENCE]
↓
correct file / page / sheet / row / section
```

Presentation tags/cards are not authoritative data objects. Structured Facts are.

---

## 13. Phase 8 — Human Review & Ground Truth

### R7

Human review states should support at least:

- `CONFIRMED`;
- `CORRECTED`;
- `MISSED_FACT_ADDED`;
- `REJECTED_FALSE_POSITIVE`;
- `WRONG_EVIDENCE`;
- `SOURCE_MISSING`;
- `SOURCE_CONFLICT`.

Ground Truth is a human-verified answer, not code and not an automatic production mutation.

```text
Prediction
↓
Human Review
↓
Verified Ground Truth
↓
Error Corpus
↓
rule/model candidate
↓
Golden regression
↓
Human-approved extractor version
```

Crawler must not self-modify production directly from feedback.

---

## 14. Critical Defect Law

Critical defects include, among others:

- wrong package;
- wrong revision;
- lost/corrupted source document;
- cross-package contamination;
- critical fact error;
- false-safe completeness such as `13 → 8` without warning.

Required response:

```text
ONE CRITICAL ERROR
       ↓
HOLD affected capability/package
       ↓
CAPTURE GROUND TRUTH
       ↓
MINIMAL RED FIXTURE
       ↓
FIX NOW
       ↓
rerun affected real HSMT
       ↓
Golden/full gates
       ↓
continue only if PASS
```

Do not batch critical defects.

---

## 15. Phase 9 — Golden HSMT & Quality

Initial real-package Golden Corpus includes at least:

- `IB2500585490-00`;
- `IB2600163730-00`.

Quality must eventually include semantic/business-safety measures, not only pytest status, for example:

- critical Source-Fact misses;
- false-safe count;
- supply-row recall;
- evidence accuracy;
- source coverage;
- human correction rate.

### WP2.7 — Quality & Audit

This gate precedes broad Bid Intelligence/AI authority expansion.

---

## 16. Phase 10 — KHMT / PL Early Discovery

Future lane:

> `WP-MI-1 — KHMT / PL Early Discovery & Bid Radar`

```text
KHMT / PL crawl
       ↓
normalize plan + plan packages
       ↓
structured filter
       ↓
watchlist
       ↓
track lifecycle
       ↓
explicit PL-package → IB relation
       ↓
TBMT / HSMT pipeline
```

Filter capability should combine structured and keyword criteria, such as:

- budget range;
- location;
- organization/unit type;
- selection method;
- package type;
- date;
- include/exclude keywords.

Representative internal profile:

```text
TPHCM ≤500M — Xã/Phường
Budget: <= 500,000,000
Location: TP.HCM
Preferred units: XÃ / PHƯỜNG
Optional selection methods: Chỉ định thầu / Chỉ định thầu rút gọn
```

The system may expose a match reason, but must not turn filter relevance into GO/NO-GO.

KHMT and TBMT require separate export contracts. Do not overload `TBMT-1.0` with KHMT semantics.

---

## 17. Phase 11 — Bid Assistant / Workflow

Only after Trusted Core and Quality are mature enough:

- Bid Summary;
- Requirement Register;
- checklist;
- task routing;
- deadline monitoring;
- missing-document warnings;
- Owner/Pending/Reviewed states;
- workflow state.

Crawler may surface outstanding facts/evidence/deadlines. Human remains the business decision authority.

---

## 18. Legal Reference lane

Legal support is a reference/cross-check lane, not a final legal decision engine.

```text
Source Fact
↓
Legal Identity
↓
Versioned Legal Reference
↓
Cross-check
↓
MATCH / POSSIBLE_MISMATCH / NEEDS_REVIEW / NOT_ENOUGH_DATA
↓
Bid / Legal Admin
```

Crawler must not emit final `LEGAL PASS`, `ILLEGAL` or equivalent conclusions on behalf of the responsible human.

---

## 19. AI lane — parked until Trusted Core maturity

Roadmap:

```text
WP-AI-0  Mini AI Reflex R&D / Feasibility
WP-AI-1  AI Provider + Authority Boundary
WP-AI-2  Local Tool Orchestration
WP-AI-3  Windows AI Pack / Installer Integration
```

AI may:

- suggest;
- classify;
- route;
- rank;
- compare;
- explain;
- recall.

AI may not create authoritative states such as:

- `VERIFIED`;
- `COMPLETE`;
- `APPROVED`;
- Human Ground Truth approval;
- uncontrolled package mutation;
- GO/NO-GO.

Do not insert AI into P0-B.

---

## 20. UX contract

Backend may extract large amounts of data; the UI should use progressive disclosure.

Representative package dashboard groups:

- Package Overview;
- Chapter III / Evaluation Criteria;
- Chapter V / Technical Requirements;
- Supply / Source BOM;
- Technical Specifications;
- SOW / Schedule;
- Documentary Requirements;
- Missing / Conflict / Needs Review;
- Evidence.

Cards summarize. Detailed Fact + Evidence appears only when opened.

Missing data must not visually resemble “no requirement”.

---

## 21. Export contract

Internal storage is machine-oriented:

```text
package_id
revision
document_id
role
sha256
```

User export is business-oriented, e.g.:

```text
IB2600163730-00/
├─ IB2600163730-00__HSMT.pdf
├─ IB2600163730-00__CHUONG_III.*
├─ IB2600163730-00__CHUONG_V.*
└─ ...
```

Principle:

> Store for machines; export for humans.

---

## 22. Multi-agent governance

Default role chain:

```text
HUMAN
Product Owner / Final Authority
      ↓
Planner / Architect
      ↓
Independent Reviewer / Auditor
      ↓
Single Writer
      ↓
GitHub Actions / Machine Verifier
      ↓
Independent Final Audit
      ↓
HUMAN Merge / Release Decision
```

`AGENTS.md` remains the constitutional authority for the engineering laws.

Every coding Work Order must define:

1. OBJECTIVE
2. IN SCOPE
3. OUT OF SCOPE
4. EXPECTED FILES / AREAS
5. ACCEPTANCE CRITERIA
6. STOP CONDITIONS
7. CI FITNESS CONTRACT

Unknown files/changes are `KEEP`.

---

## 23. Quality cadence

Every core micro-WP follows:

```text
Work Order
↓
Targeted Test
↓
Full python -m pytest
↓
Ruff
↓
git diff --check / scope hygiene
↓
data/runtime safety check
↓
CURRENT.md
↓
feature branch + PR
↓
GitHub CI
↓
Independent audit
↓
Human merge
```

After approximately 3–4 related WPs, run a Periodic Integration Checkpoint (PIC) covering more than a repeated pytest run:

- clean environment;
- blank DB;
- `alembic upgrade head`;
- cross-WP behavior;
- restart/persistence;
- warehouse integrity;
- architecture contract;
- selected real-HSMT regression.

Critical defects do not wait for PIC.

---

## 24. CI contract

Required technical jobs remain:

- `Code Quality`;
- `Tests Ubuntu 3.12`;
- `Tests Windows 3.12`;
- `Compatibility Ubuntu 3.11`.

Every required CI job has a hard maximum of 15 minutes.

If a job times out/stalls:

```text
HOLD
↓
classify root cause
  WP_CODE_DEFECT
  CI_INFRASTRUCTURE_DEFECT
  DEPENDENCY/NETWORK_DEFECT
  PRE-EXISTING_TECH_DEBT
  UNKNOWN
```

Do not blindly rerun, raise required timeouts casually, skip tests, use `continue-on-error`, or mask provisioning failures.

CI is adaptive verification, not a static fence.

---

## 25. CD contract

Future release automation should use Continuous Delivery rather than uncontrolled Continuous Deployment.

```text
protected main
↓
main integration gate
↓
Build / Package
↓
Release Candidate
↓
install/smoke/checksum
↓
Human approval
↓
Official Release
```

CI asks whether code is safe enough to enter main at current tested contracts. CD asks whether a verified commit can become a release artifact.

---

## 26. Current verified checkpoint — 2026-08-19

### Main

Current `main` baseline at creation of this document:

```text
bf48c949d000a41bcecc60757785feece8e30e72
Merge PR #16 — CI-Hardening-2B
```

CI-Hardening-2B established:

- explicit 15-minute cap on all four required jobs;
- `actions/checkout@v5`;
- `actions/setup-python@v6`;
- top-level `contents: read` workflow permission.

### PR #13 — P0-B1

```text
OPEN
head: b55f144ad9727634de08be67b3fb67e1fb93fb89
functional contract: PASS
merge gate: HOLD
```

P0-B1 proves managed-storage independence functionally, but the current exact-head CI baseline is not green enough to authorize merge under project governance.

### PR #17 — CI-Hardening-2C

```text
OPEN
head: a364f0dea978e1abf776d83379b3fcc51dea2773
change: Windows pytest → python -m pytest -q -n 2
merge gate: HOLD
```

GitHub run `32229107677` completed `cancelled`:

- Code Quality: PASS;
- Ubuntu 3.12: PASS;
- Ubuntu 3.11: PASS;
- Windows 3.12: CANCELLED at hard 15-minute budget;
- Windows pytest reached 255 passed in 847.56s before cancellation.

Therefore local `-n 2` benchmark evidence does not yet establish reliable hosted-Windows headroom.

### Current program state

```text
P0-A Bundle Guard                         ✅ CLOSED
P0-B1 Managed Storage Independence       ✅ FUNCTIONAL / ⛔ MERGE HOLD
CI runtime fitness                       ⛔ UNSTABLE
P0-B2 SHA Vault                          ⏳ NOT STARTED
P0-C Bundle Completeness                 ⏳ NOT STARTED
P0-D Extraction Integrity               ⏳ NOT STARTED
AI lane                                  ⏸ PARKED
```

Do not start P0-B2 while P0-B1/required-CI merge conditions remain unresolved.

---

## 27. Recommended next bounded sequence

```text
resolve required CI runtime stability
        ↓
exact-head verification for the CI fix
        ↓
Human merge CI hardening
        ↓
synchronize PR #13 with updated main
        ↓
fresh exact-head 4/4 GREEN
        ↓
Independent audit
        ↓
Human merge P0-B1
        ↓
P0-B2 SHA Vault
        ↓
P0-B3 Canonical Package Shelf
        ↓
P0-B4 Recovery
        ↓
PIC-1 Warehouse Integrity
        ↓
P0-C Bundle Completeness
        ↓
P0-D Extraction Integrity
        ↓
R5 Requirement Contract
        ↓
R6 Evidence Locator
        ↓
R7 Human Review / Ground Truth
        ↓
Golden HSMT
        ↓
WP2.7 Quality & Audit
```

Independent future lanes such as KHMT/PL Bid Radar must not expand the active P0-B scope.

---

## 28. Master definition of success

The trusted end-to-end target is:

```text
PL discovered
↓
structured filter narrows relevant opportunities
↓
watchlist tracks package lifecycle
↓
explicit source relation identifies IB/TBMT
↓
correct HSMT revision is acquired or manually supplied
↓
Warehouse stores it safely
↓
source-file deletion does not destroy crawler-managed data
↓
bundle is complete or fails closed
↓
Source Facts are extracted without false-safe completeness
↓
Fact has Evidence
↓
Human confirms/corrects
↓
Ground Truth is stored
↓
future extractor versions improve through regression-gated learning
↓
Team Bid receives trustworthy information at the right place to make the decision
```

This document defines the program direction. It does not authorize implementation outside the current bounded Work Order.
