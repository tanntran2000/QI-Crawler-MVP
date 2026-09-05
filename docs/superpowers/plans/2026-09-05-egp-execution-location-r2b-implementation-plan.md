# Controlled e-GP Execution Location Enrichment — R2B Implementation Plan

> REQUIRED SUB-SKILL: superpowers:executing-plans. Execute this plan from the canonical checkout as one Builder single-writer sequence, stopping at every governance checkpoint.
>
> The repository law is Human A0 approval → Planner Work Order → Builder single writer → machine evidence → Planner audit → independent Reviewer audit when requested → Human decision. This plan never grants authority to merge, release, change the Spine automatically, or begin a later milestone.

## Goal

Add a bounded, source-backed enrichment path that lets Bid Radar display and filter execution location for TBMT without mutating the imported workbook observation, source fields, raw fields, location_detail_raw, provenance, or database schema. The path must be explicit Human action, browser-native, rate-limited, fail-closed, cancellable, restart-safe, and useful only when the official response provides meaningful evidence.

The R2B MVP filter authority is province/city only. A response containing only district or ward remains visible as PARTIAL evidence and cannot be promoted into a province/city filter value. Missing, malformed, blocked, stale, or identity-ambiguous evidence is UNKNOWN or rejected and never silently becomes NO_MATCH.

## Architecture

The existing local workbook import remains the immutable source observation. A new execution-location evidence layer stores sanitized response evidence keyed by source type, base identifier, and exact revision. An effective projection joins that evidence to an OpportunityRadarItem in memory; it is the sole input shared by the Bid Radar location dropdown and filter engine, while the original item and workbook provenance remain unchanged.

Network acquisition is an application service behind the existing BrowserFetcher and AccessPolicy. The GUI only starts, observes, cancels, and applies a bounded batch after explicit Human action. The service never extracts tokens, exports cookies, replays private requests, bypasses CAPTCHA, or treats an observed UUID as a caller-supplied prerequisite.

## Tech Stack

Python, PySide6, Playwright, existing QI application/domain services, filesystem evidence cache, pytest.

## Approved specification

The governing design is:

    docs/superpowers/specs/2026-09-05-egp-execution-location-r2b-design.md

The specification is Human-approved final design. Its M0 real-response proof remains a hard gate before any implementation milestone M1–M6 can execute.

## Global Constraints

- Work only in D:\QI Technology\QI Crawler\egp-crawler-python on the canonical branch selected by the Planner.
- Use one Builder writer, one checkout, no worktrees, no parallel writers, and no subagent-driven parallel implementation. The superpowers:executing-plans skill is the execution protocol.
- Do not start M0, M1, M2, M3, M4, M5, or M6 until the preceding authority checkpoint explicitly authorizes that milestone.
- Do not make an e-GP request during documentation planning. M0 is the first and only network-capable milestone, and it uses the normal official frontend browser session.
- Do not add database tables, Alembic migrations, API endpoints, scheduler jobs, daemon behavior, MCP, external connectors, auto-Spine, auto-merge, or auto-release.
- Do not modify KHMT import, KHMT province/city normalization, Generic Find semantics, existing workbook source bytes, or existing source provenance.
- Do not infer a province/city from package name, project name, procuring entity, procuring address, issue address, or any unrelated text.
- Do not use token extraction, token export, request replay, CAPTCHA solvers, proxy rotation, fingerprint spoofing, private credentials, hidden browser storage, or aggressive retries.
- A CAPTCHA, access-control challenge, robots uncertainty, HTTP identity mismatch, malformed response, or missing direct province/city value stops the current batch and records a governed evidence gap.
- The existing source integrity guard must remain authoritative. Workbook SHA-256 and provenance are rechecked before applying a batch; a changed source makes the batch stale and ineligible for projection.
- LOCK, machine verification, cache integrity, and Reviewer PASS never equal Human approval or merge authority.
- Every implementation task has separate IMPACT_RADIUS, EDIT_RADIUS, and TEST_RADIUS. No radius may be silently widened.
- Every implementation task begins with a discriminating RED test or acceptance check before production code is edited. A pre-existing passing test is repaired or replaced before implementation continues.
- No commit may include a file outside the task's exact authorized path set. Do not use git add . or git add -A.
- No task may claim completion from a test name or static string alone; evidence must include the actual command, exit status, and observed result.

## Authority and execution model

Human A0 approved the R2B design and MVP filter level. The next authority is Planner Architect for this implementation plan. After Planner audit, Human decides whether M0 may run. M0 then stops for evidence audit and Human decision. M1 through M6 are conditional milestones; each stops after its machine evidence for Planner review and an independent Reviewer audit when requested. There is no automatic transition from M0 to M1 or from any milestone to the next.

The Builder may use the existing executing-plans protocol, but generic multi-agent defaults are overridden here: one canonical checkout, one writer, no parallel branches, no automatic delegation, and no hidden continuation after a checkpoint.

## Planned File Structure

The following paths are the complete planned implementation surface. A path is created only in the milestone that owns it; static inspection does not grant ownership.

    docs/agent_handoff/evidence/R2B-M0-egp-location-response.md
        Sanitized, durable M0 proof containing response route, response hash, identity binding, DTO path, semantic province/city value, and limitations. Raw responses remain in a temporary directory outside the repository.

    src/qi_crawler/market_intelligence/execution_location.py
        Immutable evidence types, parser result, quality/status enums, the ExecutionLocationEvidenceIndex, and EffectiveOpportunityProjection.

    src/qi_crawler/market_intelligence/execution_location_cache.py
        Filesystem cache records, key construction, schema/version checks, SHA validation, atomic writes, and corrupt-entry rejection.

    src/qi_crawler/market_intelligence/egp_detail_provider.py
        Browser-native e-GP identity resolution and detail-response observation using BrowserFetcher and AccessPolicy.

    src/qi_crawler/market_intelligence/execution_location_service.py
        Sequential cancellable batch enrichment, stale-source guards, progress events, and terminal result statuses.

    src/qi_crawler/market_intelligence/filter_engine.py
        A projection-aware TBMT execution-location criterion while preserving Generic Find and KHMT behavior.

    src/qi_crawler/market_intelligence/opportunity_radar.py
        A non-mutating effective projection adapter for existing radar items.

    src/qi_crawler/market_intelligence/opportunity_intelligence.py
        Application façade wiring for an explicit enrichment batch without moving network logic into GUI code.

    src/qi_crawler/gui_services.py
        Thin task and result adapters for starting, cancelling, and applying one enrichment batch.

    src/qi_crawler/gui.py
        Human action, progress, DỪNG action, terminal apply-once behavior, dropdown rebuild, and selection preservation.

    tests/test_execution_location.py
        Pure precedence, quality, province/city gate, multi-location, malformed-response, and non-inference contracts.

    tests/test_execution_location_cache.py
        Key, identity, source hash, corruption, atomic replace, and secret-exclusion contracts.

    tests/test_egp_detail_provider.py
        Browser policy, exact identity binding, timeout, concurrency, challenge, cancellation, and response-envelope contracts using fakes.

    tests/test_execution_location_service.py
        Batch statuses, stale generation rejection, progress, cancellation, and cache/application boundary contracts.

    tests/test_opportunity_filter_search.py
        Existing filter regression additions for effective projection, UNKNOWN semantics, Generic Find, and KHMT invariants.

    tests/test_bid_radar_gui.py
        Existing GUI regression additions for the Human enrichment action, progress/stop, confirmed-only dropdown, partial Inspector evidence, and valid-selection preservation.

    tests/test_bid_radar_gui_services.py
        Existing service adapter regression additions for source-session and batch-result identity.

    tests/test_opportunity_intelligence.py
        Existing façade regression additions proving the workbook observation and provenance remain unchanged.

    tests/test_tbmt_importer.py
        Existing importer regressions proving explicit workbook fields remain the highest precedence and are never overwritten by enrichment.

The following existing files are inspection-only unless a milestone below explicitly names them: src/qi_crawler/browser.py, src/qi_crawler/compliance.py, src/qi_crawler/config.py, src/qi_crawler/market_intelligence/search.py, src/qi_crawler/market_intelligence/tbmt_importer.py, src/qi_crawler/market_intelligence/source_integrity.py, src/qi_crawler/market_intelligence/source_session.py, and src/qi_crawler/market_intelligence/location_resolver.py. The existing location_resolver is not reused for TBMT enrichment because its historical MI-1 mappings can infer from unrelated fields.

## Static inspection before M0

Before any implementation or network action, inspect the current definitions and callers of:

- BrowserFetcher.start, new_page, fetch_html, fetch_authenticated_html, close, and the existing page lifecycle.
- AccessPolicy.validate_domain, require_robots_access, detect_block_page, and DomainRateLimiter.wait.
- AppConfig, CrawlConfig, StorageConfig, and the existing raw/report directories.
- OpportunitySourceType, OpportunityIdentity, OpportunityCandidate, OpportunityRadarItem, and observation_key.
- FilterProfile, CriterionEvidence, CriterionEvaluation, OpportunityFilterEvaluation, execution_location_values, evaluate_opportunity, and evaluate_plan_package.
- TargetedSearchRequest and search_opportunities.
- OpportunityIntelligenceService load/import/search façades.
- TBMT importer explicit-field precedence and SHA capture.
- BidRadarRow, BidRadarResult, GuiTaskBridge, FunctionWorker, and the existing source-session reset/dropdown code.
- source_integrity.py and all existing raw/evidence persistence utilities before adding the cache.
- Relevant tests named in Planned File Structure.

The inspection output is a plan checkpoint only. It must not add a network call or edit a source file.

## M0 — real browser-response proof

CONDITIONAL TASK: DO NOT EXECUTE unless Human A0 authorizes M0 after Planner audits this plan.

### M0 objective

Use the official public e-GP frontend in a normal Playwright browser session to observe one to three real detail responses for the exact real source and revision selected by the Planner. The run is bounded at one browser context, one detail acquisition at a time, the configured 12 requests per minute, and the existing browser timeout. No direct tokenless API replay is allowed.

### M0 procedure

1. Confirm the exact source identity, base identifier, revision, and approved official URL in the Planner Work Order.
2. Start BrowserFetcher with the current AppConfig and AccessPolicy. Validate domain and robots policy before navigation.
3. Navigate through the official frontend detail flow. Observe network responses emitted by the page; do not manufacture an endpoint or payload.
4. Save raw response bytes only under a unique temporary directory outside the repository. Record SHA-256, status, content type, observed route, and capture time.
5. Bind the response to the requested identity using the response's own notify number, base identifier, revision marker, and observed UUID relation. Ambiguity is a hold.
6. Locate the exact detail object path and location DTO path in the observed response. Record the path as a JSON-pointer-like sequence in the sanitized report.
7. Record at least one semantic location value that is directly a province/city. District/ward-only output does not satisfy the gate.
8. Write only the sanitized report to docs/agent_handoff/evidence/R2B-M0-egp-location-response.md after the Human-authorized M0 run. Never write cookies, storage state, authorization headers, tokens, or private account data.

### M0 proof contract

The report must contain exact observed values for REAL_RESPONSE_ENVELOPE, REAL_DETAIL_OBJECT_PATH, REAL_IDENTITY_BINDING, REAL_NOTIFYNO_REVISION_UUID_RELATION, REAL_LOCATION_DTO_PATH, REAL_SEMANTIC_LOCATION_VALUE, and M0_REAL_PROVINCE_CITY_VALUE. It must identify the source base/revision and response SHA-256 without storing secrets.

### M0 stop/decision contract

    M0_REAL_PROVINCE_CITY_VALUE = PROVEN
    M0_IDENTITY_BINDING = PASS
    M0_DETAIL_OBJECT_PATH = PROVEN
    M0_LOCATION_DTO_PATH = PROVEN
    M0_ACCESS_POLICY = PASS
    M0_RAW_SECRET_EXCLUSION = PASS

Any missing direct province/city, identity mismatch, malformed envelope, HTTP challenge, CAPTCHA, robots uncertainty, or access-control interruption sets M0_PROVINCE_GATE = FAIL or M0_ACCESS = HOLD and stops the batch. Do not bypass the challenge. The mandatory next sequence is M0 evidence → Planner audit → Human decision; M0 never auto-authorizes M1–M6.

### M0 radius and evidence

    IMPACT_RADIUS = BrowserFetcher, AccessPolicy, e-GP frontend response envelope, identity binding, location DTO, evidence report path.
    EDIT_RADIUS = temporary raw response files plus the single sanitized M0 report after explicit authorization.
    TEST_RADIUS = temporary parser/response inspection helpers and no production test changes.

Commit after accepted evidence, if Planner authorizes durable evidence: docs(evidence): record R2B M0 browser proof.

## M1 — structured execution-location contract and pure parser

CONDITIONAL TASK: DO NOT EXECUTE unless M0 passed and Planner/Human authorize M1.

### M1 exact interfaces

In src/qi_crawler/market_intelligence/execution_location.py define:

    class ExecutionLocationQuality(StrEnum):
        CONFIRMED = "CONFIRMED"
        PARTIAL = "PARTIAL"
        UNKNOWN = "UNKNOWN"

    @dataclass(frozen=True, slots=True)
    class ExecutionLocationEvidence:
        identity: OpportunityIdentity
        values: tuple[str, ...]
        province_city_values: tuple[str, ...]
        district_values: tuple[str, ...]
        ward_values: tuple[str, ...]
        quality: ExecutionLocationQuality
        source_path: str
        response_sha256: str
        observed_at: datetime

    @dataclass(frozen=True, slots=True)
    class ExecutionLocationParseResult:
        evidence: ExecutionLocationEvidence | None
        rejected: bool
        reason: str | None

    def parse_execution_location_payload(
        payload: Mapping[str, Any],
        *,
        identity: OpportunityIdentity,
        detail_object_path: str,
        response_sha256: str,
        observed_at: datetime,
    ) -> ExecutionLocationParseResult

    class ExecutionLocationEvidenceIndex:
        @classmethod
        def from_records(
            cls, records: Iterable[ExecutionLocationEvidence]
        ) -> ExecutionLocationEvidenceIndex
        def for_identity(
            self, identity: OpportunityIdentity
        ) -> tuple[ExecutionLocationEvidence, ...]

    @dataclass(frozen=True, slots=True)
    class EffectiveOpportunityProjection:
        item: OpportunityRadarItem
        execution_locations: tuple[str, ...]
        confirmed_province_city: tuple[str, ...]
        quality: ExecutionLocationQuality
        source_fingerprint: str

    def project_effective_opportunity(
        item: OpportunityRadarItem,
        evidence_index: ExecutionLocationEvidenceIndex,
    ) -> EffectiveOpportunityProjection

The parser accepts structured detail only at the M0-proven object path. It emits CONFIRMED only for meaningful province/city values, PARTIAL for meaningful district/ward without a province/city, and UNKNOWN for absent location or unusable evidence. Malformed content is rejected with an explicit reason and is not relabeled as source-no-location.

Projection precedence is explicit workbook execution fields, then confirmed M0-backed province/city evidence, then PARTIAL detail evidence for display only, then UNKNOWN. The projection is immutable and never writes into item.source_fields, item.raw_fields, item.location_detail_raw, or workbook provenance.

### M1 TDD and verification

RED command:

    .venv\Scripts\python.exe -m pytest tests/test_execution_location.py -q

Expected RED is missing execution_location types/parser or the old implementation returning no structured evidence. The red assertion must distinguish a missing parser contract from an unrelated import failure.

Minimum implementation is the immutable types, M0-path parser, explicit workbook precedence adapter, province/city gate, and multi-location normalization without administrative inference.

GREEN commands:

    .venv\Scripts\python.exe -m pytest tests/test_execution_location.py -q
    .venv\Scripts\python.exe -m pytest tests/test_tbmt_importer.py tests/test_opportunity_filter_search.py -q
    .venv\Scripts\python.exe -m ruff check src/qi_crawler/market_intelligence/execution_location.py tests/test_execution_location.py
    git diff --check

The test matrix must include HCM-only pass, HCM-only versus Đồng Nai fail, HCM plus Đồng Nai matching either value, missing UNKNOWN, procuring-address HCM with execution Đồng Nai fail, issue-location HCM with execution Đồng Nai fail, explicit workbook value outranking detail, malformed response rejection, and unchanged KHMT behavior.

    IMPACT_RADIUS = TBMT projection, filter_engine execution criterion, existing radar item contract.
    EDIT_RADIUS = execution_location.py, filter_engine.py only at the projection seam, and tests/test_execution_location.py plus named existing regression tests.
    TEST_RADIUS = pure parser, projection, filter, Generic Find, and KHMT regression tests.

Commit: feat(location): add structured execution evidence contract.

## M2 — filesystem evidence cache

CONDITIONAL TASK: DO NOT EXECUTE unless M1 evidence is accepted by Planner and Human authorizes M2.

### M2 exact interfaces

In src/qi_crawler/market_intelligence/execution_location_cache.py define:

    @dataclass(frozen=True, slots=True)
    class ExecutionLocationCacheRecord:
        source_type: OpportunitySourceType
        base_id: str
        revision: str
        notify_id: str
        source_sha256: str
        response_sha256: str
        parser_contract_version: str
        observed_at: datetime
        evidence: ExecutionLocationEvidence

    class ExecutionLocationCache:
        def __init__(
            self,
            root: Path,
            *,
            parser_contract_version: str,
            raw_schema_version: str,
        ) -> None
        def get(
            self,
            source_type: OpportunitySourceType,
            base_id: str,
            revision: str,
        ) -> ExecutionLocationCacheRecord | None
        def put(self, record: ExecutionLocationCacheRecord) -> None
        def invalidate(
            self,
            source_type: OpportunitySourceType,
            base_id: str,
            revision: str,
        ) -> None

The on-disk key is source_type + base_id + revision. Each record contains the notify identifier, source SHA, response SHA, parser contract version, evidence path, and sanitized evidence only. Corrupt JSON, wrong schema, wrong identity, wrong source SHA, or malformed evidence is rejected and never returned as a usable record. Writes use a temporary sibling file, flush/close, and atomic replace. Cookies, tokens, authorization headers, browser storage, and raw private response secrets are not cache fields.

### M2 TDD and verification

RED command:

    .venv\Scripts\python.exe -m pytest tests/test_execution_location_cache.py -q

Expected RED is the absence of the cache contract or failure to reject a wrong source/revision identity.

Minimum implementation covers exact key construction, read identity/hash/parser/schema checks, temporary write plus atomic replace, corrupt-entry rejection, and no secret material.

GREEN commands:

    .venv\Scripts\python.exe -m pytest tests/test_execution_location_cache.py -q
    .venv\Scripts\python.exe -m pytest tests/test_source_integrity_hardening.py tests/test_opportunity_intelligence.py -q
    .venv\Scripts\python.exe -m ruff check src/qi_crawler/market_intelligence/execution_location_cache.py tests/test_execution_location_cache.py
    git diff --check

The tests must prove cache hit, source identity mismatch, revision mismatch, raw/source modification invalidation, malformed record rejection, atomic replacement, and absence of secrets.

    IMPACT_RADIUS = SourceIntegrityProof, filesystem evidence root, restart/reopen semantics, stale-source handling.
    EDIT_RADIUS = execution_location_cache.py and its focused tests.
    TEST_RADIUS = cache key, integrity, corruption, atomicity, and secret-exclusion tests.

Commit: feat(location): add integrity-checked execution evidence cache.

## M3 — browser-native detail provider

CONDITIONAL TASK: DO NOT EXECUTE unless M2 evidence is accepted and Planner/Human authorize M3.

### M3 exact interfaces

In src/qi_crawler/market_intelligence/egp_detail_provider.py define:

    @dataclass(frozen=True, slots=True)
    class ResolvedEGPIdentity:
        identity: OpportunityIdentity
        notify_id: str
        revision_uuid: str
        detail_url: str

    @dataclass(frozen=True, slots=True)
    class ObservedDetailResponse:
        resolved: ResolvedEGPIdentity
        response_url: str
        status_code: int
        content_type: str
        body: bytes
        response_sha256: str
        detail_object_path: str
        observed_at: datetime

    class EGPBrowserDetailProvider:
        def __init__(self, fetcher: BrowserFetcher, *, acquisition_budget: int = 1) -> None
        async def resolve_revision(
            self, identity: OpportunityIdentity
        ) -> ResolvedEGPIdentity
        async def fetch_detail(
            self, resolved: ResolvedEGPIdentity
        ) -> ObservedDetailResponse

The provider navigates the official frontend with BrowserFetcher, uses AccessPolicy and DomainRateLimiter, allows only one in-flight detail acquisition, and binds the observed response to the requested base/revision/notify identity. The UUID is recorded as observed metadata; the caller does not need to discover or supply it before navigation. A finite timeout, cancellation signal, challenge detection, HTTP mismatch, and response-envelope mismatch all return governed failure statuses. No provider method exports or persists browser credentials.

### M3 TDD and verification

RED command:

    .venv\Scripts\python.exe -m pytest tests/test_egp_detail_provider.py -q

Expected RED is the missing provider contract or a fake response being accepted without identity binding.

Minimum implementation wraps the existing BrowserFetcher lifecycle, captures only the M0-approved response, enforces the acquisition budget and concurrency 1, and stops on challenge/cancel/identity mismatch.

GREEN commands:

    .venv\Scripts\python.exe -m pytest tests/test_egp_detail_provider.py -q
    .venv\Scripts\python.exe -m pytest tests/test_authenticated_sources.py tests/test_source_pipeline.py -q
    .venv\Scripts\python.exe -m ruff check src/qi_crawler/market_intelligence/egp_detail_provider.py tests/test_egp_detail_provider.py
    git diff --check

The tests must distinguish exact identity binding, timeout, one-at-a-time concurrency, 12-per-minute budget configuration, CAPTCHA/access denial, cancellation, malformed response, and no token/replay behavior.

    IMPACT_RADIUS = BrowserFetcher, AccessPolicy, compliance markers, official e-GP frontend response path.
    EDIT_RADIUS = egp_detail_provider.py and its focused tests; browser.py is unchanged unless a Planner-approved proven seam defect exists.
    TEST_RADIUS = provider fakes and existing compliance/browser regressions.

Commit: feat(location): add bounded browser-native e-GP detail provider.

## M4 — batch service and effective projection

CONDITIONAL TASK: DO NOT EXECUTE unless M3 evidence is accepted and Planner/Human authorize M4.

### M4 exact interfaces

In src/qi_crawler/market_intelligence/execution_location_service.py define:

    class EnrichmentItemStatus(StrEnum):
        CONFIRMED = "CONFIRMED"
        PARTIAL = "PARTIAL"
        UNKNOWN = "UNKNOWN"
        CHALLENGE = "CHALLENGE"
        STALE = "STALE"
        CANCELLED = "CANCELLED"
        REJECTED = "REJECTED"

    @dataclass(frozen=True, slots=True)
    class EnrichmentItemResult:
        identity: OpportunityIdentity
        status: EnrichmentItemStatus
        evidence: ExecutionLocationEvidence | None
        source_fingerprint: str
        observation_key: str
        message: str

    @dataclass(frozen=True, slots=True)
    class EnrichmentBatchResult:
        source_fingerprint: str
        generation: int
        items: tuple[EnrichmentItemResult, ...]
        cancelled: bool

    class ExecutionLocationEnrichmentService:
        def __init__(
            self,
            cache: ExecutionLocationCache,
            provider: EGPBrowserDetailProvider,
            parser: Callable[[ObservedDetailResponse], ExecutionLocationParseResult],
        ) -> None
        async def enrich(
            self,
            items: Sequence[OpportunityRadarItem],
            *,
            source_session: SourceSessionIdentity,
            generation: int,
            cancel: CancellationToken,
            on_progress: Callable[[int, int, EnrichmentItemResult], None] | None = None,
        ) -> EnrichmentBatchResult

The service checks source_session SHA before starting and before applying. A stale result may remain in the cache for forensic evidence, but it cannot update the current projection when source fingerprint or generation differs. Results are deterministic for a given source identity and evidence set. Applying a batch is a single terminal operation; partial items remain visible to Inspector and do not enter confirmed province/city dropdown options.

The effective projection is consumed by opportunity_radar.py, filter_engine.py, and opportunity_intelligence.py. The filter contract remains workbook explicit > confirmed enrichment province/city > UNKNOWN for TBMT; PARTIAL district/ward never becomes a filter value. Generic Find remains literal, case-insensitive, accent-sensitive substring OR. KHMT evaluation is unchanged.

### M4 TDD and verification

RED command:

    .venv\Scripts\python.exe -m pytest tests/test_execution_location_service.py tests/test_opportunity_filter_search.py -q

Expected RED is absent batch statuses, stale-generation guard, or projection-aware filtering.

Minimum implementation adds immutable item/batch results, sequential acquisition, progress/cancel handling, stale-source rejection, projection application, and filter-engine compatibility.

GREEN commands:

    .venv\Scripts\python.exe -m pytest tests/test_execution_location_service.py tests/test_opportunity_filter_search.py -q
    .venv\Scripts\python.exe -m pytest tests/test_opportunity_radar.py tests/test_opportunity_intelligence.py tests/test_tbmt_importer.py -q
    .venv\Scripts\python.exe -m ruff check src/qi_crawler/market_intelligence/execution_location_service.py src/qi_crawler/market_intelligence/opportunity_radar.py src/qi_crawler/market_intelligence/filter_engine.py src/qi_crawler/market_intelligence/opportunity_intelligence.py tests/test_execution_location_service.py tests/test_opportunity_filter_search.py
    git diff --check

The tests must cover confirmed/partial/unknown/challenge/stale/cancelled statuses, source fingerprint mismatch, changed-source non-application, deterministic result ordering, multi-location matching, no mutation of source item/provenance, Generic Find, and KHMT regression.

    IMPACT_RADIUS = Radar projection, search/filter authority, source-session generation, cache application.
    EDIT_RADIUS = execution_location_service.py, opportunity_radar.py, filter_engine.py, opportunity_intelligence.py, and the named tests.
    TEST_RADIUS = service fakes, projection/filter regression, and source-integrity tests.

Commit: feat(location): add cancellable source-backed enrichment service.

## M5 — Human-triggered GUI integration

CONDITIONAL TASK: DO NOT EXECUTE unless M4 evidence is accepted and Planner/Human authorize M5.

### M5 exact GUI contract

In src/qi_crawler/gui_services.py add thin adapters with these signatures:

    def start_execution_location_enrichment(
        config: AppConfig,
        items: Sequence[OpportunityRadarItem],
        source_session: SourceSessionIdentity,
        *,
        generation: int,
    ) -> GuiTaskHandle

    def cancel_execution_location_enrichment(handle: GuiTaskHandle) -> None

    def apply_execution_location_batch(
        result: EnrichmentBatchResult,
        *,
        current_source_session: SourceSessionIdentity,
        current_generation: int,
    ) -> EffectiveOpportunityIndex

In src/qi_crawler/gui.py add a Human-labelled action named Làm giàu Địa điểm thực hiện từ e-GP, an explicit progress indicator, a DỪNG action, a terminal status summary, and one apply-once callback. The GUI never calls e-GP directly and never edits an OpportunityRadarItem. After a confirmed batch is applied, rebuild the TBMT selector from distinct confirmed province/city values only, preserve the prior selection when still valid, otherwise select Tất cả, show PARTIAL evidence in Inspector, show UNKNOWN/invalidated items explicitly, and rerun the current filter exactly once. A source switch or generation change invalidates pending application.

### M5 TDD and verification

RED command:

    .venv\Scripts\python.exe -m pytest tests/test_bid_radar_gui.py tests/test_bid_radar_gui_services.py -q

Expected RED is the missing explicit action/progress/cancel/apply-once contract or a stale result being applied after a source switch.

Minimum implementation adds only the adapters and GUI wiring above; no network logic, DB writes, or automatic import is introduced.

GREEN commands:

    .venv\Scripts\python.exe -m pytest tests/test_bid_radar_gui.py tests/test_bid_radar_gui_services.py -q
    .venv\Scripts\python.exe -m pytest tests/test_gui.py tests/test_opportunity_workspace_handoff.py -q
    .venv\Scripts\python.exe -m ruff check src/qi_crawler/gui.py src/qi_crawler/gui_services.py tests/test_bid_radar_gui.py tests/test_bid_radar_gui_services.py
    git diff --check

GUI tests must prove explicit Human action, no auto-import at workbook load, progress, DỪNG, terminal apply once, confirmed-only dropdown values, PARTIAL Inspector evidence, source-switch invalidation, valid-selection preservation, and unchanged result identity mapping.

    IMPACT_RADIUS = Bid Radar desktop workflow, source session, filter selector, Inspector, review/handoff mapping.
    EDIT_RADIUS = gui_services.py, gui.py, and existing GUI/service tests.
    TEST_RADIUS = Qt GUI fixtures, service adapters, source-switch and selector tests.

Commit: feat(bid-radar): add explicit e-GP location enrichment action.

## M6 — real-source acceptance and regression

CONDITIONAL TASK: DO NOT EXECUTE unless M5 evidence is accepted and Planner/Human authorize M6.

### M6 fixed real-source fixture

Use exactly:

    D:\QI Technology\QI Crawler\business-data\TBMT_3_9_2026.xlsx
    expected SHA-256 = 5B8C033A3BAAEA682DE53E1FB410B2138B876FBA77DD1124B58FCA93263E064A

The acceptance run records the exact source base/revision selected by the Work Order, the M0-proven real execution-location value, and the response/cache SHA-256. The source workbook is read-only and must retain its original SHA and provenance before and after enrichment.

### M6 acceptance sequence

1. Rehash the workbook and fail closed on mismatch.
2. Import it locally and record baseline item count, source SHA, source fields, raw fields, location_detail_raw, and provenance.
3. Confirm the exact revision identity and run the bounded enrichment action against the official frontend only.
4. Verify the observed location is displayed as source-backed evidence and, when province/city is direct, appears in the confirmed dropdown.
5. Verify no district/ward-only value is promoted into the province/city filter.
6. Verify matching selected location returns PASS, absent selected location returns FAIL only when execution evidence exists, and missing/partial/invalid evidence returns UNKNOWN/INDETERMINATE.
7. Verify HCM-versus-Dong Nai and multi-location cases using the real observed evidence plus safe fixture rows.
8. Verify workbook SHA, provenance, source_fields, raw_fields, and location_detail_raw are unchanged.
9. Verify cache key, response hash, parser version, and atomic record integrity.
10. Change the source fingerprint in a temporary copy and verify the stale batch cannot apply; verify a valid prior selection remains preserved after dropdown rebuild.
11. Close and restart the application or service boundary, reopen the exact source identity, and confirm the cache/projection semantics remain deterministic.

M6 coverage is smoke acceptance only; do not invent a full real-source count until the command actually runs. Any network challenge, missing direct province/city, source mismatch, cache corruption, or unexplained mutation is a HOLD and stops the lane.

### M6 tests and verification

Add or update tests/test_execution_location_service.py, tests/test_bid_radar_gui.py, tests/test_opportunity_intelligence.py, and tests/test_tbmt_importer.py for the acceptance invariants. Run:

    .venv\Scripts\python.exe -m pytest tests/test_execution_location.py tests/test_execution_location_cache.py tests/test_egp_detail_provider.py tests/test_execution_location_service.py tests/test_opportunity_filter_search.py tests/test_bid_radar_gui.py tests/test_bid_radar_gui_services.py tests/test_opportunity_intelligence.py tests/test_tbmt_importer.py -q
    .venv\Scripts\python.exe -m pytest tests/test_opportunity_filter_search.py tests/test_bid_radar_gui.py tests/test_bid_radar_gui_services.py tests/test_opportunity_intelligence.py tests/test_tbmt_importer.py -q
    .venv\Scripts\python.exe -m pytest -q
    .venv\Scripts\python.exe -m ruff check .
    .venv\Scripts\python.exe -m pip check
    git diff --check
    .venv\Scripts\python.exe plugins/qi-agent-workbench/verify_lock.py --root plugins/qi-agent-workbench

Record actual collection/pass counts, Ruff output, pip check output, diff-check exit status, and Workbench integrity result. Never replace missing hosted or real-source evidence with a local claim.

    IMPACT_RADIUS = Entire R2B source-to-GUI path, existing Bid Radar regressions, real workbook and cache evidence.
    EDIT_RADIUS = only the previously accepted M1–M5 paths and the explicitly named acceptance tests.
    TEST_RADIUS = real-source smoke, focused regressions, full pytest, Ruff, pip check, diff check, and Workbench integrity.

Commit: test(location): record R2B real-source acceptance evidence.

## Checkpoints and commit protocol

Checkpoint 0: this plan and the Human-approved spec → Planner audit → Human decision.

Checkpoint M0: bounded real response report → Planner evidence audit → Human decision. No M1 starts automatically.

Checkpoints M1, M2, M3, M4, M5, and M6: focused RED/GREEN evidence, relevant regression output, Ruff, diff-check, and scope review → Planner audit → independent Reviewer when requested → explicit authority for the next milestone.

Each accepted milestone receives one bounded commit with the exact message defined in that section. A commit is never amended, rebased, or reused as evidence for a later unreviewed change. The final R2B implementation branch does not merge or release by virtue of this plan.

## Final self-review checklist

- Spec coverage: architecture, authority, filter level, no inference, cache identity, browser policy, M0 proof, stale guard, GUI safety, and M6 acceptance are all represented.
- Type consistency: OpportunityIdentity, SourceSessionIdentity, OpportunityRadarItem, ExecutionLocationEvidenceIndex, EffectiveOpportunityProjection, cache records, provider responses, and batch results have explicit immutable interfaces.
- Network boundary: only BrowserFetcher/AccessPolicy-backed M3 service may observe official responses; GUI and local importer stay offline.
- Identity: source type, base identifier, exact revision, notify identifier, response SHA, source SHA, and generation are independently checked.
- Province/city rule: direct meaningful province/city is required for CONFIRMED; district/ward is preserved as PARTIAL and never inferred upward.
- Evidence boundary: Builder claims, machine results, Planner audit, Reviewer audit, Human approval, merge, and release are distinct states.
- No placeholders: every implementation path, function signature, test command, expected RED reason, minimum implementation, regression command, and commit message is named.
- Scope: no product schema, migration, release, Warehouse/HSMT, Team Bid pilot, NotebookLM, scheduler, MCP, connector, or autonomous Spine work is introduced.

## Completion boundary

Completion of this plan means only that the authorized R2B milestones have produced auditable evidence. It does not authorize merge, official release, A7 export, REL-C, a new product Work Package, or a change to Human/Planner authority.
