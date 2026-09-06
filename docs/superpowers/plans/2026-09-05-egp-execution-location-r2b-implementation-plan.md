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
- Do not make an e-GP request during documentation planning. M0 is the first authorized network-capable validation milestone and it uses the normal official frontend browser session. M3 and M6 may perform network activity only after their separate Planner and Human authorization checkpoints.
- Do not add database tables, Alembic migrations, API endpoints, scheduler jobs, daemon behavior, MCP, external connectors, auto-Spine, auto-merge, or auto-release.
- Do not modify KHMT import, KHMT province/city normalization, Generic Find semantics, existing workbook source bytes, or existing source provenance.
- Do not infer a province/city from package name, project name, procuring entity, procuring address, issue address, or any unrelated text.
- Do not use token extraction, token export, request replay, CAPTCHA solvers, proxy rotation, fingerprint spoofing, private credentials, hidden browser storage, or aggressive retries.
- At M0, a missing direct province/city value fails the M0 province gate. During production M3/M4, a valid district/ward-only response is FOUND with PARTIAL quality and the batch continues with province filtering UNKNOWN. Only ACCESS_CHALLENGE or INTEGRITY_MISMATCH stops the whole batch; malformed or unsupported item responses become SCHEMA_UNSUPPORTED/RETRIEVAL_FAILED item outcomes.
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

    src/qi_crawler/market_intelligence/search.py
        Explicit keyword-only forwarding of an EffectiveOpportunityIndex; the default None path preserves existing callers.

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

The following existing files are inspection-only unless a milestone below explicitly names them: src/qi_crawler/browser.py, src/qi_crawler/compliance.py, src/qi_crawler/config.py, src/qi_crawler/market_intelligence/search.py, src/qi_crawler/market_intelligence/tbmt_importer.py, src/qi_crawler/market_intelligence/source_integrity.py, src/qi_crawler/market_intelligence/source_session.py, and src/qi_crawler/market_intelligence/location_resolver.py. The existing location_resolver is not reused for TBMT enrichment because its historical MI-1 mappings can infer from unrelated fields. FunctionWorker and GuiTaskBridge are existing types at src/qi_crawler/gui.py:242 and src/qi_crawler/gui.py:289; the GUI task adapter uses those concrete types.

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

Use the official public e-GP frontend in a normal Playwright browser session to observe at most three real detail responses. The only approved candidate pairs are IB2600488839:00, IB2600498410:00, and IB2600489267:00. They are candidates, not assertions that a province/city value exists. The run is bounded at one browser context, one detail acquisition at a time, and min(configured_rate, 12) requests per minute. The existing BrowserFetcher page timeout remains authoritative. No direct tokenless API replay is allowed.

### M0 exact execution method

Create this temporary script outside the repository:

    %TEMP%\qi-r2b-m0\capture_egp_location.py

Run it only after M0 authorization:

    .venv\Scripts\python.exe %TEMP%\qi-r2b-m0\capture_egp_location.py --config config.yaml --detail-url "IB2600488839:00=$env:QI_R2B_M0_DETAIL_URL_1" --detail-url "IB2600498410:00=$env:QI_R2B_M0_DETAIL_URL_2" --detail-url "IB2600489267:00=$env:QI_R2B_M0_DETAIL_URL_3" --max-samples 3 --concurrency 1 --raw-root %TEMP%\qi-r2b-m0\raw --report docs/agent_handoff/evidence/R2B-M0-egp-location-response.md

The three QI_R2B_M0_DETAIL_URL_* values are exact official frontend detail URLs or route descriptors copied verbatim from the later Human/Planner M0 Work Order. The script does not construct a source-to-URL mapping from source_id/revision. It validates the e-GP allowed domain and causal binding to the known revision UUID. Routes are never committed, raw output is TEMP-only, and report routes omit query strings.

The complete temporary script below uses BrowserFetcher, AccessPolicy, robots checks, the existing page timeout, and a dedicated DomainRateLimiter at min(config.crawl.requests_per_minute, 12). It never extracts tokens, exports cookies, replays requests, saves storage state, or uses a solver.

    from __future__ import annotations
    import argparse, asyncio, hashlib, json
    from dataclasses import dataclass
    from datetime import UTC, datetime
    from pathlib import Path
    from urllib.parse import urlsplit, urlunsplit
    from qi_crawler.browser import BrowserFetcher
    from qi_crawler.compliance import AccessDenied, DomainRateLimiter
    from qi_crawler.config import load_config

    @dataclass(frozen=True)
    class M0Sample:
        source_id: str
        revision: str
        expected_notify_id: str

        @property
        def source_revision_id(self) -> str:
            return f"{self.source_id}-{self.revision}"

        @property
        def key(self) -> str:
            return f"{self.source_id}:{self.revision}"

    SAMPLES = (
        M0Sample("IB2600488839", "00", "ca1aadd6-edbc-4912-81fa-dccba9712245"),
        M0Sample("IB2600498410", "00", "9446dc1c-3687-4fa5-a73f-67b1b9cc75cf"),
        M0Sample("IB2600489267", "00", "9716b9c7-e446-4e0a-89fc-27cb244b3eac"),
    )

    def safe_url(value: str) -> str:
        parsed = urlsplit(value)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))

    def walk(value, path=""):
        if isinstance(value, dict):
            yield path or "/", value
            for key, child in value.items():
                yield from walk(child, f"{path}/{str(key).replace('~', '~0').replace('/', '~1')}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from walk(child, f"{path}/{index}")

    def supported_location_path(payload):
        containers = []
        for detail_path, node in walk(payload):
            for name in ("bidpBidLocationList", "lsBidpBidLocationDTO"):
                if name in node:
                    value = node[name]
                    if not isinstance(value, list):
                        return None, None, "UNSUPPORTED_CONTAINER_SHAPE"
                    containers.append((detail_path, f"{detail_path}/{name}", value))
        if len(containers) != 1:
            return None, None, "NOT_PROVEN"
        detail_path, location_path, dtos = containers[0]
        evidence = []
        for index, dto in enumerate(dtos):
            if not isinstance(dto, dict):
                return None, None, "UNSUPPORTED_DTO_SHAPE"
            def text(name):
                value = dto.get(name)
                return value.strip() if isinstance(value, str) and value.strip() else None
            province, district, ward = text("provName"), text("districtName"), text("wardName")
            if province or district or ward:
                evidence.append({"path": f"{location_path}/{index}", "province_city": province,
                                 "district": district, "ward": ward})
        return detail_path, (location_path, evidence), "PROVEN"

    def visible_challenge_text(text: str) -> bool:
        lowered = text.casefold()
        return any(marker in lowered for marker in (
            "access denied", "xác minh bạn là con người", "xác minh bạn không phải",
            "human verification", "verify you are human",
        ))

    async def one(fetcher, limiter, url, sample, raw_root):
        await fetcher.ensure_browser_access_allowed(url)
        await limiter.wait(url)
        page, captures, pending = await fetcher.new_page(), [], []
        async def record(response):
            content_type = (await response.all_headers()).get("content-type", "")
            if "json" not in content_type.casefold():
                return
            body = await response.body()
            try:
                payload = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                return
            captures.append({"response": response, "body": body, "json": payload,
                             "request_binding": f"{response.request.url}\n{response.request.post_data or ''}",
                             "status": response.status, "content_type": content_type})
        page.on("response", lambda response: pending.append(asyncio.create_task(record(response))))
        try:
            response = await page.goto(url, wait_until="domcontentloaded")
            if response is not None and response.status in {401, 403, 429}:
                raise AccessDenied(f"ACCESS_CHALLENGE HTTP {response.status}")
            await page.wait_for_timeout(fetcher.config.crawl.render_wait_ms)
            if visible_challenge_text(await page.locator("body").inner_text()):
                raise AccessDenied("ACCESS_CHALLENGE visible human-verification UI")
            await asyncio.gather(*pending)
            selected = [item for item in captures if sample.expected_notify_id in item["request_binding"]]
            if len(selected) != 1:
                return {"sample": sample.key, "outcome": "INTEGRITY_MISMATCH",
                        "REAL_IDENTITY_BINDING": "NOT_PROVEN"}
            selected = selected[0]
            digest = hashlib.sha256(selected["body"]).hexdigest()
            raw_root.mkdir(parents=True, exist_ok=True)
            (raw_root / f"{sample.source_id}-{sample.revision}-{digest}.json").write_bytes(selected["body"])
            detail_path, location_result, path_state = supported_location_path(selected["json"])
            envelope = {"root_type": type(selected["json"]).__name__,
                        "root_keys": sorted(selected["json"]) if isinstance(selected["json"], dict) else []}
            base = {"sample": sample.key, "official_notify_no": sample.source_id,
                    "revision": sample.revision, "source_revision_id": sample.source_revision_id,
                    "notify_id": sample.expected_notify_id, "binding_method": "EXPECTED_NOTIFY_ID_REQUEST",
                    "REAL_RESPONSE_ENVELOPE": envelope, "REAL_DETAIL_OBJECT_PATH": detail_path or "NOT_PROVEN",
                    "response_sha256": digest, "response_status": selected["status"],
                    "sanitized_response_route": safe_url(selected["response"].url),
                    "captured_at": datetime.now(UTC).isoformat()}
            if path_state != "PROVEN":
                return base | {"outcome": "HOLD_DETAIL_PATH", "REAL_LOCATION_DTO_PATH": "NOT_PROVEN",
                               "REAL_SEMANTIC_LOCATION_VALUE": "NOT_PROVEN"}
            location_path, values = location_result
            confirmed = [value for value in values if value["province_city"]]
            partial = [value for value in values if not value["province_city"] and (value["district"] or value["ward"])]
            return base | {"outcome": "PROVEN" if confirmed else "PARTIAL" if partial else "NO_PROVINCE",
                           "REAL_LOCATION_DTO_PATH": location_path,
                           "REAL_SEMANTIC_LOCATION_VALUE": confirmed[0]["province_city"] if confirmed else "NOT_PROVEN",
                           "location_dtos": confirmed or partial}
        finally:
            await page.close()

    async def run(args):
        if args.max_samples != 3 or args.concurrency != 1 or len(args.detail_url) != 3:
            raise SystemExit("M0 is exactly three approved sequential samples and concurrency one")
        urls = dict(value.split("=", 1) for value in args.detail_url)
        if set(urls) != {sample.key for sample in SAMPLES}:
            raise SystemExit("each exact sample requires a Work-Order-supplied official detail URL")
        config, report = load_config(args.config), {
            "samples": [], "REAL_RESPONSE_ENVELOPE": "NOT_PROVEN", "REAL_DETAIL_OBJECT_PATH": "NOT_PROVEN",
            "REAL_IDENTITY_BINDING": "NOT_PROVEN", "REAL_NOTIFYNO_REVISION_UUID_RELATION": "NOT_PROVEN",
            "REAL_LOCATION_DTO_PATH": "NOT_PROVEN", "REAL_SEMANTIC_LOCATION_VALUE": "NOT_PROVEN",
            "M0_REAL_PROVINCE_CITY_VALUE": "NOT_PROVEN", "M0_IDENTITY_BINDING": "FAIL",
            "M0_DETAIL_OBJECT_PATH": "FAIL", "M0_LOCATION_DTO_PATH": "FAIL", "M0_ACCESS_POLICY": "PASS",
            "M0_RAW_SECRET_EXCLUSION": "PASS", "M0_PROVINCE_GATE": "FAIL",
        }
        fetcher, limiter = BrowserFetcher(config), DomainRateLimiter(min(config.crawl.requests_per_minute, 12))
        await fetcher.start(headed=True)
        try:
            for sample in SAMPLES:
                try:
                    item = await one(fetcher, limiter, urls[sample.key], sample, args.raw_root)
                except AccessDenied as error:
                    report["samples"].append({"sample": sample.key, "outcome": "ACCESS_CHALLENGE"})
                    report["stop_reason"] = str(error)
                    report["M0_ACCESS_POLICY"] = "HOLD"
                    break
                report["samples"].append(item)
                if item["outcome"] in {"INTEGRITY_MISMATCH", "HOLD_DETAIL_PATH"}:
                    report["stop_reason"] = "INTEGRITY_MISMATCH"
                    break
                if item["outcome"] == "PROVEN":
                    report["M0_REAL_PROVINCE_CITY_VALUE"], report["M0_PROVINCE_GATE"] = "PROVEN", "PASS"
                    for key in ("REAL_RESPONSE_ENVELOPE", "REAL_DETAIL_OBJECT_PATH", "REAL_LOCATION_DTO_PATH",
                                "REAL_SEMANTIC_LOCATION_VALUE"):
                        report[key] = item[key]
                    report["REAL_IDENTITY_BINDING"] = "EXPECTED_NOTIFY_ID_REQUEST"
                    report["REAL_NOTIFYNO_REVISION_UUID_RELATION"] = {
                        "official_notify_no": sample.source_id, "revision": sample.revision,
                        "source_revision_id": sample.source_revision_id, "notify_id": sample.expected_notify_id}
                    report["M0_IDENTITY_BINDING"] = "PASS"
                    report["M0_DETAIL_OBJECT_PATH"] = "PASS"
                    report["M0_LOCATION_DTO_PATH"] = "PASS"
                    break
            else:
                report["stop_reason"] = "CANDIDATES_EXHAUSTED"
        finally:
            await fetcher.close()
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        required = ("M0_IDENTITY_BINDING", "M0_DETAIL_OBJECT_PATH", "M0_LOCATION_DTO_PATH",
                    "M0_ACCESS_POLICY", "M0_RAW_SECRET_EXCLUSION", "M0_PROVINCE_GATE")
        return 0 if all(report[key] == "PASS" for key in required) else 2

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--detail-url", action="append", required=True)
    parser.add_argument("--max-samples", required=True, type=int)
    parser.add_argument("--concurrency", required=True, type=int)
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    raise SystemExit(asyncio.run(run(parser.parse_args())))

### M0 procedure

1. Confirm the approved official frontend URL template in the Human Work Order and set QI_R2B_M0_DETAIL_URL_TEMPLATE only for this process. Do not infer a route or use an undocumented API endpoint.
2. Start BrowserFetcher with the current AppConfig and AccessPolicy. Validate domain and robots policy before navigation.
3. Acquire the three M0Sample objects sequentially in their exact command order. Browser asset requests are not counted as detail acquisitions.
4. Save selected raw response bytes only under the unique temporary directory outside the repository. Record SHA-256, status, content type, sanitized observed route, and capture time.
5. Bind each response only through the spike-proven M0Sample expected_notify_id: approved source/revision → expected notify_id → exactly one official frontend request containing that UUID → the response generated by it. The report records official_notify_no, revision, source_revision_id, notify_id, binding_method, and sanitized response route. Any ambiguity is INTEGRITY_MISMATCH and stops M0; the script never identifies a revision by a generic response substring.
6. Record PARTIAL when a candidate has district/ward but no province/city; PARTIAL does not satisfy the province gate and the next candidate must run. Only ACCESS_CHALLENGE, INTEGRITY_MISMATCH, or robots-policy HOLD stops immediately.
7. If all three candidates complete without a direct province/city, record M0_REAL_PROVINCE_CITY_VALUE = NOT_PROVEN and M0_PROVINCE_GATE = FAIL, then STOP_FOR_PLANNER.

### M0 proof contract

The report must contain exact observed values for REAL_RESPONSE_ENVELOPE, REAL_DETAIL_OBJECT_PATH, REAL_IDENTITY_BINDING, REAL_NOTIFYNO_REVISION_UUID_RELATION, REAL_LOCATION_DTO_PATH, REAL_SEMANTIC_LOCATION_VALUE, and M0_REAL_PROVINCE_CITY_VALUE. It must identify the source base/revision and response SHA-256 without storing secrets.

### M0 stop/decision contract

    M0_REAL_PROVINCE_CITY_VALUE = PROVEN
    M0_IDENTITY_BINDING = PASS
    M0_DETAIL_OBJECT_PATH = PROVEN
    M0_LOCATION_DTO_PATH = PROVEN
    M0_ACCESS_POLICY = PASS
    M0_RAW_SECRET_EXCLUSION = PASS

Identity mismatch, HTTP challenge, CAPTCHA, robots uncertainty, or access-control interruption sets M0_ACCESS = HOLD and stops M0. A malformed/unsupported candidate response is recorded and the next candidate runs. A missing direct province/city after all three candidates sets M0_REAL_PROVINCE_CITY_VALUE = NOT_PROVEN and M0_PROVINCE_GATE = FAIL, then STOP_FOR_PLANNER. Do not bypass a challenge. The mandatory next sequence is M0 evidence → Planner audit → Human decision; M0 never auto-authorizes M1–M6. Production M3/M4 handles PARTIAL item evidence without stopping the batch, while ACCESS_CHALLENGE and INTEGRITY_MISMATCH remain whole-batch stops.

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

    class ExecutionLocationItemOutcome(StrEnum):
        FOUND = "FOUND"
        SOURCE_HAS_NO_LOCATION = "SOURCE_HAS_NO_LOCATION"
        RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
        SCHEMA_UNSUPPORTED = "SCHEMA_UNSUPPORTED"
        INTEGRITY_MISMATCH = "INTEGRITY_MISMATCH"
        ACCESS_CHALLENGE = "ACCESS_CHALLENGE"
        NOT_PROCESSED = "NOT_PROCESSED"

    @dataclass(frozen=True, slots=True)
    class ExecutionLocationEvidence:
        identity: OpportunityIdentity
        province_city: str | None
        district: str | None
        ward: str | None
        quality: ExecutionLocationQuality
        source_path: str
        response_sha256: str
        observed_at: datetime

    class ExecutionLocationParseOutcome(StrEnum):
        FOUND = "FOUND"
        SOURCE_HAS_NO_LOCATION = "SOURCE_HAS_NO_LOCATION"
        SCHEMA_UNSUPPORTED = "SCHEMA_UNSUPPORTED"

    @dataclass(frozen=True, slots=True)
    class ExecutionLocationParseResult:
        outcome: ExecutionLocationParseOutcome
        evidence: tuple[ExecutionLocationEvidence, ...]
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
        execution_location_evidence: tuple[ExecutionLocationEvidence, ...]
        confirmed_province_city: tuple[str, ...]
        quality: ExecutionLocationQuality

    def project_effective_opportunity(
        item: OpportunityRadarItem,
        evidence_index: ExecutionLocationEvidenceIndex,
    ) -> EffectiveOpportunityProjection

    @dataclass(frozen=True, slots=True)
    class EffectiveOpportunityIndex:
        projections: tuple[EffectiveOpportunityProjection, ...]
        def for_observation_key(
            self, observation_key: str
        ) -> EffectiveOpportunityProjection | None

The parser accepts structured detail only at the M0-proven object path. One official location DTO produces one ExecutionLocationEvidence record. Every multi-DTO layer preserves those records as tuple[ExecutionLocationEvidence, ...], never by flattening province/district/ward components across DTOs. FOUND returns a non-empty tuple; SOURCE_HAS_NO_LOCATION and SCHEMA_UNSUPPORTED return evidence = (). SOURCE_HAS_NO_LOCATION applies only to a supported schema with no meaningful component; SCHEMA_UNSUPPORTED applies to an unknown or malformed schema. Within FOUND, quality is CONFIRMED for meaningful province/city, PARTIAL for district/ward without province/city, and UNKNOWN when the supported record has no filterable component.

Projection precedence is component-level: explicit workbook province/city > confirmed e-GP province/city > UNKNOWN for the filter. Workbook district/ward is preserved as provenance but does not block confirmed e-GP province/city. Structured e-GP district/ward remains PARTIAL display evidence and never becomes a province/city value. The projection is immutable and never writes into item.source_fields, item.raw_fields, item.location_detail_raw, or workbook provenance; display strings are derived views only.

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

The test matrix must include HCM-only pass, HCM-only versus Đồng Nai fail, HCM plus Đồng Nai matching either value, missing UNKNOWN, procuring-address HCM with execution Đồng Nai fail, issue-location HCM with execution Đồng Nai fail, explicit workbook province/city outranking detail, workbook district-only allowing confirmed e-GP province/city, malformed schema returning SCHEMA_UNSUPPORTED, and unchanged KHMT behavior.

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
        official_notify_no: str
        source_revision_id: str
        notify_id: str
        retrieved_at: datetime
        response_sha256: str
        raw_schema_version: str
        parser_contract_version: str
        retrieval_method: str
        raw_payload_path: Path
        workbook_source_sha256: str | None
        evidence: tuple[ExecutionLocationEvidence, ...]

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

The on-disk key is source_type + base_id + revision. Each record preserves a reparsable raw official response payload or sanitized raw JSON payload at raw_payload_path plus official_notify_no, source_revision_id, notify_id, retrieved_at, response_sha256, raw_schema_version, parser_contract_version, retrieval_method, and optional workbook_source_sha256 provenance. The cache reader recomputes the raw payload SHA-256 and rejects a mismatch before parsing. Parser-version changes may invalidate or reparse an existing raw payload without browser reacquisition. Corrupt JSON, wrong schema, wrong identity, or malformed evidence is rejected and never returned as a usable record. Writes use a temporary sibling file, flush/close, and atomic replace. Cookies, tokens, authorization headers, browser storage, and raw private response secrets are not cache fields. Workbook source_sha256 is not part of cache lookup identity or cache corruption validity; stale application is enforced separately by source session, workbook SHA, generation, and observation_key.

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

The tests must prove cache hit, source identity mismatch, revision mismatch, raw payload SHA mismatch, parser-version reparse/invalidation, malformed record rejection, atomic replacement, absence of secrets, and the fact that a different workbook SHA alone does not invalidate the same exact e-GP revision.

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
        official_notify_no: str
        source_revision_id: str
        notify_id: str
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
        def __init__(
            self,
            fetcher: BrowserFetcher,
            *,
            concurrency_limit: int = 1,
            detail_acquisition_rate: int | None = None,
        ) -> None
        async def resolve_revision(
            self, identity: OpportunityIdentity, *, is_cancelled: Callable[[], bool]
        ) -> ResolvedEGPIdentity
        async def fetch_detail(
            self, resolved: ResolvedEGPIdentity, *, is_cancelled: Callable[[], bool]
        ) -> ObservedDetailResponse

The approved identity vocabulary is official_notify_no = IB..., revision = 00, source_revision_id = IB...-00, and notify_id = the revision-specific UUID observed in the official frontend flow. The provider navigates the official frontend with BrowserFetcher, uses AccessPolicy and DomainRateLimiter, enforces CONCURRENCY_LIMIT = 1, and uses min(config.crawl.requests_per_minute, 12) as the detail-acquisition rate. The UUID is observed metadata; the caller does not need to discover or supply it before navigation. Cancellation checks occur before navigation, during retry waits, during detail-rate waits, and between response waits; every active browser operation has the existing finite BrowserFetcher timeout. For a cancellable rate wait, create limiter.wait(url) as an asyncio Task, poll is_cancelled() at a short bounded interval, and on Human DỪNG cancel and await the limiter task so asyncio releases its lock normally; return the governed cancellation outcome. A finite timeout, cancellation signal, challenge detection, HTTP mismatch, and response-envelope mismatch all return governed failure statuses. Retries consume the same detail-acquisition rate budget; browser asset requests are not counted as separate detail attempts. No provider method exports or persists browser credentials.

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

The tests must distinguish exact identity binding, timeout, one-at-a-time concurrency, the separate concurrency/rate values, the 12-per-minute detail budget, retry budget consumption, CAPTCHA/access denial, cancellation, malformed response, and no token/replay behavior.

    IMPACT_RADIUS = BrowserFetcher, AccessPolicy, compliance markers, official e-GP frontend response path.
    EDIT_RADIUS = egp_detail_provider.py and its focused tests; browser.py is unchanged unless a Planner-approved proven seam defect exists.
    TEST_RADIUS = provider fakes and existing compliance/browser regressions.

Commit: feat(location): add bounded browser-native e-GP detail provider.

## M4 — batch service and effective projection

CONDITIONAL TASK: DO NOT EXECUTE unless M3 evidence is accepted and Planner/Human authorize M4.

### M4 exact interfaces

In src/qi_crawler/market_intelligence/execution_location_service.py define:

    from threading import Event

    class ExecutionLocationBatchOutcome(StrEnum):
        COMPLETED = "COMPLETED"
        PARTIAL = "PARTIAL"
        STOPPED_ACCESS_CHALLENGE = "STOPPED_ACCESS_CHALLENGE"
        STOPPED_INTEGRITY_MISMATCH = "STOPPED_INTEGRITY_MISMATCH"
        CANCELLED_BY_HUMAN = "CANCELLED_BY_HUMAN"
        FAILED_BEFORE_START = "FAILED_BEFORE_START"

    @dataclass(frozen=True, slots=True)
    class EnrichmentCancellationToken:
        event: Event
        def cancel(self) -> None
        def is_cancelled(self) -> bool

    @dataclass(frozen=True, slots=True)
    class EnrichmentItemResult:
        identity: OpportunityIdentity
        outcome: ExecutionLocationItemOutcome
        evidence: tuple[ExecutionLocationEvidence, ...]
        observation_key: str
        message: str

    @dataclass(frozen=True, slots=True)
    class EnrichmentBatchResult:
        source_session: SourceSessionIdentity
        generation: int
        items: tuple[EnrichmentItemResult, ...]
        outcome: ExecutionLocationBatchOutcome
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
            cancel: EnrichmentCancellationToken,
            on_progress: Callable[[int, int, EnrichmentItemResult], None] | None = None,
        ) -> EnrichmentBatchResult

The service checks source_session SHA before starting and before applying. EnrichmentCancellationToken.cancel() sets its Event; the GUI DỪNG action calls that token method and never tries to cancel through GuiTaskBridge. A stale result may remain in the cache for forensic evidence, but it cannot update the current projection unless source_session_matches(batch.source_session, current_source_session) and batch.generation == current_generation. Reject the other case as STALE_BATCH_RESULT with no projection apply. Results are deterministic for a given source identity and evidence set. Applying a batch is a single terminal operation; partial items remain visible to Inspector and do not enter confirmed province/city dropdown options.

The effective projection is consumed by opportunity_radar.py, filter_engine.py, and opportunity_intelligence.py. The filter contract remains workbook explicit > confirmed enrichment province/city > UNKNOWN for TBMT; PARTIAL district/ward never becomes a filter value. Generic Find remains literal, case-insensitive, accent-sensitive substring OR. KHMT evaluation is unchanged.

### M4 filter/search integration seam

In src/qi_crawler/market_intelligence/filter_engine.py define the backward-compatible seam:

    def evaluate_opportunity(
        item: OpportunityRadarItem,
        profile: FilterProfile,
        *,
        effective_projection: EffectiveOpportunityProjection | None = None,
    ) -> OpportunityFilterEvaluation

In src/qi_crawler/market_intelligence/search.py define:

    def search_opportunities(
        items: tuple[OpportunityRadarItem, ...] | list[OpportunityRadarItem],
        request: TargetedSearchRequest,
        *,
        effective_index: EffectiveOpportunityIndex | None = None,
    ) -> TargetedOpportunitySearchResult

The default effective_projection/effective_index value is None so every existing caller keeps its current behavior. When an index is supplied, search resolves the projection with effective_index.for_observation_key(item.observation_key), never by OpportunityIdentity, and passes it as the keyword-only argument to evaluate_opportunity. Generic Find always reads the original item/source fields. KHMT continues to use its existing province/city criterion. No hidden global index is permitted. OpportunityIntelligenceService.search_opportunities exposes the same optional effective_index and forwards it explicitly.

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

The tests must cover confirmed/partial/unknown/challenge/stale/cancelled statuses, SourceSessionIdentity mismatch, generation mismatch, changed-source non-application, deterministic result ordering, multi-location matching, no mutation of source item/provenance, Generic Find, and KHMT regression.

    IMPACT_RADIUS = Radar projection, search/filter authority, source-session generation, cache application.
    EDIT_RADIUS = execution_location_service.py, opportunity_radar.py, filter_engine.py, search.py, opportunity_intelligence.py, and the named tests.
    TEST_RADIUS = service fakes, projection/filter regression, and source-integrity tests.

Commit: feat(location): add cancellable source-backed enrichment service.

## M5 — Human-triggered GUI integration

CONDITIONAL TASK: DO NOT EXECUTE unless M4 evidence is accepted and Planner/Human authorize M5.

### M5 exact GUI contract

In src/qi_crawler/gui_services.py add only a pure, GUI-independent adapter. gui_services.py must not import or return FunctionWorker or GuiTaskBridge because gui.py imports gui_services.py:

    def run_execution_location_enrichment(
        config: AppConfig,
        items: Sequence[OpportunityRadarItem],
        source_session: SourceSessionIdentity,
        *,
        generation: int,
        cancel: EnrichmentCancellationToken,
        on_progress: Callable[..., None] | None = None,
    ) -> EnrichmentBatchResult

    class ExecutionLocationApplyOutcome(StrEnum):
        APPLIED = "APPLIED"
        STALE_BATCH_RESULT = "STALE_BATCH_RESULT"

    @dataclass(frozen=True, slots=True)
    class ExecutionLocationApplyResult:
        outcome: ExecutionLocationApplyOutcome
        effective_index: EffectiveOpportunityIndex | None

    def apply_execution_location_batch(
        result: EnrichmentBatchResult,
        *,
        current_source_session: SourceSessionIdentity,
        current_generation: int,
    ) -> ExecutionLocationApplyResult

apply_execution_location_batch returns ExecutionLocationApplyResult(APPLIED, effective_index) only when source_session_matches(batch.source_session, current_source_session) and batch.generation == current_generation. On either mismatch it returns ExecutionLocationApplyResult(STALE_BATCH_RESULT, None); cache evidence may remain, but no projection applies. SourceSessionIdentity + generation + observation_key are the only freshness authority: EffectiveOpportunityProjection has no opaque source_fingerprint. In src/qi_crawler/gui.py construct FunctionWorker and GuiTaskBridge around the pure adapter, retain the cancellation token, and wire DỪNG to token.cancel(). Add a Human-labelled action named BỔ SUNG ĐỊA ĐIỂM TỪ e-GP, an explicit progress indicator, a terminal status summary, and one apply-once callback. The GUI never calls e-GP directly and never edits an OpportunityRadarItem. After a confirmed batch is applied, rebuild the TBMT selector from distinct confirmed province/city values only, preserve the prior selection when still valid, otherwise emit and show FILTER_SELECTION_INVALIDATED with a Human-visible notice before selecting Tất cả, show PARTIAL evidence in Inspector, show UNKNOWN/invalidated items explicitly, and rerun the current filter exactly once. A source switch or generation change invalidates pending application.

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

M6 coverage is smoke acceptance only; do not invent a full real-source count until the command actually runs. For the selected M6 source, missing direct province/city fails the M0-backed acceptance gate; it does not change the M3/M4 rule that valid PARTIAL item evidence may continue. Any network challenge, source mismatch, cache corruption, or unexplained mutation is a HOLD and stops the lane.

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

- MULTI_DTO_COLLECTION scan = ExecutionLocationParseResult.evidence, ExecutionLocationCacheRecord.evidence, and EnrichmentItemResult.evidence are tuple[ExecutionLocationEvidence, ...]; SOURCE_HAS_NO_LOCATION and SCHEMA_UNSUPPORTED use ().
- OBSERVATION_KEY_BINDING scan = EffectiveOpportunityIndex exposes for_observation_key(observation_key), and search passes item.observation_key rather than an identity lookup.
- GUI_IMPORT_DIRECTION scan = gui_services.py contains the pure run_execution_location_enrichment adapter and does not import or return FunctionWorker or GuiTaskBridge; gui.py owns those types.
- CANCELLATION_PROPAGATION scan = EnrichmentCancellationToken.cancel() sets Event; DỪNG calls it; provider resolve_revision and fetch_detail receive is_cancelled; cancellation checks cover retry waits, rate waits, pre-navigation, response waits, and finite browser operations.
- SOURCE_SESSION_IDENTITY scan = EnrichmentBatchResult retains SourceSessionIdentity and generation; stale application is rejected as STALE_BATCH_RESULT without projection apply.
- M0_SAMPLE_PROVENANCE scan = exactly IB2600488839:00, IB2600498410:00, and IB2600489267:00 appear as candidate samples, with no claim that any already has a province value.
- M0_PARTIAL_CONTINUE scan = PARTIAL records district/ward evidence, does not satisfy the province gate, and continues to the next candidate; only challenge, integrity mismatch, or robots-policy HOLD stops immediately.
- M0_TEMP_SCRIPT_COMPLETENESS scan = the embedded script covers argparse, exact samples, AppConfig, BrowserFetcher start/close, AccessPolicy/robots checks, sequential rate waits, frontend response observation only, causal UUID binding, TEMP raw writes, SHA-256, sanitized report, and no token/cookie/storage/replay handling.
- CONFIGURED_RATE_POLICY scan = M0 and M3 use min(config.crawl.requests_per_minute, 12), concurrency one, and do not count browser assets as detail acquisitions.
- GUI_INVALIDATION scan = BỔ SUNG ĐỊA ĐIỂM TỪ e-GP is exact, and FILTER_SELECTION_INVALIDATED is shown before fallback to Tất cả.
- PLACEHOLDERS scan = no unfinished marker, undefined interface, or unowned implementation path remains.
- TYPE_CONSISTENCY scan = all referenced signatures have a named type or explicit None terminal value.
- SPEC_COVERAGE scan = architecture, authority, M0 bounded evidence, multi-DTO fidelity, observation identity, cancellation, stale guard, GUI safety, filter authority, and M6 acceptance have named sections.
- EXECUTION_LOCATION_PATH_AUTHORITY scan = M0 searches only bidpBidLocationList and lsBidpBidLocationDTO, requires a list, and reads only provName, districtName, and wardName inside each DTO.
- EXACT_NOTIFY_ID_BINDING scan = each M0Sample has source_id, revision, and spike-proven expected_notify_id; a selected response has exactly one request binding to that UUID.
- NO_REVISION_SUBSTRING_IDENTITY scan = no generic search for source_id/revision text or 00 within response JSON determines identity.
- REAL_PROOF_FIELDS scan = the report contract contains all REAL_* and M0_* gates, and zero exit requires every PASS gate.
- CAPTCHA_RUNTIME_ONLY scan = challenge detection uses status, visible challenge/access-denied UI, or redirect evidence; a static reCAPTCHA script is not itself a challenge.
- M0_EXIT_GATE scan = a province string alone cannot return zero; identity, detail path, location path, access policy, raw-secret exclusion, and province gate must all pass.
- PARTIAL_CONTINUE scan = a supported DTO with district/ward but no provName is PARTIAL and proceeds to the next bounded sample.
- CANCELLABLE_RATE_WAIT scan = rate wait is an asyncio Task polled by is_cancelled and cancelled/awaited on DỪNG.
- APPLY_RESULT_TYPE scan = apply returns ExecutionLocationApplyResult with APPLIED or STALE_BATCH_RESULT, never a bare None sentinel.
- SOURCE_SESSION_SINGLE_AUTHORITY scan = SourceSessionIdentity, generation, and observation_key govern freshness; projection source_fingerprint is absent.
- SPEC COVERAGE = architecture, authority, filter level, no inference, source identity, raw cache, browser policy, M0 proof, stale guard, GUI safety, and M6 acceptance are each mapped to a named section.
- TYPE CONSISTENCY = every referenced type is existing at a cited path or defined in this plan, including Event, EnrichmentCancellationToken, EffectiveOpportunityIndex, ExecutionLocationApplyResult, item outcomes, batch outcomes, cache records, provider responses, and projections.
- OUTCOME VS QUALITY SEPARATION = FOUND, SOURCE_HAS_NO_LOCATION, RETRIEVAL_FAILED, SCHEMA_UNSUPPORTED, INTEGRITY_MISMATCH, ACCESS_CHALLENGE, and NOT_PROCESSED are distinct from CONFIRMED, PARTIAL, and UNKNOWN.
- MULTI-DTO STRUCTURE = one official DTO produces one structured evidence record; multiple DTOs remain a tuple with province/district/ward relationships intact.
- FILTER SEAM = evaluate_opportunity and search_opportunities keyword-only projection/index signatures preserve old callers, Generic Find, and KHMT behavior.
- CACHE RAW PAYLOAD = reparsable raw payload, response SHA recomputation, raw schema, parser version, retrieval method, and secret exclusion are explicit.
- CACHE VS WORKBOOK IDENTITY = cache lookup uses source type + base ID + revision; workbook SHA is optional provenance, while stale application uses source session + workbook SHA + generation + observation key.
- EGP IDENTITY VOCABULARY = official_notify_no, revision, source_revision_id, and notify_id have one unambiguous meaning.
- M0 NETWORK CONTRACT = exact temporary harness command, three-sample maximum, concurrency one, governed rate, raw TEMP root, sanitized report path, and challenge stop are explicit.
- GUI COPY = BỔ SUNG ĐỊA ĐIỂM TỪ e-GP is the Human action label and no auto-import occurs.
- PLACEHOLDER SCAN = no unfinished marker, undefined interface, or unowned implementation path remains.
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
