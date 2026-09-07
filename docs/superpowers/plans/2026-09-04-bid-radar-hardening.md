# Bid Radar Hardening Implementation Plan

> For agentic workers: execute only under approved WP-BID-RADAR-HARDENING-01. This plan is subordinate to the canonical Work Order and repository governance. Use TDD and discriminating acceptance; do not widen scope or infer authorization from a passing test.

**Goal:** Implement QI BID DESK — CALM BID RADAR as a source-neutral, explainable desktop workflow while preserving PL/IB identity, Human Review independence, Warehouse layering and derived-output provenance.

**Architecture:** Keep domain decisions in existing market-intelligence/search/review/workspace services. gui.py and any focused view component render state and dispatch through gui_services.py; they never query persistence directly. Extend existing contracts minimally and avoid a whole-GUI refactor.

**Baseline:** feat/bid-radar-hardening-01 starts at 0fbf50bc25e85ff58f8f53214a30f1c4708bea0a.

**Tech stack:** Existing Python, PySide6, SQLAlchemy/Tender Workspace services, openpyxl, pytest and Ruff.

**Design:** docs/superpowers/specs/2026-09-04-bid-radar-calm-desk-design.md.

## Global constraints

- No Alembic migration or new schema. No Workbench, HSMT, AI/NotebookLM, API, automation, MCP, connector, release or Team Bid pilot work.
- PL != IB; (base_id, revision) is exact identity; no automatic review inheritance.
- FILTER MATCH != HUMAN CONFIRMED != BUSINESS GO.
- GUI -> application facade -> domain/Warehouse -> persistence; never GUI -> SQLite/DuckDB.
- Every task has real RED or a present-but-wrong fixture, minimal GREEN and relevant regression. Positive-only acceptance is insufficient.
- Pre-existing Workbench patches/README remain protected and are not absorbed.
- Impact radius is not edit authority; inspect callers with CodeGraph/manual evidence before selecting the smallest edit radius.

## Existing impact map

| Capability | Existing implementation seam | Existing tests |
| --- | --- | --- |
| source-neutral filtering | src/qi_crawler/market_intelligence/search.py, filter_engine.py, khmt_normalization.py, khmt_importer.py | tests/test_opportunity_filter_search.py, tests/test_khmt_filter_engine.py, tests/test_khmt_normalization_location.py, tests/test_khmt_search.py |
| Bid Radar facade | src/qi_crawler/gui_services.py, opportunity_intelligence.py, opportunity_radar.py | tests/test_bid_radar_gui_services.py, tests/test_opportunity_intelligence.py, tests/test_opportunity_radar.py |
| desktop presentation | src/qi_crawler/gui.py; focused src/qi_crawler/bid_radar_view.py only if justified | tests/test_bid_radar_gui.py, tests/test_gui.py |
| review/handoff | candidate_review.py, opportunity_review.py, opportunity_review_persistence.py, opportunity_workspace_handoff.py | tests/test_candidate_review.py, tests/test_opportunity_review.py, tests/test_opportunity_workspace_handoff.py |
| derived export | market_intelligence/confirmed_opportunity_export.py, confirmed_package_export.py, export/tbmt_excel.py, tbmt_formatter.py, tbmt_mapper.py, tbmt_schema.py, tbmt_validator.py | tests/test_confirmed_opportunity_export.py, tests/test_confirmed_package_export.py, tests/test_tbmt_export.py |
| TenderCase/Warehouse context | tender_workspace.py, tender_case_service.py, tender_case_persistence.py, warehouse.py | tests/test_tender_workspace.py, tests/test_tender_workspace_gui_services.py, tests/test_tender_workspace_ops.py, tests/test_tender_case_service.py, tests/test_warehouse.py |

## MICRO-A1 — FILTER / INPUT CONTRACT SAFETY

**Purpose:** Make Vietnamese money input schema-driven without changing source identity or filter authority.

**Files:** Modify src/qi_crawler/market_intelligence/khmt_normalization.py, khmt_importer.py and search.py only where current contracts need a normalized value. Test tests/test_khmt_normalization_location.py, tests/test_opportunity_filter_search.py and tests/test_khmt_importer.py.

**Interfaces:** TargetedSearchRequest; normalized package/opportunity fields; field-schema-aware result containing raw value, normalized value, parse status and field/provenance context.

**Failing test:** Accept 1.000.000.000, 1 000 000 000, 1,000,000,000 and 1000000000 in MONEY; reject ambiguous forms; digits in TEXT remain text. A global punctuation heuristic is the wrong counterexample.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_khmt_normalization_location.py tests/test_opportunity_filter_search.py -q.

**Minimal implementation direction:** Reuse parse_package_price and existing normalization; make field schema explicit, preserve raw input and return non-match/needs-review for ambiguity.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_khmt_normalization_location.py tests/test_opportunity_filter_search.py tests/test_khmt_importer.py -q.

**Relevant regression:** tests/test_khmt_contract.py, tests/test_opportunity_contract.py and tests/test_khmt_search.py.

**Commit boundary:** One A1 implementation/test commit only; no UI or database change.

## MICRO-A2 — SELECTION METHOD + REAL-SOURCE NORMALIZATION

**Purpose:** Separate display labels from canonical selection-method values and keep unsupported real-source values fail-safe.

**Files:** Modify src/qi_crawler/market_intelligence/khmt_normalization.py, khmt_importer.py and source_detection.py only as existing source contracts require. Test tests/test_khmt_normalization_location.py, tests/test_khmt_importer.py, tests/test_source_detection.py and tests/test_khmt_filter_engine.py.

**Interfaces:** normalize_selection_method, selection_method_raw/canonical value, source-review status and FilterProfile.selection_methods.

**Failing test:** Supported Đấu thầu rộng rãi maps to canonical value; an unsupported label and a representative real warning remain UNKNOWN/UNSUPPORTED/NEEDS_REVIEW and cannot match.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_khmt_normalization_location.py tests/test_khmt_filter_engine.py -q.

**Minimal implementation direction:** Extend the explicit table, preserve raw text and never compare arbitrary display labels in GUI or coerce unsupported values.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_khmt_normalization_location.py tests/test_khmt_filter_engine.py tests/test_khmt_importer.py -q.

**Relevant regression:** tests/test_khmt_contract.py, tests/test_khmt_search.py and tests/test_opportunity_filter_search.py.

**Commit boundary:** One A2 implementation/test commit; preserve A1 behavior.

## MICRO-A3 — NO-CRITERIA DECISION SAFETY

**Purpose:** Replace unsafe empty-criteria match-all semantics with neutral CHƯA LỌC while preserving any explicit full-listing contract.

**Files:** Modify src/qi_crawler/market_intelligence/search.py, filter_engine.py and the smallest required caller in opportunity_intelligence.py. Test tests/test_opportunity_filter_search.py, tests/test_khmt_search.py and tests/test_khmt_filter_engine.py.

**Interfaces:** TargetedSearchRequest, TargetedOpportunitySearchResult, OpportunityFilterDisposition and NO_ACTIVE_CRITERIA/CHƯA LỌC state.

**Failing test:** Empty request must not return all rows as MATCH; explicit criteria continue to match and explicit listing remains intentional.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_opportunity_filter_search.py tests/test_khmt_search.py -q.

**Minimal implementation direction:** Guard the empty request at the domain seam, retain evaluated rows for diagnostics and make GUI consume neutral state without matching logic.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_opportunity_filter_search.py tests/test_khmt_search.py tests/test_khmt_filter_engine.py -q.

**Relevant regression:** tests/test_opportunity_intelligence.py and tests/test_bid_radar_gui_services.py.

**Commit boundary:** One A3 implementation/test commit; no widget edits.

## MICRO-A4 — FILTER RESULT / MATCH REASON CONTRACT

**Purpose:** Expose deterministic criteria/reason evidence to the Inspector without duplicated GUI business logic.

**Files:** Modify src/qi_crawler/market_intelligence/filter_engine.py, search.py and gui_services.py. Test tests/test_khmt_filter_engine.py, tests/test_opportunity_filter_search.py and tests/test_bid_radar_gui_services.py.

**Interfaces:** CriterionEvaluation, OpportunityFilterEvaluation, BidRadarRow, BidRadarResult and run_bid_radar_import_search.

**Failing test:** Matched rows expose budget/geography/selection/1G1T/keyword reasons; GUI-fabricated reason is rejected; INDETERMINATE is distinct from MATCH.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_khmt_filter_engine.py tests/test_bid_radar_gui_services.py -q.

**Minimal implementation direction:** Project existing criterion reason codes through the service DTO, preserving source/provenance and review state.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_khmt_filter_engine.py tests/test_bid_radar_gui_services.py tests/test_opportunity_intelligence.py -q.

**Relevant regression:** A1–A3 tests and tests/test_opportunity_radar.py.

**Commit boundary:** One A4 backend/facade/test commit.

## MICRO-A5 — CALM BID DESK UI SHELL

**Purpose:** Materialize Selection Desk, Active Tender Canvas and Smart Inspector with cognitive-safe layout.

**Files:** Modify src/qi_crawler/gui.py and gui_services.py only for thin wiring; create src/qi_crawler/bid_radar_view.py only if current gui.py structure proves it necessary. Test tests/test_bid_radar_gui.py, tests/test_gui.py and tests/test_bid_radar_gui_services.py.

**Interfaces:** Existing Bid Radar window/actions, run_bid_radar_import_search, BidRadarResult, selection state and three-region widget contract.

**Failing test:** Calm summary/chips/funnel and Quick View exist; side panels collapse independently; flexible layout has no clipping/overlap/horizontal overflow; primary action is unambiguous.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_bid_radar_gui.py tests/test_gui.py -q.

**Minimal implementation direction:** Use bounded splitters/layouts/scroll areas, hide advanced controls behind Filter Studio/Inspector disclosure and retain service delegation. Do not refactor whole GUI.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_bid_radar_gui.py tests/test_gui.py tests/test_bid_radar_gui_services.py -q.

**Relevant regression:** tests/test_gui_services.py and A4 tests; DPI/layout matrix is completed in A9.

**Commit boundary:** One focused UI-shell/test commit; no domain or persistence changes.

## MICRO-A6 — REVIEW + CONTROLLED HANDOFF

**Purpose:** Preserve independent Human Review and enable handoff only for latest persisted confirmation.

**Files:** Modify src/qi_crawler/market_intelligence/candidate_review.py, opportunity_review.py, opportunity_review_persistence.py, opportunity_workspace_handoff.py and gui_services.py only for labels/enablement. Test tests/test_candidate_review.py, tests/test_opportunity_review.py, tests/test_opportunity_workspace_handoff.py and tests/test_bid_radar_gui.py.

**Interfaces:** HumanReviewDecision, OpportunityReviewDecision, run_bid_radar_review, run_bid_radar_workspace_handoff and exact identity/provenance event lookup.

**Failing test:** Match alone creates no review event and cannot hand off; CONFIRMED enables only the governed facade; IB...-00 cannot hand off IB...-01; unsafe Xác nhận thầu label is rejected.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_candidate_review.py tests/test_opportunity_review.py tests/test_opportunity_workspace_handoff.py tests/test_bid_radar_gui.py -q.

**Minimal implementation direction:** Keep append-only persistence/current-event authority, use Xác nhận cơ hội and preserve existing error paths for absent/stale/unsupported identities.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_candidate_review.py tests/test_opportunity_review.py tests/test_opportunity_workspace_handoff.py tests/test_bid_radar_gui.py -q.

**Relevant regression:** tests/test_bid_radar_gui_services.py and tests/test_opportunity_delivery_acceptance.py.

**Commit boundary:** One review/handoff/test commit; no automatic business decision.

## MICRO-A7 — XLSX DERIVED OUTPUT

**Purpose:** Produce three source-backed sheets with provenance and a Team Bid summary without invented ranking.

**Files:** Modify src/qi_crawler/market_intelligence/confirmed_opportunity_export.py, confirmed_package_export.py and existing src/qi_crawler/export/tbmt_excel.py, tbmt_formatter.py, tbmt_mapper.py, tbmt_schema.py, tbmt_validator.py only where contracts require. Test tests/test_confirmed_opportunity_export.py, tests/test_confirmed_package_export.py and tests/test_tbmt_export.py.

**Interfaces:** Confirmed-review export facade, source hash/type/provenance, sheet names and controlled output path.

**Failing test:** Workbook contains 00_ThongTinLoc, 01_DuLieuGoc_DaLoc and 02_ThongTinPhuHop; required “Số liệu được lọc bởi QI Crawler” and source SHA are present; wrong provenance rejects without overwriting a valid output.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_confirmed_opportunity_export.py tests/test_confirmed_package_export.py tests/test_tbmt_export.py -q.

**Minimal implementation direction:** Extend current openpyxl mappers/validators, preserve source rows, derive summary from confirmed observations and do not add A+/A/B ranking.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_confirmed_opportunity_export.py tests/test_confirmed_package_export.py tests/test_tbmt_export.py -q.

**Relevant regression:** tests/test_active_source_filter.py and tests/test_opportunity_delivery_acceptance.py.

**Commit boundary:** One derived-output/test commit; no release artifact.

## MICRO-A8 — WAREHOUSE INSPECTOR BRIDGE

**Purpose:** Surface existing TenderCase/Warehouse context through the backend seam while keeping GUI storage-blind.

**Files:** Modify src/qi_crawler/gui_services.py, tender_workspace.py, tender_case_service.py, tender_case_persistence.py and warehouse.py only as needed. Test tests/test_tender_workspace.py, tests/test_tender_workspace_gui_services.py, tests/test_tender_workspace_ops.py, tests/test_tender_case_service.py, tests/test_warehouse.py and tests/test_opportunity_workspace_handoff.py.

**Interfaces:** TenderWorkspaceService, TenderCaseService, WorkspaceEntry, OpportunityWorkspaceHandoffService and Inspector DTOs.

**Failing test:** Inspector reports case/exact revision through facade; direct GUI DB access or invented seven-zone completeness fails; handoff preserves identity.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_tender_workspace_gui_services.py tests/test_tender_workspace.py tests/test_opportunity_workspace_handoff.py -q.

**Minimal implementation direction:** Reuse current workspace search/handoff, add only persistence-proven read summaries, keep DB operations below the facade.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_tender_workspace_gui_services.py tests/test_tender_workspace.py tests/test_tender_workspace_ops.py tests/test_opportunity_workspace_handoff.py -q.

**Relevant regression:** tests/test_tender_case_persistence.py, tests/test_warehouse.py and A5/A6 tests.

**Commit boundary:** One Inspector bridge/test commit; no schema/migration.

## MICRO-A9 — REALISTIC ACCEPTANCE / WINDOWS REGRESSION

**Purpose:** Prove the integrated desk at realistic scale and Windows DPI without promoting evidence gaps into product claims.

**Files:** Modify only the smallest integrated Bid Radar view/facade files proven necessary by A1–A8. Add deterministic non-confidential fixture tests/fixtures/bid_radar/khmt_624_rows.xlsx if absent. Test tests/test_bid_radar_gui.py, tests/test_bid_radar_gui_services.py, tests/test_opportunity_delivery_acceptance.py, tests/test_gui.py and, if required, tests/test_bid_radar_realistic_acceptance.py.

**Interfaces:** Source import/search -> chips/funnel/grid -> Inspector reasons -> Human Review -> controlled handoff/export; diagnostics and isolated test data root.

**Failing test:** A 624-row fixture with Vietnamese numeric values, supported/unsupported methods, empty criteria, review isolation, provenance-safe export and 100/125/150% DPI geometry exposes false match, false confirmation, clipping or missing diagnostics.

**RED command:** .venv\Scripts\python.exe -m pytest tests/test_bid_radar_realistic_acceptance.py tests/test_bid_radar_gui.py tests/test_bid_radar_gui_services.py -q.

**Minimal implementation direction:** Keep fixture/data isolated from production DB, capture source count, normalized request, issue counts, result counts and terminal status, and fix only within A1–A8 radius.

**GREEN command:** .venv\Scripts\python.exe -m pytest tests/test_bid_radar_realistic_acceptance.py tests/test_bid_radar_gui.py tests/test_bid_radar_gui_services.py tests/test_opportunity_delivery_acceptance.py -q.

**Relevant regression:** full .venv\Scripts\python.exe -m pytest, Ruff and diff check; hosted Windows CI is required before integration review.

**Commit boundary:** One final acceptance commit after A1–A8 review; no merge, release or Team Bid pilot.

## Verification and review order

After each task inspect exact diff, run its GREEN and relevant regressions, then Ruff and diff check before a semantic commit. At the end run focused Bid Radar tests, full pytest, Ruff and diff check and preserve exact BASE/HEAD/evidence for an independent Reviewer. Reviewer receives the candidate and evidence but never edits the audited output.

## Out-of-scope confirmation

HSMT UI/deep extraction, API, AI/NotebookLM, autonomous behavior, MCP/scheduler/connectors, new database architecture, package completeness, release/publish and Team Bid pilot remain out of scope. FILTER MATCH, CONFIRMED and business workflow remain separate states.

## Next authority

After this planning Micro is locally committed and verified, stop for PLANNER_ARCHITECT review before MICRO-A1 — FILTER / INPUT CONTRACT SAFETY.
