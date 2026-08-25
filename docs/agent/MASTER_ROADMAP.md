# QI-CRAWLER MASTER ROADMAP
# PRODUCT HOUSE & ARCHITECTURE README

QI-Crawler → Internal Bid Assistant

**Status:** MASTER BLUEPRINT / STRATEGIC ROADMAP / MANDATORY ARCHITECTURE README
**Blueprint revision:** 1.2 (conceptual roadmap revision; not application SemVer)
**Execution model:** PARENT-WP / MICRO-WP ONLY

**Core product boundary:** QI-Crawler reads, extracts, organizes, locates and
surfaces information. Team Bid validates, calculates, evaluates and decides.

> Roadmap node != implementation authorization. The roadmap tells agents where
> the product is going; a Human-approved Parent WP tells agents what may be
> implemented next.

This document is the canonical Product House and Architecture README. It is a
strategic blueprint, product capability roadmap and technical construction map
for every future agent. It is not an active handoff, live Git authority, Work
Order or source of proven merged facts.

### Architecture entry contract

For a `NEW AGENT`, `NEW PARENT WP`, `WRITER TAKEOVER`, `PLANNER TAKEOVER`,
`INDEPENDENT REVIEW` or `MATERIAL ARCHITECTURE / GOVERNANCE CHANGE`:

```text
→ governed FULL READ-IN
→ reconcile live Git/GitHub and CURRENT.md
→ only then READY / PROMPT_READY / implementation
```

A `NEW MICRO-WP` under the same approved Parent and unchanged architecture
baseline uses governed `DELTA READ-IN`; continuous work in the same Micro-WP
and Approval Lease uses governed `NO-RE-READ`. The selector and escalation
rules live in `docs/agent/MEMORY_INDEX.md`; this roadmap remains a strategic
blueprint, not a status dashboard.

## START HERE — 30-second orientation

QI-Crawler is being built as:

```text
QI-Crawler
→ Internal Bid Assistant
```

Current primary route:

```text
SOURCE ACQUISITION
→ OPPORTUNITY INTELLIGENCE
→ UNIFIED TENDER WAREHOUSE
→ TENDER PACKAGE & HSMT INTELLIGENCE
→ SOP BID INTELLIGENCE
→ HUMAN GROUND TRUTH
→ CONTROLLED LEARNING
→ BID ASSISTANT / OUTPUT
→ optional MINI AI AGENTS
```

```text
CURRENT_PRODUCT_FRONTIER = Opportunity Intelligence
ACTIVE EXECUTION STATE    → docs/agent_handoff/CURRENT.md → live Git/GitHub
```

Each horizontal capability is built vertically through the Product House
technical layers defined below. A layer can be mature while another remains
unwired; neither alone proves the complete Team Bid capability.

## Product House model

```text
                    HUMAN / MACHINE CONSUMERS
                              │
                              ▼
                      DELIVERY SURFACES
             GUI / CLI / API / Agent Adapter
                              │
                              ▼
                    APPLICATION BACKEND
                              │
                              ▼
                        DOMAIN CORE
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
          SOURCE ADAPTERS          INFRASTRUCTURE /
                                   PERSISTENCE
                │                           │
                └─────────────┬─────────────┘
                              ▼
                             DATA
```

The Engineering Toolbox / Plugins exists outside the Product House. This is
the target architecture model and classification doctrine; it does not claim a
one-to-one mapping to current Python packages.

### Consumers

```text
CONSUMER = who or what needs a product capability
```

Human consumers include Team Bid, SA, Maker, Checker, Bid Lead/Approver and
IT/operator. Machine consumers include CLI automation, API clients, reporting
processes, future Mini AI Agents and approved scheduled services.

```text
CONSUMER != FRONTEND
```

Team Bid is a Consumer and the Desktop GUI is a Delivery Surface. A future AI
Agent is a Consumer and an Agent Adapter is its controlled Delivery Surface.
Consumer status never grants authority; Human/business authority remains
governed by role.

### Delivery surfaces / frontend

Delivery surfaces are separate from the backend:

- **Desktop Frontend:** current PySide6 display, input, navigation, feedback
  and interaction surface.
- **CLI:** command delivery surface.
- **API:** transport/interface delivery surface; product API evolution is HOLD.
- **Agent Adapter:** future controlled surface for Mini AI consumers.

```text
FRONTEND != BACKEND
API != BACKEND CORE
CLI != BACKEND CORE
AGENT ADAPTER != AI AUTHORITY
```

No material business rule may exist only in a frontend event handler. Frontend
may collect a Human command, but Application Backend validates and executes it.
`BACKEND FIRST != FRONTEND NEVER`.

### Application Backend

Application Backend is executable product use cases and orchestration
independent of GUI. Examples include opportunity import/search/review/export,
Tender Package creation and revision linking, Warehouse completeness
inspection, HSMT evidence/requirements, Ground Truth and SOP readiness.

It coordinates Domain Core, Source Adapters, Persistence and controlled output
adapters, and must not depend on PySide6 behavior.

```text
BACKEND != SERVER
BACKEND != REST API
BACKEND != DATABASE
```

Application Backend development remains ACTIVE according to the current
frontier even while API evolution is HOLD.

### Domain Core

Domain Core is the load-bearing foundation for durable product meaning and
invariants: Opportunity and Tender Package identity, source type/namespace,
`base_id`, revision, provenance, review states, completeness states, Ground
Truth contracts and SOP readiness/domain states.

```text
PL != IB
base_id = lineage
(base_id, revision) = exact revision identity
IB...-00 Human Confirmed does NOT imply IB...-01 Human Confirmed
FILE STORED != PACKAGE COMPLETE
MACHINE READINESS != HUMAN BUSINESS DECISION
```

Domain Core must be understandable without GUI, database implementation,
network, Excel implementation, REST, GitHub or AI prompt logic.

### Source Adapters

Source Adapters are external material intake gates for KHMT XLSX, TBMT XLSX,
e-GP/web, manual HSMT, PDF, DOCX, XLSX tender documents and future approved
internal sources:

```text
EXTERNAL SOURCE
→ parse
→ validate
→ preserve raw/provenance
→ source/domain contract
```

```text
SOURCE FORMAT != DOMAIN MODEL
```

An adapter may observe source facts but may not create business authority. Do
not force TBMT into `PlanPackage` or infer Human confirmation from import.

### Infrastructure / Persistence

Infrastructure describes how bytes and data are stored and retrieved:
SQLite, Alembic-managed schema, managed filesystem, Source Vault, Package
Shelf, DuckDB, Parquet, archive and backup/recovery.

```text
DATABASE != DOMAIN
DATABASE COLUMN != DOMAIN CONTRACT
ONE PRODUCT WAREHOUSE != ONE DATABASE FILE
```

Unified Tender Warehouse is the product capability; SQLite/files/DuckDB/Parquet
are internal implementation components.

### Engineering Toolbox / Plugins

The toolbox is outside the Product House:

| Tool | Construction metaphor | Technical role | Boundary |
| --- | --- | --- | --- |
| CodeGraph | Structure scanner / dependency map | Impact, caller and dependency intelligence | Not scope or edit authority. |
| Superpowers | Construction procedure / handbook | Planning, TDD, debugging and verification discipline | Does not override `AGENTS.md`, Blueprint or Human Work Order. |
| pytest | Load/test equipment | Behavior and regression verification | Does not determine business truth. |
| Ruff | Quality measuring tool | Static/code quality checks | No product authority. |
| Alembic | Controlled plumbing renovation | Database migration mechanism | Does not authorize migration. |
| Git | Construction ledger | Exact version/change history | No merge authority by itself. |
| GitHub | Site control room | Remote history, PRs, collaboration and CI metadata | Human merge/release authority remains. |
| CI | Machine inspection gate | Automated verification | Not a business-authority pole. |
| Golden / regression corpus | Reference specimen | Deterministic evidence | Not automatically Human Ground Truth. |
| Build/Installer tools | Handover/build crew | Windows artifacts | Not release authority. |
| Diagnostics/logging | Sensors/meters | Failure evidence | Not automatic root-cause authority. |
| AI coding agents | Engineers/workers | Assigned Planner/Builder/Reviewer roles | `ROLE > MODEL NAME`. |

```text
TOOL != PRODUCT CAPABILITY
TOOL != AUTHORITY
PLUGIN RECOMMENDATION != APPROVED WORK ORDER
TOOL AVAILABILITY != TOOL AUTHORITY
CODEGRAPH IMPACT RADIUS != EDIT RADIUS
SUPERPOWERS PROCEDURE != PRODUCT SCOPE
```

Plugin states are `AVAILABLE`, `UNAVAILABLE`, `REQUIRES_VERIFICATION` and
`PARKED`. If a required tool is unavailable, report `TOOL_UNAVAILABLE` and use
the governed fallback. Never disable or remove a plugin merely to bypass its
workflow.

### Dependency direction

```text
CONSUMER
   ↓
DELIVERY SURFACE / INTERFACE ADAPTER
   ↓
APPLICATION BACKEND
   ↓
DOMAIN CORE
```

Source Adapters and Persistence implement/serve contracts consumed by backend
and domain boundaries. Forbidden authority dependencies include Domain Core →
PySide6, a domain rule that exists only in a GUI handler, TBMT parser → Human
`CONFIRMED`, AI Agent → uncontrolled SQLite writes, API endpoint → duplicated
business rules, and GUI → independently reimplemented filter/review semantics.

### Horizontal and vertical blueprint

The roadmap has two axes:

```text
HORIZONTAL: Source → Opportunity → Warehouse → HSMT → SOP → Ground Truth
            → Learning → Bid Assistant

VERTICAL:   Consumer → Delivery → Application Backend → Domain Core
            → Source Adapter → Infrastructure / Persistence
```

A capability may have `CORE_BACKEND = OPERATIONAL` while
`DESKTOP_GUI = NOT_WIRED`, or `FRONTEND = PRESENT` while
`DOMAIN_CAPABILITY = NOT_PROVEN`. Neither is simply `DONE`:

```text
BACKEND IMPLEMENTED != TEAM BID FEATURE DELIVERED
FRONTEND WIRED != DOMAIN CAPABILITY PROVEN
API EXISTS != PRODUCT AUTHORITY EXISTS
```

## Blueprint use and adaptive navigation

This document is a construction blueprint, not a status dashboard or an
implementation lease. Agents are engineers working on the same structure and
must consult it at the start of a Work Package/session, when a blocker or
systemic defect appears, before proposing a new strategic Parent Work Package,
architecture or refactor/tool/AI direction, and at major Parent closeout. The blueprint keeps
the mission, product structure, dependencies and safety boundaries stable while
allowing the Human-approved Parent decomposition, micro-WP count, sequence and
implementation details to adapt.

```text
CURRENT_PRODUCT_FRONTIER = Opportunity Intelligence
ACTIVE EXECUTION STATE    → docs/agent_handoff/CURRENT.md → live Git/GitHub
```

The default route is one primary frontier at a time. **NO ROADMAP EXPLOSION:**
do not create unrelated
Warehouse, HSMT or AI/UI Parents merely because those future lanes exist.
Prefer, in order: (1) continue the current Parent, (2) a bounded micro-WP,
(3) a forward correction, (4) re-plan an existing roadmap node, and only then
(5) propose a new Parent.

Before accepting a new slice, perform a **STRUCTURAL COMPATIBILITY** check:

- What capability does it serve and what verified gap explains why now?
- What dependency does it consume, and does it fit the existing Parent or
  micro-WP?
- Does it change the structural architecture, and where does work return to
  the roadmap?
- What Human approval is required?

Unsupported answers mean `PARK` or `ENTRY_HOLD`, not speculative expansion.
An adaptive `ROADMAP_DEVIATION_PROPOSAL` is reserved for a critical defect,
false-safe result, data-loss/security risk, architecture blocker, external
dependency or explicit Human priority. It must name the trigger, risk,
affected capability, bounded intervention, return point and Human approval.

## THREE-POLE DEVELOPMENT MODEL

```text
Human Authority
→ domain truth / intent / priorities / approvals /
  Ground Truth authority / business decisions

Planning & Audit Pole
→ clarification / reasoning / architecture /
  Blueprint alignment / Work Order / risk / audit

Builder / Single Writer Pole
→ implementation / testing / verification evidence /
  bounded findings

Machine Verifier
→ CI / Golden / local machine verification as governed
→ external evidence gate
→ NOT a fourth business-authority pole
```

```text
ROLE > MODEL NAME
```

No pole may silently assume another pole's authority. Planner, Reviewer and
Auditor roles remain separated wherever `AGENTS.md` or the approved Work Order
requires independence.

### Triangle closure

For material work, closure follows:

```text
HUMAN INTENT / AUTHORITY
        ↓
PLANNED / APPROVED CONTRACT
        ↓
BUILDER IMPLEMENTATION + EVIDENCE
        ↓
INDEPENDENT REVIEW
        ↓
MACHINE GATE RESOLVED
```

Builder `DONE`, passing tests, Human verbal agreement or Planner belief alone
does not close a change. The machine gate is `PASS` or explicitly classified
infrastructure-unavailable/waived under current governance; an authorized
waiver does not require hosted CI before closure.

## PROGRAM COMPLETION and resource map

The program is complete when QI-Crawler can safely:

```text
COLLECT → PRESERVE → ORGANIZE → UNDERSTAND → EXTRACT → PROVE
→ LEARN → ASSIST → DELIVER
```

Team Bid remains the decision authority. Completion does not mean no future
improvement, and Mini AI Agents are not a mandatory completion gate.

Completion mapping:

```text
COLLECT
  → Source Acquisition + Opportunity Intelligence
PRESERVE / ORGANIZE
  → Unified Tender Warehouse
UNDERSTAND / EXTRACT / PROVE
  → Tender Package & HSMT Intelligence
CONTROL / CONFIRM
  → SOP Bid Intelligence + Human review
LEARN
  → Ground Truth + Controlled Learning
ASSIST
  → Bid Assistant
DELIVER
  → Windows / outputs / approved delivery surfaces
```

GUI/API redesign completion is not mandatory unless required for agreed Team
Bid usability. Mini AI Agents remain optional.

Resource availability is explicit and must be verified at entry; roadmap prose
never makes a tool or service available by implication:

| Resource | State | Boundary |
| --- | --- | --- |
| CodeGraph | `AVAILABLE` / `REQUIRES_VERIFICATION` | Impact intelligence, not scope authority. |
| Superpowers | `AVAILABLE` / `REQUIRES_VERIFICATION` | Execution discipline, not planning authority. |
| pytest / Ruff | `AVAILABLE` / `REQUIRES_VERIFICATION` | Canonical local quality gates. |
| Alembic | `AVAILABLE` / `REQUIRES_VERIFICATION` | Only for approved schema work. |
| Git / GitHub | `AVAILABLE` / `REQUIRES_VERIFICATION` | Live repository/remote authority. |
| SQLite / review history | `AVAILABLE` / `REQUIRES_VERIFICATION` | System of Record for source/review state. |
| Managed file storage component | `PARTIAL` / `REQUIRES_VERIFICATION` | Internal component of Unified Tender Warehouse; use only its verified intake/storage contract. |
| Windows packaging/release | `OPERATIONAL` / `REQUIRES_VERIFICATION` | Release plumbing; no implicit publish authority. |
| Golden / real acceptance assets | `REQUIRES_VERIFICATION` | Evidence, never assumed available. |
| Governance docs / lessons / feedback | `AVAILABLE` / `REQUIRES_VERIFICATION` | Handoff continuity and systemic learning. |

CodeGraph and Superpowers, like all resources above, must be checked for actual
availability before relying on them; do not infer availability from this map.

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
UNIFIED TENDER WAREHOUSE
        ↓
TENDER PACKAGE & HSMT INTELLIGENCE
        ↓
SOP BID INTELLIGENCE
        ↓
HUMAN GROUND TRUTH
        ↓
CONTROLLED LEARNING
        ↓
BID ASSISTANT / OUTPUT
        ↓
MINI AI AGENTS
```

Cross-cutting lanes:

```text
WINDOWS / TEAM BID DELIVERY
QUALITY / VERIFICATION / RELEASE GOVERNANCE
```

Cross-cutting capability (not a third roadmap axis or Lane 10):

```text
KNOWLEDGE / RULE / VERIFICATION CORPUS
```

QI-KVS is a governed target architecture for versioned, evidence-backed
knowledge and verification rules. It does not change the Product Frontier,
interrupt Opportunity Intelligence, or activate a Knowledge DB/API/MCP.

```text
RULE CONTRACT != EVALUATOR IMPLEMENTATION
RULE CONTRACT = DATA
EVALUATOR = CODE
KNOWLEDGE RULE != SOURCE TRUTH
KNOWLEDGE RULE != HUMAN GROUND TRUTH
KNOWLEDGE RULE != SOP DECISION RECORD
ENGINEERING FAILURE MEMORY != PRODUCT KNOWLEDGE RULE
RULE BASIS EVIDENCE != RUNTIME EVALUATION EVIDENCE
ABSENCE_OF_DETECTION != PROOF_OF_ABSENCE
UNKNOWN != FALSE
UNKNOWN != COMPLETE
rule_id = knowledge lineage
(rule_id, version) = exact knowledge identity
ACTIVE KNOWLEDGE = HUMAN-APPROVED VERSIONED KNOWLEDGE BUNDLE
AI CONSUMER != KNOWLEDGE AUTHORITY
```

Target Product House placement:

```text
CONSUMER / FUTURE AI
→ DELIVERY SURFACE
→ APPLICATION BACKEND
  (KnowledgeRegistry / VerificationService / RuleSelection /
   ExplainEvaluation)
→ DOMAIN CORE
  (RuleId / RuleVersion / Applicability / VerificationMode /
   EvaluationOutcome / EvidenceContract)
→ EVALUATOR ADAPTERS + CANONICAL CORPUS / PERSISTENCE
```

The following evolution tracks are deliberately `HOLD` and do not create
Parent WPs in this reconciliation:

```text
GUI EVOLUTION   |   API EVOLUTION   |   CI EVOLUTION
```

## Capability matrix

| Capability | State | What exists now | Main gap | Next gate / dependency |
| --- | --- | --- | --- | --- |
| Source/web crawl | `STABLE` / `MAINTENANCE_ONLY` | Supported web adapters, discovery, retry/resume, dedup and compliance controls. | New-source coverage and bounded operational fixes only. | Human-prioritized source work; do not rework mature crawling for HSMT. |
| KHMT/PL intake | `OPERATIONAL` | Source-routed KHMT workbook intake preserves PL identity, raw fields and provenance. | Broader source variants may need bounded corrections. | Source evidence and regression fixture. |
| KHMT Bid Radar | `OPERATIONAL` | Import, targeted search, explicit Human review and derived confirmed outputs. | Future lifecycle expansion and richer operational workflows. | Human-approved scope after current handoff reconciliation. |
| TBMT source-neutral intake | `DONE` | TBMT XLSX importer produces IB `OpportunityCandidate` records with SHA/sheet/row provenance; source-neutral filter/search and Human Review persistence are merged. | Confirmed output, backend source-integrity closure, thin existing-GUI wiring and vertical KHMT/TBMT acceptance. | Active execution is governed by `CURRENT.md` and live Git/GitHub. |
| TBMT Bid Radar | `PARTIAL` | Source-neutral schema, parser, importer, filter/search and Human Review persistence are merged. | Source-neutral confirmed output, backend source-integrity closure, thin existing-GUI wiring and vertical KHMT/TBMT acceptance. | Active execution is governed by `CURRENT.md` and live Git/GitHub. |
| Unified Tender Warehouse | `PARTIAL` | Managed document storage foundations, hashing/identity, operational data stores, analytical warehouse assets and document intake foundations. | One package/revision shelf model, completeness, recovery, archive/integrity and source reconciliation. | Storage Reconciliation and protected-data verification. |
| Tender Package & HSMT Intelligence | `PARTIAL` | Native intake, identity/revision boundaries, evidence persistence and bounded HSMT source-fact foundations. | Complete package continuity, bundle coverage and reliable structured requirements. | Unified Tender Warehouse, Evidence and Human review contracts. |
| Native Evidence / Requirement Extraction | `PARTIAL` | Native PDF/DOCX/XLSX extraction, evidence rows and bounded source-fact parsers exist. | Broader requirement coverage, item linkage and completeness controls. | Tender Package continuity and Golden acceptance. |
| Completeness / Extraction Integrity | `PARTIAL` | Fail-closed flags and explicit uncertainty concepts exist in bounded areas. | Bundle completeness and false-safe prevention across full HSMT sets. | Evidence coverage and deterministic regression corpus. |
| Evidence Locator | `PARTIAL` | Page/sheet/section/table provenance is retained where available. | Consistent locators and reviewable source context across all facts. | Structured extraction and integrity gates. |
| SOP Bid Intelligence | `PLANNED` | Legacy/pilot bid analysis code and Human review foundations exist; no approved SOP evaluation engine is claimed. | Requirement Register → Cross-check → Gate readiness → Freeze/change-control workflow with Human authority. | Tender Package & HSMT Intelligence + Evidence + Human review contracts. |
| Human Ground Truth | `PARTIAL` | Human review concepts and source/revision boundaries exist. | Durable HSMT correction corpus and review workflow. | Structured extraction and exact revision identity. |
| Knowledge / Rule / Verification Corpus | `PLANNED` | Versioned-rule, evidence and Human-approval boundaries are defined by the QI-KVS blueprint. | Canonical corpus, evaluator implementation, validation and production activation. | Ground Truth, Golden regression and explicit Human approval. |
| Controlled Learning | `PARKED` | Governance boundary is defined; no self-modifying production behavior. | Evaluation dataset, candidate rules/models and approval lifecycle. | Ground Truth + Golden regression + Human promotion. |
| XLSX/DOCX outputs | `OPERATIONAL` | Confirmed package XLSX and Legal DOCX are derived from authoritative state. | Wider report bundles and HSMT evidence outputs. | Source-backed facts and explicit output contracts. |
| PDF/unified output | `PLANNED` | No unified output authority is claimed. | Approved template and evidence/report bundle contract. | Confirmed source facts and Human review. |
| Windows deployment | `OPERATIONAL` | Known-good v0.8.0 Windows delivery and persistent user-data boundary. | Future updates must preserve release/data governance. | Release impact assessment and verified candidate. |
| Mini AI agents | `PARKED` | Future role boundary is documented only. | Unified Tender Warehouse, completeness, evidence and Ground Truth gates. | All unlock gates plus explicit Human approval. |

### Capability layer maturity example — TBMT Bid Radar

```text
PRODUCT LANE:
  Opportunity Intelligence

DOMAIN CORE:
  PARTIAL — source-neutral Opportunity contract exists;
  downstream contract needs completion.

SOURCE ADAPTER:
  DONE for bounded TBMT XLSX intake.

APPLICATION BACKEND:
  PARTIAL — source-neutral filter/search/review persistence is merged;
  confirmed output and source-integrity closure remain.

PERSISTENCE:
  PARTIAL — source-neutral Opportunity Human Review persistence is merged;
  broader confirmed-output integration remains.

DESKTOP FRONTEND:
  THIN EXISTING-GUI WIRING PENDING — TBMT delivery is not fully wired.

CLI:
  not a required current Opportunity Intelligence delivery target
  unless separately approved.

API:
  HOLD.

TEAM BID DELIVERY:
  NOT YET OPERATIONAL for TBMT Bid Radar.
```

This is descriptive architecture status, not a substitute for `CURRENT.md`
or live Git/GitHub execution state. The current Opportunity Intelligence
delivery-closure Parent is human-approved; its active Micro-WP state remains
in `CURRENT.md` and live Git.

### Work Package architecture layer contract

Future material Work Orders must include:

```text
ARCHITECTURE_LAYER_CONTRACT
===========================

PRODUCT_LANE:

HUMAN_CONSUMER:
MACHINE_CONSUMER:

DOMAIN_CORE:
IN_SCOPE / OUT_OF_SCOPE

APPLICATION_BACKEND:
IN_SCOPE / OUT_OF_SCOPE

SOURCE_ADAPTERS:
IN_SCOPE / OUT_OF_SCOPE

PERSISTENCE_INFRA:
IN_SCOPE / OUT_OF_SCOPE

DELIVERY_ADAPTERS:
IN_SCOPE / OUT_OF_SCOPE

DESKTOP_FRONTEND:
IN_SCOPE / OUT_OF_SCOPE

CLI:
IN_SCOPE / OUT_OF_SCOPE

API:
IN_SCOPE / OUT_OF_SCOPE

AI_CONSUMER:
IN_SCOPE / OUT_OF_SCOPE

ENGINEERING_TOOLS:
required / optional / not applicable

DEPENDENCY_DIRECTION_CHECK:
PASS / HOLD

RATIONALE:
```

No Builder may silently cross an `OUT_OF_SCOPE` layer. A material new-layer
finding requires `BUILDER_FINDING + SCOPE_EXPANSION_REQUIRED +
STOP_FOR_REVIEW`.

### Engineer lookup table

| Change wanted | Start inspection at |
| --- | --- |
| IB revision semantics | Domain Core |
| Review inheritance | Domain Core |
| TBMT filtering | Application Backend |
| Human review workflow | Backend |
| Review DB schema | Persistence |
| TBMT Excel parser | Source Adapter |
| Package SHA/provenance | Domain Core + Source Adapter |
| Confirm button | Frontend |
| Button-to-service wiring | Delivery Adapter |
| REST endpoint | API Adapter |
| HSMT extraction | Backend + Source Adapter |
| Vault/file storage | Infrastructure |
| Warehouse completeness | Domain + Backend |
| Ground Truth rules | Domain + Backend |
| AI capability | Consumer / Agent Adapter |
| Impact discovery | CodeGraph tool |
| TDD/debug workflow | Superpowers tool |
| Migration execution | Alembic tool |
| Regression verification | pytest |
| Merge | Git/GitHub + Human authority |
| Release | Release governance + Human authority |

### Architecture invariants

```text
CONSUMER != FRONTEND
FRONTEND != BACKEND
API != BACKEND CORE
DATABASE != DOMAIN
SOURCE FORMAT != DOMAIN MODEL
PLUGIN != PRODUCT CAPABILITY
TOOL != AUTHORITY
MODEL NAME != AGENT ROLE

BACKEND IMPLEMENTED != TEAM BID FEATURE DELIVERED
FRONTEND WIRED != DOMAIN CAPABILITY PROVEN
FILE EXISTS != APPROVED PRODUCT AUTHORITY
```

No layer may silently assume another layer's authority.

### GUI / API hold clarification

```text
GUI_ARCHITECTURE_EVOLUTION = HOLD
API_PRODUCT_EVOLUTION = HOLD
```

This means no broad redesign or new interface architecture now. It does not
hold Application Backend development. Thin delivery wiring may be separately
approved after a backend capability is proven. `BACKEND FIRST != FRONTEND
NEVER`. No GUI/API work is activated by this roadmap WP.

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

Current direction is KHMT/PL operational. TBMT source-neutral intake,
filter/search and Human Review persistence are merged. Remaining gaps are
source-neutral confirmed output, backend source-integrity closure, thin
existing-GUI wiring and vertical KHMT/TBMT acceptance. The current Parent is
`WP-MI-TBMT-02C — Opportunity Intelligence Delivery Closure`, approved by
Human authority; active Micro-WP state remains in `CURRENT.md` and live Git.

Hard invariant:

```text
PL != IB
base_id = lineage
(base_id, revision) = exact source identity
IB...-00 Human Confirmed does NOT automatically imply IB...-01 Human Confirmed
```

No automatic review inheritance is defined by this roadmap.

## Lane 3 — Unified Tender Warehouse

**Mission:** provide one safe, organized repository for the complete lifecycle
of every tender package. This is one product capability, not one database or
storage engine.

```text
PACKAGE
  → exact REVISION
     → source documents
     → extracted evidence
     → requirements
     → Human review / Ground Truth
     → SOP working records
     → submission artifacts
     → outcome/archive
```

Physical shelf metaphor:

- Tender Package = shelf;
- Revision = revision compartment / version slot;
- documents, evidence and results = correctly classified shelf contents;
- the Crawler must know what belongs there and detect missing, conflicting or
  misplaced sources;
- a few stored files must never silently mean the shelf is complete.

Expected source-status concepts are `EXPECTED`, `FOUND`, `MISSING`,
`CONFLICT`, `UNKNOWN`, `SUPERSEDED` and `QUARANTINED`.

```text
FILE STORED != PACKAGE COMPLETE
```

Internal components may include SQLite, managed file storage, SHA identity,
DuckDB/Parquet analytical datasets and future archive backends. DuckDB and
Parquet are internal analytical components, not competing product warehouses.

The Warehouse must preserve source bytes, SHA, provenance, revision lineage,
old revisions and recovery ability. External deletion or movement must not
destroy managed source authority, and archive operations remain
non-destructive. Internal names may be machine-oriented while Team Bid output
remains business-oriented:

```text
INTERNAL STORAGE FORMAT != TEAM BID EXPORT FORMAT
```

### Warehouse shelf model — SOP alignment

This is conceptual product organization; it does not claim every shelf exists
today:

```text
01_SOURCE
  E-TBMT | E-HSMT | appendices | amendments | clarifications
  manually supplied authoritative sources

02_REQUIREMENTS
  Native Evidence | Requirement Register | structured source facts
  Critical Issues

03_EVIDENCE
  Legal | Capability | Technical | Vendor / NPP

04_SOP_WORKING
  Master Bid Data | Cross-check records | Gate evidence
  Change Control | Freeze records

05_SUBMISSION
  FINAL files | webform snapshots where applicable | submitted version
  receipt/status evidence

06_OUTCOME_ARCHIVE
  clarification | reconciliation | result | Win/Loss | lessons/handoff evidence
```

## Lane 4 — Tender Package & HSMT Intelligence

**Strategic priority: HIGHEST.**

**Mission:** connect the tender opportunity identity known from KHMT/TBMT with
the actual E-HSMT bundle and extract source-backed requirements from the
correct package revision.

Primary continuity:

```text
KHMT / PL
→ Opportunity

TBMT / IB
→ exact Tender Package identity

base_id + revision
→ Warehouse Package Shelf
→ HSMT Bundle
→ Native Evidence
→ Structured Requirements
→ Requirement Register
→ SOP Bid Intelligence
```

`PL != IB`; `base_id` is lineage and `(base_id, revision)` is the exact
source/review package revision. `IB...-00` and `IB...-01` share lineage but
remain distinct revisions. A new revision must not overwrite the old one,
silently replace source evidence, inherit Human confirmation automatically or
inherit Ground Truth where source context changed.

When no safe IB identity is known, manual HSMT intake is
`PROVISIONAL PACKAGE / HUMAN_LINK_REQUIRED`; do not invent an IB identity.

Human Verified Ground Truth is not only a downstream phase. It may be captured
during Tender Package & HSMT Intelligence as soon as the exact package and
revision, source evidence and Human review authority are present. Extraction
Ground Truth is a feedback loop used to harden HSMT before SOP Bid Intelligence
is complete. SOP Bid Intelligence later contributes SOP-specific review and
case records, but SOP Decision Records do not automatically become extraction
Ground Truth.

```text
HSMT Bundle
→ Native Evidence
→ Document Structure
→ Structured Requirement Extraction
→ Verification Profile
→ Rule Evaluation
→ Completeness / Extraction Integrity
→ Evidence Locator
→ Human Review / Ground Truth
```

Verification Profile and Rule Evaluation are target capabilities only. They
must not replace source evidence or Human authority. Rule outcomes are:
`SATISFIED`, `VIOLATED`, `INDETERMINATE`, `NOT_APPLICABLE` and
`NEEDS_HUMAN_REVIEW`.

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

## Lane 5 — SOP Bid Intelligence

**State: PLANNED.**

**Mission:** use structured source facts and evidence to support QI's
controlled package evaluation and confirmation workflow under the internal
SOP. This is not autonomous business decision authority.

```text
Tender Package & HSMT Intelligence
→ Bid Summary
→ Requirement Register
→ Critical Issue List
→ SOP evaluation
→ PASS / PENDING / FAIL / CRITICAL
→ Maker / Checker
→ Cross-check
→ Gate readiness
→ Freeze / Change Control
→ Human decision / confirmation
```

Required role and control concepts are `Maker`, `Checker`, `Approver / Bid
Lead`, `Submitter`, `Evidence Provider`, `Requirement ID`, `Master Bid Data`,
`Cross-check`, `Gate`, `Freeze`, `Change Control` and `Stop Rule`.

The Crawler may determine evidence/readiness facts such as correct
package/revision, source existence, evidence presence, locator presence,
unresolved `PENDING`, `Critical`, Checker review, and source/version conflict.
It may surface `READY_FOR_HUMAN_GATE_DECISION`,
`NOT_READY_MISSING_EVIDENCE`, `REQUIRES_CHECKER` and `SOURCE_CONFLICT`.
These are machine readiness statuses only:

```text
MACHINE READINESS STATUS != HUMAN GO/HOLD/NO-GO DECISION
```

SOP business roles retain GO/HOLD/NO-GO and Freeze authority. `SOURCE FACT !=
HUMAN BUSINESS DECISION` and `MACHINE READINESS != HUMAN APPROVAL`.

### Legacy bid-intelligence boundary

`src/qi_crawler/bid_intelligence.py` is a `REFACTOR TARGET / LEGACY-PILOT
ASSET`. Its heuristic scoring, estimated-win and GO/HOLD/NO-GO behavior is not
approved product authority. Future direction is:

```text
legacy analysis primitives where useful
→ evidence/readiness support
→ SOP evaluation records
→ Human-controlled Gate workflow
```

Do not delete or refactor it in this roadmap WP, and do not promise reuse until
the relevant behavior is verified.

## Lane 6 — Human Ground Truth

**Mission:** turn Team Bid corrections into durable Human-verified truth used
to measure Crawler accuracy, correct extraction errors, build regression
corpora and improve the Crawler safely.

Ground Truth is not every piece of business data, every Human business
decision, a synonym for SOP Gate status or automatic production-rule
promotion. Keep these four layers distinct:

```text
SOURCE TRUTH
= immutable/source-backed evidence from the exact package/revision

MACHINE OBSERVATION
= what the Crawler extracted or classified

HUMAN VERIFIED GROUND TRUTH
= Human-confirmed/corrected interpretation of that observation

SOP DECISION RECORD
= operational/business decision such as Gate, Freeze, GO, HOLD or NO-GO
```

The target Ground Truth record conceptually retains package `base_id`, exact
revision, document identity, source SHA, source locator, target/fact type,
machine prediction/state, Human verdict and corrected value/locator,
Maker/Checker/reviewer authority, review time/history, extractor/rule version,
error type and severity. This roadmap does not claim every field is currently
implemented.

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

```text
RULE BASIS EVIDENCE != RUNTIME EVALUATION EVIDENCE
```

### Ground Truth stability loop

```text
SOURCE / MACHINE OBSERVATION
→ HUMAN REVIEW
→ GROUND TRUTH
→ ERROR / PATTERN CORPUS
→ DISCOVERED RULE CANDIDATE
→ PENDING
→ RULE CONTRACT VALIDATION
→ EVALUATOR + GOLDEN
→ INDEPENDENT EVALUATION
→ HUMAN APPROVAL
→ APPROVED
→ ACTIVE RULE VERSION
→ VERSIONED KNOWLEDGE BUNDLE
→ PRODUCTION
```

```text
SELF-LEARNING != SELF-MODIFYING PRODUCTION
```

One observation must never directly mutate a production parser or rule. Ground
Truth serves three purposes: quality measurement of what the Crawler reads;
system improvement through verified failures and bounded fixes; and
organizational memory reusable across tender packages. Win/Loss or SOP
business decisions may be linked to future Case Memory, but do not
automatically become extraction Ground Truth.

## Lane 7 — Controlled Learning

**State: PARKED.**

```text
Ground Truth
→ recurring-pattern/error analysis
→ discovered rule candidate
→ pending rule-contract validation
→ evaluator + Golden regression
→ independent evaluation
→ Human approval
→ active rule version
→ versioned knowledge bundle
→ production
```

`SELF-LEARNING != SELF-MODIFYING PRODUCTION`. Future candidates may be
`DISCOVERED`, `PENDING`, `APPROVED`, `ACTIVE` or `DEPRECATED`, but no automatic
promotion is authorized by this roadmap. The future Agent Adapter is read-only
with respect to knowledge authority.

## Lane 8 — Bid Assistant / Output

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

## Lane 9 — Mini AI Agents

**State: PARKED.**

Future agents may suggest, classify, route, rank, compare, explain and recall.
They are not authorities and may not autonomously assign `HUMAN_CONFIRMED`,
`VERIFIED`, `APPROVED`, `FINAL_COMPLIANCE`, `FINAL_BOM`, `GO` or `NO_GO`.

Unlock gates are Unified Tender Warehouse, Completeness/Integrity, Structured Facts,
Evidence, Human Ground Truth and Golden regression, followed by explicit Human
authority.

## Existing asset register

This register tells future agents what already exists so they neither rebuild
it blindly nor promote experimental code accidentally. Asset disposition is
separate from roadmap capability state:

```text
ACTIVE | ACTIVE_FOUNDATION | ACTIVE_SUPPORT | HOLD_REUSE | PARKED
REQUIRES_VERIFICATION
EXPERIMENTAL | REFACTOR_TARGET
```

| Existing asset | Disposition | Roadmap role / boundary |
| --- | --- | --- |
| Authenticated source / e-GP session | `ACTIVE_SUPPORT` | Source Acquisition support. |
| Monitoring | `HOLD_REUSE` | Future opportunity monitoring/deadline support. |
| Notification / Reporting | `HOLD_REUSE` | Alerts and operational reporting. |
| Inventory / Stock | `PARKED` | Future internal supply/support evidence; **not BOM authority**. |
| Company Evidence | `REQUIRES_VERIFICATION` | Future SOP capability/evidence support if verified; external provider data is not automatic compliance truth. |
| DuckDB / Parquet analytical assets | `ACTIVE_FOUNDATION` | Internal analytical component of Unified Tender Warehouse; not a second product warehouse. |
| `smart_filter` | `PARKED` | Candidate asset, not current authority. |
| `ai_classifier` | `EXPERIMENTAL` | No automatic production promotion. |
| `competitor_analysis` | `EXPERIMENTAL` | No decision authority. |
| `price_intelligence` | `EXPERIMENTAL` | No purchasing or bid decision authority. |
| `bid_intelligence.py` | `REFACTOR_TARGET` | Legacy/pilot asset; not approved SOP authority. |
| XLSX / DOCX exporters | `ACTIVE` | Derived outputs from authoritative state. |
| Native extraction | `ACTIVE_FOUNDATION` | Source evidence foundation. |
| HSMT facts/parsers | `ACTIVE_FOUNDATION` | Source-fact foundation, not legal/business decision authority. |
| Ground Truth review service | `ACTIVE_FOUNDATION` | Append-only Human verification foundation. |
| GUI / CLI / API | `ACTIVE_SUPPORT` | Delivery surfaces; classify individually without creating roadmap lanes. |

```text
EXISTING ASSET != APPROVED PRODUCT AUTHORITY
PARKED / EXPERIMENTAL != AUTOMATIC PROMOTION
```

## GUI evolution — HOLD

```text
GUI_EVOLUTION = HOLD
```

The current GUI remains a usable delivery surface where already supported.
Do not authorize redesign in this roadmap WP. The future direction is a
package-centric UI rather than function-centric accumulation: Package/Revision
dashboard, Warehouse shelf, source completeness, document/evidence viewer,
Requirement Register, Critical/Pending view, SOP readiness, Maker/Checker,
Ground Truth correction, revision comparison and package retrieval. Unlock
requires stable Package/Revision, Warehouse, HSMT and SOP contracts. No GUI
Parent is created here.

## API evolution — HOLD

```text
API_EVOLUTION = HOLD
```

Do not expand API endpoints around legacy models merely to expose more data.
Future conceptual resources follow stabilized packages, revisions, documents,
evidence, requirements, reviews, Ground Truth, SOP readiness and exports. No
endpoint implementation is authorized here.

## CI evolution — HOLD, quality active

```text
CI_EVOLUTION_PROGRAM = HOLD
QUALITY_VERIFICATION = ACTIVE
```

Testing is not paused. Future bounded CI targets may include risk-based
matrices, collection protection, migration/schema gates, Golden HSMT and
Ground Truth regression, Warehouse integrity, Package/Revision lineage,
protected-data safety, Windows packaging smoke, release artifact integrity,
retro-CI debt handling and adaptive runtime budgets. Operational CI state
belongs to `CURRENT.md` and live GitHub.

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

Operational CI availability, waiver state and retro-CI debt belong to
`CURRENT.md` and live GitHub verification, not to this strategic roadmap. CI
Fitness evolves with capability risk; `CI GREEN` is evidence for tested
contracts, not proof of no bugs. Release eligibility depends on current
verified CI/release state, applicable governance and Human authority.

## Dependency rules and likely path

1. Mature source crawling does not block HSMT work when Team Bid can provide
   documents manually.
2. Opportunity Intelligence should complete TBMT Bid Radar integration before
   broad opportunity-lifecycle expansion.
3. Unified Tender Warehouse reliability should precede heavy reliance on large
   HSMT/AI historical corpora.
4. Tender Package & HSMT Intelligence must precede SOP Bid Intelligence.
5. Evidence and Completeness/Integrity are prerequisites for trusting HSMT
   semantic outputs and SOP readiness.
6. Human Verified Ground Truth may be captured during HSMT when exact package,
   evidence and review authority exist; SOP-specific records remain distinct.
7. Ground Truth precedes Controlled Learning.
8. Mini AI agent production integration remains parked until the trusted core
   gates are satisfied.
9. Human may change business priority; dependency safety still applies.

Likely development path, not an approval sequence:

```text
WP-MI-TBMT-02C — Opportunity Intelligence Delivery Closure
→ Unified Tender Warehouse reliability
→ Tender Package & HSMT Intelligence hardening
→ Completeness / Evidence
→ SOP Bid Intelligence
→ Human Ground Truth expansion
→ Controlled Learning
→ Bid Assistant outputs
→ Mini AI Agents
```

This path is NOT an approval sequence. Human may reorder business priority
when dependency safety remains satisfied.

## SOP business authority boundary

QI SOP defines the internal workflow and role/gate control model. Per-package
source authority remains the correct E-HSMT plus amendments, clarifications and
live system fields/state. SOP organizes QI evaluation but does not replace the
package source requirements.

```text
SOURCE FACT != HUMAN BUSINESS DECISION
MACHINE READINESS != HUMAN APPROVAL
GROUND TRUTH != SOP DECISION RECORD
```

No roadmap wording grants the Crawler final bid-decision authority.

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
