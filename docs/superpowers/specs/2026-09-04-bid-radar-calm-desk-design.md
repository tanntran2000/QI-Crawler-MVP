# QI BID DESK — CALM BID RADAR

## Status and authority

- Work package: WP-BID-RADAR-HARDENING-01.
- Micro: MICRO-A0 — DESIGN SPEC + IMPLEMENTATION PLAN.
- Human A0 approved the redesign; this document is a bounded implementation contract, not product code.
- Audited baseline: 0fbf50bc25e85ff58f8f53214a30f1c4708bea0a.
- Canonical Work Order, repository governance, CURRENT.md and live Git remain authoritative. This design cannot authorize edits by itself.

## Objective

Provide Team Bid with a calm, explainable Bid Radar desk for narrowing real opportunity records, inspecting the selected tender, recording an independent Human Review decision, and handing a confirmed observation to the existing Tender Workspace/Warehouse seams. The design changes presentation and focused application behavior only; it does not change source authority, persistence authority or business decision authority.

## Authority and cognitive safety

These distinctions are mandatory:

- PL is not IB. PL notice identity and IB tender/revision identity remain separate.
- base_id is a lineage and (base_id, revision) is an exact revision identity. Confirming IB...-00 never confirms IB...-01.
- Filter matching and normalization never create Human Review events.
- FILTER MATCH is not HUMAN CONFIRMED and CONFIRMED OPPORTUNITY is not BUSINESS GO.
- GUI calls application/backend facades. GUI never queries SQLite/DuckDB or writes Warehouse state directly.
- Missing, unsupported or ambiguous values stay UNKNOWN, UNSUPPORTED or NEEDS_REVIEW; they are never silently coerced.

Cognitive safety is an operational control: clarity before density, recognition before recall, one primary task per region, one dominant action per state, progressive disclosure, decision-relevant defaults, secondary technical metadata and state-based color. Decoration must never compete with amount, deadline, location, match reason or review state.

## Calm desktop layout

The modern enterprise desktop is organized as:

    GLOBAL NAVIGATION
            |
            +-- SELECTION DESK (preferred 280–320 px)
            |     Source / Khoanh vùng / shared Keyword Profile /
            |     saved-profile extension seam
            |
            +-- ACTIVE TENDER CANVAS (flexible center)
            |     active chips / funnel summary / Opportunity Result Grid
            |
            +-- SMART INSPECTOR (preferred 300–340 px)
                  Quick View / Match Reasons / Search /
                  evidence seam / Warehouse / Review / Revision / History seam

Left and right panels collapse independently. The result grid owns bounded internal scrolling; filter and Inspector panes may scroll vertically without nested-page chaos. There is no page-level horizontal overflow, clipped control or overlap. Preferred widths are guidance rather than fixed-resolution assumptions. Acceptance covers representative Windows sizes at 100%, 125% and 150% DPI.

## Selection Desk and filter studio

The default view is calm and compact:

    KHOANH VÙNG
    TP.HCM + 100 km
    500 triệu – 1,3 tỷ
    Đấu thầu rộng rãi · 1G1T
    [Chỉnh bộ lọc]

    KEYWORDS
    QI-CNTT-v3 · 12 include · 6 exclude
    [mạng] [switch] [CNTT] [+9]

Chỉnh bộ lọc expands one Filter Studio containing budget, geography, selection method, supported online status and supported one-stage-one-envelope. Include and exclude keywords remain one shared keyword profile. Saved profiles are an extension seam, not a second authority or implicit persistence feature.

Effective criteria are always visible as chips above the result grid. Removing a chip explicitly changes the request and re-evaluates rows.

## Filter pipeline and neutral state

The application flow is:

    SOURCE
      -> schema normalization
      -> hard/business scope criteria
      -> shared include/exclude keywords
      -> filter disposition plus reason evidence
      -> explicit Human Review

Money input is schema-driven. A MONEY field accepts unambiguous forms 1.000.000.000, 1 000 000 000, 1,000,000,000 and 1000000000, returning raw value, normalized value, parse status and field/provenance context. Digits in a TEXT field remain text; punctuation never globally changes type.

An empty active criteria set is not match-all. It returns a neutral CHƯA LỌC / NO_ACTIVE_CRITERIA state with an explicit explanation. Existing source-neutral search contracts remain compatible and any intentional full-listing operation is explicit rather than hidden behind an empty filter.

Every result has deterministic MATCH, NO_MATCH or INDETERMINATE disposition and structured reasons from domain filter evaluation. GUI text projects those reasons and never reconstructs matching. A compact funnel may show 624 nguồn → 94 khoanh vùng → 18 keyword match; it is not a dashboard and needs no charts.

## Selection method and real-source normalization

Display labels and canonical domain values are separate. Đấu thầu rộng rãi maps through the explicit existing normalization contract before filtering. Unsupported source labels remain UNKNOWN, UNSUPPORTED or NEEDS_REVIEW and cannot become matches. The 28 unsupported-source warnings observed in a real KHMT workbook remain unsupported evidence. Raw value, source type, source hash and exact observation identity remain attached to each normalized record.

## Result canvas

Default columns are opportunity/tender identifier, Tên gói, Giá, Địa bàn, Match and Review. Revision, source SHA, base_id and raw provenance are secondary Inspector/column-chooser fields. A newer revision can warn and expose a future comparison seam; it never inherits review or silently replaces an exact revision.

## Smart Inspector and Warehouse seam

Quick View shows selected identifier, package name, amount, location/deadline when available, match summary, review state and a concise TenderCase/Warehouse summary only when existing backend data supports it. Evidence, search, revision and history are progressive disclosure sections.

Reasons come from FilterEvaluation or OpportunityFilterEvaluation criteria: budget, geography, selection method, 1G1T and keyword examples are formatted projections, not GUI-created facts.

The dependency direction remains:

    GUI -> application/backend use-case facade -> domain/Warehouse services -> persistence

The Inspector may report case existence, PL context, exact IB revision and supported evidence/readiness. It must not invent seven-zone readiness, completeness percentages or direct database access.

## Review, handoff and revision

Review states remain UNREVIEWED, CONFIRMED, REJECTED and NEEDS_REVIEW. The primary action says Xác nhận cơ hội (or another approved domain-safe label), not Xác nhận thầu. Filtering never writes review events. Only the latest persisted CONFIRMED event enables the existing controlled TenderCase/workspace handoff. Absent, stale, rejected or ambiguous review remains blocked.

Handoff preserves source type, source hash, PL/IB identity, base_id and revision. Confirmation of IB...-00 does not unlock IB...-01. Revision comparison and history are extension seams; automatic inheritance, arbitrary history comparison and package completeness are out of scope.

## Derived XLSX output

XLSX remains a derived, source-backed output with:

- 00_ThongTinLoc, prominently showing “Số liệu được lọc bởi QI Crawler”, source filename/type/hash, run/filter context, operator/reviewer when applicable, timestamp, effective criteria and keyword profile/version when implemented;
- 01_DuLieuGoc_DaLoc, filtered source data close to source representation;
- 02_ThongTinPhuHop, a Team Bid-friendly summary.

Existing export validation must reject wrong source/review provenance without replacing a valid output. No A+/A/B ranking is invented without a separately approved deterministic rule.

## Diagnostics and evidence

Each operation should expose source detection/result, source row count, normalized request, parse/normalization issue counts, per-stage result counts and terminal success/failure classification without leaking sensitive document content. Acceptance evidence is classified as targeted tests, full regression, Ruff/diff and limitations; a Builder claim is not machine evidence.

## Discriminating acceptance

Future implementation tests include present-but-wrong cases:

| Contract | Wrong but plausible behavior | Required result |
| --- | --- | --- |
| Empty criteria | returns all rows as MATCH | neutral CHƯA LỌC / explicit hold |
| Money schema | parses digits in TEXT as money | remain text or reject ambiguity |
| Selection map | coerces unsupported label to a canonical match | UNKNOWN / UNSUPPORTED / NEEDS_REVIEW |
| Reason integrity | GUI invents a reason not in filter evaluation | reject mismatch |
| Review independence | match enables handoff or is labelled business GO | handoff blocked |
| Revision | -00 confirmation unlocks -01 | reject; new review required |
| GUI boundary | view reaches SQLite/DuckDB directly | architecture contract fails |
| Export provenance | wrong source hash still exports | reject; preserve existing output |
| Layout | controls overlap or clip at 125%/150% DPI | geometry acceptance fails |

## Scope boundary

Only existing Opportunity/Bid Radar application seams and focused tests named by the plan may change. No migration or new database architecture is needed. HSMT UI/deep extraction, NotebookLM, AI Assistant or Legal/Technical/Commercial AI, API evolution, autonomous agents, external connectors, MCP, schedulers, Warehouse completion, package completeness, release/publish and Team Bid pilot are out of scope.

No Product WP is activated by this design. The Workbench remains governance support, not a product runtime dependency.

## Completion gate

Implementation is reviewable only after each task has fresh RED/GREEN or a discriminating fixture, focused and relevant regressions pass, Ruff and diff check pass, and realistic acceptance covers Vietnamese numeric input, supported and unsupported selection methods, a 624-row-scale dataset, provenance-safe review/export and Windows DPI layout without GUI-to-database shortcuts or automatic business decisions.
