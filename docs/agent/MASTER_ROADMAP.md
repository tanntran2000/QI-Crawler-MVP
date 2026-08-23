# QI-Crawler Master Development Roadmap

QI-Crawler → Internal Bid Assistant

**Status:** MASTER BLUEPRINT / STRATEGIC ROADMAP
**Execution model:** PARENT-WP / MICRO-WP ONLY

**Core product boundary:** QI-Crawler reads, extracts, organizes, locates and
surfaces information. Team Bid validates, calculates, evaluates and decides.

> Roadmap node != implementation authorization. The roadmap tells agents where
> the product is going; a Human-approved Parent WP tells agents what may be
> implemented next.

## Authority and state vocabulary

The documents have distinct authority:

- `AGENTS.md` contains durable laws and governance.
- `docs/agent/PROJECT_MEMORY.md` contains durable verified facts already merged
  to `main`.
- `MASTER_ROADMAP.md` is the strategic capability map: existing, partial and
  missing capabilities, dependencies and likely development path.
- `CURRENT.md` is the active handoff/execution snapshot and may legitimately
  have `ACTIVE_PARENT_WP = NONE`.
- Live Git/GitHub is the authority for repository, branch, PR and CI state.
- Human decisions control product priority, scope and approval.

No roadmap entry overrides an explicit Human decision or merged evidence.

Roadmap states are qualitative only:

| State | Meaning |
| --- | --- |
| `STABLE` | Mature capability is protected from unnecessary redesign. |
| `OPERATIONAL` | Usable capability exists in the supported workflow. |
| `DONE` | The bounded capability contract is implemented and verified. |
| `PARTIAL` | Some foundations or slices exist; material gaps remain. |
| `PLANNED` | Dependency and scope are understood, but implementation is not active. |
| `PARKED` | Deliberately deferred until explicit unlock gates are met. |
| `BLOCKED` | Cannot safely proceed until a named blocker is resolved. |
| `MAINTENANCE_ONLY` | Mature lane receives only bounded fixes or Human-priority work. |

## Main product map

```text
SOURCE ACQUISITION
        ↓
OPPORTUNITY INTELLIGENCE
        ↓
TRUSTED DOCUMENT WAREHOUSE
        ↓
HSMT INTELLIGENCE
        ↓
HUMAN GROUND TRUTH
        ↓
CONTROLLED LEARNING
        ↓
BID ASSISTANT / OUTPUT
        ↓
MINI AI AGENTS
```

Windows / Team Bid delivery and Quality / CI / Release governance are
cross-cutting lanes across this path.

## Capability matrix

| Capability | State | What exists now | Main gap | Next gate / dependency |
| --- | --- | --- | --- | --- |
| Source/web crawl | `STABLE` / `MAINTENANCE_ONLY` | Supported web adapters, discovery, retry/resume, dedup and compliance controls. | New-source coverage and bounded operational fixes only. | Human-prioritized source work; do not rework mature crawling for HSMT. |
| KHMT/PL intake | `OPERATIONAL` | Source-routed KHMT workbook intake preserves PL identity, raw fields and provenance. | Broader source variants may need bounded corrections. | Source evidence and regression fixture. |
| KHMT Bid Radar | `OPERATIONAL` | Import, targeted search, explicit Human review and derived confirmed outputs. | Future lifecycle expansion and richer operational workflows. | Human-approved scope after current handoff reconciliation. |
| TBMT source-neutral intake | `DONE` | TBMT XLSX importer produces IB `OpportunityCandidate` records with SHA/sheet/row provenance. | Downstream Bid Radar integration is not wired. | Parent 02B design and Human approval. |
| TBMT Bid Radar | `PARTIAL` | Schema, parser, importer and revision semantics exist. | Filter/search, review persistence, confirmed export and GUI integration. | WP-MI-TBMT-02B design, then approval. |
| Managed Document Store | `PARTIAL` | Managed copy, hashing, duplicate/version handling, identity and bundle guards. | Fully trusted Vault/Shelf/Recovery/Warehouse integrity. | Storage Reconciliation → SHA Vault. |
| Trusted Document Warehouse | `PLANNED` | Architecture direction and safety boundaries are documented. | Canonical shelf, recovery, integrity, completeness and retention policy. | Storage Reconciliation and protected-data verification. |
| HSMT native evidence | `PARTIAL` | Native PDF/DOCX/XLSX intake and evidence persistence foundations exist. | Complete bundle/integrity handling and broader evidence inspection. | Warehouse integrity and evidence-locator gates. |
| HSMT semantic/structured extraction | `PARTIAL` | Bounded source-fact parsers and HSMT fact storage exist. | Completeness, item linkage, ambiguity handling and broader structured coverage. | Native Evidence + Extraction Integrity + Golden acceptance. |
| Completeness / Extraction Integrity | `PLANNED` | Fail-closed flags and explicit uncertainty concepts exist in bounded areas. | Bundle completeness and false-safe prevention across full HSMT sets. | Evidence coverage and deterministic regression corpus. |
| Evidence Locator | `PARTIAL` | Page/sheet/section/table provenance is retained where available. | Consistent locators and reviewable source context across all facts. | Structured extraction and integrity gates. |
| Human Ground Truth | `PLANNED` | Human review concepts and source/revision boundaries exist. | Durable HSMT correction corpus and review workflow. | Structured extraction and exact revision identity. |
| Controlled Learning | `PARKED` | Governance boundary is defined; no self-modifying production behavior. | Evaluation dataset, candidate rules/models and approval lifecycle. | Ground Truth + Golden regression + Human promotion. |
| XLSX/DOCX outputs | `OPERATIONAL` | Confirmed package XLSX and Legal DOCX are derived from authoritative state. | Wider report bundles and HSMT evidence outputs. | Source-backed facts and explicit output contracts. |
| PDF/unified output | `PLANNED` | No unified output authority is claimed. | Approved template and evidence/report bundle contract. | Confirmed source facts and Human review. |
| Windows deployment | `OPERATIONAL` | Known-good v0.8.0 Windows delivery and persistent user-data boundary. | Future updates must preserve release/data governance. | Release impact assessment and verified candidate. |
| Mini AI agents | `PARKED` | Future role boundary is documented only. | Trusted Warehouse, completeness, evidence and Ground Truth gates. | All unlock gates plus explicit Human approval. |

## Lane 1 — Source Acquisition

**Mission:** receive information from Muasamcong and supported web sources,
KHMT/TBMT Excel supplied by SA, HSMT files supplied by Team Bid and future
approved internal sources.

The mature crawler-web capability is independent from HSMT extraction. Web and
manual documents converge at the shared document/package boundary. `Crawl HSMT`
and `Extract HSMT` are separate capabilities; later HSMT work must not trigger
an unnecessary crawler rewrite.

## Lane 2 — Opportunity Intelligence

**Mission:** turn KHMT/TBMT sources into understandable, source-backed
opportunities for Team Bid.

Current direction is KHMT/PL operational, TBMT recognition and source-neutral
intake done, and TBMT downstream integration partial. The next candidate Parent
is `WP-MI-TBMT-02B — Bid Radar Integration`, subject to design and Human
approval. Concerns include source-neutral filter/search, revision-specific
Human Review persistence, approved migration if needed, confirmed export, GUI
integration and revision history/supersession behavior.

Hard invariant:

```text
PL != IB
base_id = lineage
(base_id, revision) = exact source identity
IB...-00 Human Confirmed does NOT automatically imply IB...-01 Human Confirmed
```

No automatic review inheritance is defined by this roadmap.

## Lane 3 — Trusted Document Warehouse

**Mission:** make QI-Crawler a safe document warehouse for Team Bid.

Development chain:

```text
Storage Reconciliation
→ SHA Vault
→ Package Shelf
→ Recovery
→ Warehouse Integrity
→ Bundle Completeness
→ retention / cleanup policy when storage pressure requires it
```

Target architecture:

```text
External File
→ Intake/Staging
→ crawler-managed copy
→ SHA / identity / provenance
→ immutable/raw Vault authority
→ Package / Revision Shelf
→ recovery/export
```

Deleting or moving an external file must not destroy the managed record.
Historical revisions must not be silently destroyed. Unknown/recovery
artifacts default to `KEEP`; destructive cleanup requires explicit safety
authority. Internal storage naming is machine-oriented; Team Bid export naming
is human/business-oriented.

```text
INTERNAL STORAGE FORMAT != TEAM BID EXPORT FORMAT
```

## Lane 4 — HSMT Intelligence

**Strategic priority: HIGHEST.**

**Mission:** transform HSMT documents into source-backed information that Team
Bid can review quickly.

```text
HSMT Bundle
→ Native Evidence
→ Document Structure
→ Structured Requirement Extraction
→ Completeness / Extraction Integrity
→ Evidence Locator
→ Human Review
```

The target source domains include package identity/value, owner, deadlines,
selection and contract terms, eligibility, legal/financial requirements,
experience, personnel, equipment, bid security, schedule, technical
requirements, supply items, materials/specifications, warranty/SLA, required
documents, evaluation criteria and commercial requirements.

Every material output remains traceable to file, page/sheet, section/table or
region, source excerpt/locator and provenance. The crawler extracts source
facts; it must not finalize BOM/BOQ, calculate bid quantities, choose
SKU/model/vendor, decide equivalence/compliance, decide GO/HOLD/NO-GO or replace
Human Ground Truth.

Historical integrity lesson:

```text
source contains 13 rows → crawler extracts 8
MUST NOT silently become COMPLETE
```

Use Bundle Completeness, Extraction Integrity, Structured/Semantic Extraction,
Evidence Locator and Golden HSMT acceptance as explicit capability gates.

## Lane 5 — Human Ground Truth

**Mission:** turn Team Bid corrections into durable, verified project/domain
truth.

```text
Crawler Prediction
→ Human Review
→ Correct / Incorrect / Missing / Conflict
→ verified correction
→ Ground Truth
→ Error Corpus
```

Ground Truth is verified data/evidence, not automatically a production code
change. Records should retain package, exact revision, source, evidence,
machine prediction, Human correction, review authority, error class and time/
history. A critical error means `HOLD` the affected capability/package, capture
Ground Truth, add regression, apply a minimal fix and re-verify.

## Lane 6 — Controlled Learning

**State: PARKED.**

```text
Ground Truth
→ recurring-pattern/error analysis
→ rule/model/pattern candidate
→ evaluation dataset
→ Golden regression
→ Human approval
→ promoted extractor/rule/model version
```

`SELF-LEARNING != SELF-MODIFYING PRODUCTION`. Future candidates may be
`DISCOVERED`, `PENDING`, `APPROVED`, `ACTIVE` or `DEPRECATED`, but no automatic
promotion is authorized by this roadmap.

## Lane 7 — Bid Assistant / Output

**Mission:** turn verified/source-backed information into useful Team Bid
working artifacts: XLSX, DOCX, PDF, checklists, requirement registers,
source/evidence reports and package export bundles.

Future bounded pre-fill is:

```text
verified data
→ approved template
→ bounded pre-fill
→ missing-field indication
→ Human review
```

Autonomous final bid-document approval is not authorized. Source-derived facts
remain separate from Team Bid derived/proposed data.

## Lane 8 — Mini AI Agents

**State: PARKED.**

Future agents may suggest, classify, route, rank, compare, explain and recall.
They are not authorities and may not autonomously assign `HUMAN_CONFIRMED`,
`VERIFIED`, `APPROVED`, `FINAL_COMPLIANCE`, `FINAL_BOM`, `GO` or `NO_GO`.

Unlock gates are Trusted Warehouse, Completeness/Integrity, Structured Facts,
Evidence, Human Ground Truth and Golden regression, followed by explicit Human
authority.

## Cross-cutting — Windows / Team Bid delivery

Development uses Python in an isolated developer environment. Team Bid uses a
Windows installer/executable with bundled runtime/dependencies and persistent
user data outside disposable build artifacts. The known-good v0.8.0 release is
immutable; this roadmap does not change the version.

```text
Implementation DONE != Official Team Bid RELEASED
```

Future user-visible work requires release-impact assessment.

## Cross-cutting — Quality / CI / release governance

Per-Parent and per-micro-WP verification flows through targeted tests, full
pytest where relevant, Ruff, diff-check, collection integrity,
migration/schema gates when relevant and protected-data safety. CI Fitness must
evolve with capability risk; `CI GREEN` is evidence, not proof of absence of
all bugs.

Current governance records hosted CI as `INFRASTRUCTURE_UNAVAILABLE`,
`CI_WAIVER = ACTIVE`, `PENDING_RETRO_CI = YES`. Official Team Bid release
remains blocked while applicable retro-CI debt is open unless Human authority
explicitly changes release authority.

## Dependency rules and likely path

1. Mature source crawling does not block HSMT work when Team Bid can provide
   documents manually.
2. Opportunity Intelligence should complete TBMT Bid Radar integration before
   broad opportunity-lifecycle expansion.
3. Trusted Warehouse should become reliable before relying heavily on large
   HSMT/AI historical corpora.
4. HSMT Structured Extraction must precede serious Ground Truth learning.
5. Evidence and Completeness/Integrity are prerequisites for trusting HSMT
   semantic outputs.
6. Ground Truth precedes Controlled Learning.
7. Mini AI agent production integration remains parked until Trusted Core gates
   are satisfied.
8. Human may change business priority; dependency safety still applies.

Likely development path, not an approval sequence:

```text
02B Bid Radar Integration
→ Warehouse reliability
→ HSMT completeness/evidence hardening
→ Structured HSMT extraction
→ Human Ground Truth
→ Controlled Learning
→ Bid Assistant outputs
→ Mini AI Agents
```

## Prompt Writer algorithm

When asked to write the next prompt, review:

```text
AGENTS
→ OPERATING_MODEL
→ HUMAN_COLLABORATION
→ LOCAL_STAGED_INTEGRATION
→ PROJECT_MEMORY
→ MASTER_ROADMAP
→ CURRENT
→ live Git/GitHub
```

Then verify current capability state, identify the completed capability, gap,
Human priority, dependency, risk boundary and current Parent status. Return
exactly one of:

```text
CONTINUE_EXISTING_PARENT
DESIGN_NEXT_PARENT
SPLIT_REVIEW_REQUIRED
PARKED
ENTRY_HOLD
```

Only after Parent design and Human approval may an implementation Work Order be
generated. `ROADMAP NODE != APPROVAL LEASE`.

## Parent closeout / roadmap reconciliation

After every major Parent WP merge/closeout, review:

- what capability improved;
- what became `DONE`/`OPERATIONAL`;
- what remains `PARTIAL`;
- what dependency became available;
- what risk/debt remains;
- whether this roadmap needs updating;
- which Parent is eligible next; and
- whether Human priority changed.

Update this roadmap only when a Parent changes capability maturity, Human
changes strategic priority, a major discovery changes dependencies/architecture,
a lane is parked/unparked, or a new strategic Parent is accepted. Do not update
it for every micro-WP.

## Roadmap safety boundary

This file contains no live `main` SHA, current branch assumption, temporary PR
number or current CI run ID as strategic authority. Historical evidence may be
referenced, but live Git/GitHub must always be reconciled at handoff entry.
