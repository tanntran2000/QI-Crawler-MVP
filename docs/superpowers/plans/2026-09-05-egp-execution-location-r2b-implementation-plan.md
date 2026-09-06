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

CONDITIONAL TASK: DO NOT EXECUTE unless Human A0 authorizes M0 after Planner audits this plan. This plan embeds a temporary harness specification only; it is not M0 authority.

### M0 objective and state

Observe at most three real detail responses through the official public e-GP frontend in a normal Playwright browser session. The approved candidates are IB2600488839:00, IB2600498410:00, and IB2600489267:00; they are candidates, not assertions that a province/city value exists.

    R2B_SPEC = HUMAN_APPROVED_FINAL
    R2B_PLAN = FEATURE_BRANCH_PLAN
    R2B_M0 = NOT_EXECUTED
    R2B_M1_TO_M6 = NOT_IMPLEMENTED

M0 uses one browser context, sequential detail acquisition, and min(configured_rate, 12) requests per minute. Existing browser timeout remains authoritative. It may use neither a direct tokenless API replay nor a CAPTCHA solver.

### M0 exact execution method

Create the temporary script below only under a unique directory outside the repository. A later Human/Planner M0 Work Order must supply the exact official frontend navigation URLs and the exact spike-proven detail request contract as JSON. The contract has four fields only: origin, method, route, and identity_field.

Use PowerShell only after M0 authorization:

    $M0Root = Join-Path $env:TEMP 'qi-r2b-m0'
    $RawRoot = Join-Path $M0Root 'raw'
    $Script = Join-Path $M0Root 'capture_egp_location.py'
    $DetailContract = $env:QI_R2B_M0_DETAIL_REQUEST_CONTRACT
    & .\.venv\Scripts\python.exe $Script --config .\config.yaml --detail-url "IB2600488839:00=$env:QI_R2B_M0_DETAIL_URL_1" --detail-url "IB2600498410:00=$env:QI_R2B_M0_DETAIL_URL_2" --detail-url "IB2600489267:00=$env:QI_R2B_M0_DETAIL_URL_3" --detail-contract $DetailContract --max-samples 3 --concurrency 1 --raw-root $RawRoot --report .\docs\agent_handoff\evidence\R2B-M0-egp-location-response.md

The later Work Order must copy the descriptor verbatim from approved spike evidence. The harness does not construct a source-to-URL mapping from source id or revision. It rejects a non-HTTPS/non-allowed contract origin, validates the official navigation URL against existing access policy and robots policy, and persists neither query strings, request bodies, headers, cookies, nor credentials.

The harness is side-effect-free before browser start: it parses YAML directly and calls AppConfig.model_validate, never load_config, so it does not create configured application storage directories. It hard-holds before browser start unless both obey_robots_txt and stop_on_captcha are true. It also rejects any raw-root outside TEMP.

The complete temporary script is:

    """Temporary, authorization-gated R2B M0 browser evidence harness.

    This file belongs under %TEMP% only.  It is deliberately read-only with
    respect to application state; raw response bytes are permitted only after a
    secret scan and only under a unique TEMP root.
    """
    from __future__ import annotations

    import argparse
    import asyncio
    import hashlib
    import json
    import re
    from dataclasses import dataclass
    from datetime import UTC, datetime
    from pathlib import Path
    from typing import Any
    from urllib.parse import urlsplit, urlunsplit

    import yaml

    from qi_crawler.config import AppConfig

    SUPPORTED_CONTAINERS = ("bidpBidLocationList", "lsBidpBidLocationDTO")
    CHALLENGE_STATUSES = {401, 403, 429}
    SECRET_KEYS = {
        "password", "passphrase", "authorization", "cookie", "setcookie",
        "accesstoken", "refreshtoken", "clientsecret", "sessiontoken",
        "csrftoken", "grecaptcharesponse", "recaptcharesponse", "recaptchatoken", "captchatoken",
    }
    BEARER = re.compile(r"\bbearer\s+[a-z0-9._~+/=-]{8,}", re.I)
    URL = re.compile(r"https?://[^\s'\"<>]+", re.I)


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


    @dataclass(frozen=True)
    class DetailRequestContract:
        origin: str
        method: str
        route: str
        identity_field: str


    SAMPLES = (
        M0Sample("IB2600488839", "00", "ca1aadd6-edbc-4912-81fa-dccba9712245"),
        M0Sample("IB2600498410", "00", "9446dc1c-3687-4fa5-a73f-67b1b9cc75cf"),
        M0Sample("IB2600489267", "00", "9716b9c7-e446-4e0a-89fc-27cb244b3eac"),
    )


    def pointer_join(parent: str, token: str | int) -> str:
        escaped = str(token).replace("~", "~0").replace("/", "~1")
        return f"/{escaped}" if parent == "/" else f"{parent}/{escaped}"


    def walk(value: Any, path: str = "/"):
        if isinstance(value, dict):
            yield path, value
            for key, child in value.items():
                yield from walk(child, pointer_join(path, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from walk(child, pointer_join(path, index))


    def safe_url(value: str) -> str:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))


    def sanitize_error(error: BaseException | str) -> str:
        message = str(error)
        message = URL.sub(lambda match: safe_url(match.group(0)), message)
        return BEARER.sub("Bearer [REDACTED]", message)


    def detail_status(status: int) -> str:
        if 200 <= status < 300:
            return "SUCCESS"
        if status in CHALLENGE_STATUSES:
            return "ACCESS_CHALLENGE"
        return "RETRIEVAL_FAILED"


    def _normal_key(value: str) -> str:
        return value.casefold().replace("-", "").replace("_", "")


    def contains_secret(value: Any, key: str | None = None) -> bool:
        if key and _normal_key(key) in SECRET_KEYS:
            return True
        if isinstance(value, dict):
            return any(contains_secret(child, str(child_key)) for child_key, child in value.items())
        if isinstance(value, list):
            return any(contains_secret(child) for child in value)
        return isinstance(value, str) and bool(BEARER.search(value))


    def persist_raw_if_secret_free(raw_path: Path, body: bytes) -> tuple[str, bool]:
        digest = hashlib.sha256(body).hexdigest()
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return digest, False
        if contains_secret(payload):
            return digest, False
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(body)
        return digest, True


    def raw_root_inside_temp(raw_root: Path, temp_root: Path | None = None) -> bool:
        root = raw_root.resolve()
        temp = (temp_root or Path(__import__("os").environ["TEMP"])).resolve()
        try:
            root.relative_to(temp)
            return True
        except ValueError:
            return False


    def read_config_side_effect_free(path: Path) -> AppConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return AppConfig.model_validate(payload)


    def enforce_access_policy(config: AppConfig) -> None:
        if not config.compliance.obey_robots_txt or not config.compliance.stop_on_captcha:
            raise RuntimeError("M0_ACCESS_POLICY_HOLD")


    def enforce_official_origin(config: AppConfig, contract: DetailRequestContract) -> None:
        parsed = urlsplit(contract.origin)
        if parsed.scheme != "https" or not parsed.hostname:
            raise RuntimeError("DETAIL_CONTRACT_ORIGIN_INVALID")
        if parsed.hostname.casefold() not in {domain.casefold() for domain in config.allowed_domains}:
            raise RuntimeError("DETAIL_CONTRACT_ORIGIN_NOT_ALLOWED")


    def _text(dto: dict[str, Any], key: str) -> str | None:
        value = dto.get(key)
        return value.strip() if isinstance(value, str) and value.strip() else None


    def _evidence(location_path: str, values: list[Any]) -> list[dict[str, str | None]]:
        evidence: list[dict[str, str | None]] = []
        for index, dto in enumerate(values):
            if not isinstance(dto, dict):
                raise ValueError("UNSUPPORTED_DTO_SHAPE")
            province = _text(dto, "provName")
            district = _text(dto, "districtName")
            ward = _text(dto, "wardName")
            if province or district or ward:
                evidence.append(
                    {
                        "path": pointer_join(location_path, index),
                        "province_city": province,
                        "district": district,
                        "ward": ward,
                    }
                )
        return evidence


    def supported_location_path(payload: Any) -> tuple[str | None, dict[str, Any] | None, str]:
        objects: list[tuple[str, dict[str, Any], list[tuple[str, list[Any]]]]] = []
        for detail_path, node in walk(payload):
            if not isinstance(node, dict):
                continue
            found: list[tuple[str, list[Any]]] = []
            for name in SUPPORTED_CONTAINERS:
                if name in node:
                    if not isinstance(node[name], list):
                        return detail_path, None, "SCHEMA_UNSUPPORTED"
                    found.append((name, node[name]))
            if found:
                objects.append((detail_path, node, found))
        if len(objects) != 1:
            return None, None, "DETAIL_OBJECT_AMBIGUOUS" if objects else "SCHEMA_UNSUPPORTED"
        detail_path, _, containers = objects[0]
        evaluated = []
        for name, values in containers:
            location_path = pointer_join(detail_path, name)
            try:
                evidence = _evidence(location_path, values)
            except ValueError:
                return detail_path, None, "SCHEMA_UNSUPPORTED"
            evaluated.append((name, location_path, evidence))
        usable = [item for item in evaluated if item[2]]
        if not usable:
            primary = next(
                (item for item in evaluated if item[0] == "bidpBidLocationList"), evaluated[0]
            )
            return detail_path, {
                "location_path": primary[1],
                "location_dtos": [],
                "selected_container": primary[0],
                "container_resolution": "SUPPORTED_BUT_EMPTY",
            }, "SOURCE_HAS_NO_LOCATION"
        if len(usable) == 1:
            name, location_path, evidence = usable[0]
            return detail_path, {
                "location_path": location_path,
                "location_dtos": evidence,
                "selected_container": name,
                "container_resolution": "SINGLE_USABLE"
                if len(evaluated) == 1 else "EMPTY_CONTAINER_IGNORED",
            }, "PROVEN"
        first, second = usable
        def semantic_values(item):
            return [
                (dto["province_city"], dto["district"], dto["ward"])
                for dto in item[2]
            ]
        if semantic_values(first) != semantic_values(second):
            return detail_path, None, "CONFLICTING_LOCATION_CONTAINERS"
        primary = next(item for item in evaluated if item[0] == "bidpBidLocationList") if any(
            item[0] == "bidpBidLocationList" for item in evaluated
        ) else first
        return detail_path, {
            "location_path": primary[1],
            "location_dtos": primary[2],
            "selected_container": primary[0],
            "container_resolution": "MIRRORED_DETERMINISTIC_PRIMARY",
        }, "PROVEN"


    def _parsed_payload(request: Any) -> dict[str, Any] | None:
        raw = getattr(request, "post_data", None)
        if not isinstance(raw, str):
            return None
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return result if isinstance(result, dict) else None


    def request_binds(request: Any, sample: M0Sample, contract: DetailRequestContract) -> bool:
        parsed = urlsplit(str(getattr(request, "url", "")))
        actual_origin = f"{parsed.scheme}://{parsed.netloc}".casefold()
        expected_origin = contract.origin.rstrip("/").casefold()
        if actual_origin != expected_origin:
            return False
        if str(getattr(request, "method", "")).upper() != contract.method.upper():
            return False
        if parsed.path != contract.route:
            return False
        payload = _parsed_payload(request)
        return bool(payload and payload.get(contract.identity_field) == sample.expected_notify_id)


    async def visible_runtime_challenge(page: Any) -> bool:
        """Detect only visible runtime gates; static script references are not a challenge."""
        url = str(getattr(page, "url", "")).casefold()
        if any(token in url for token in ("/login", "/sign-in", "/dang-nhap")):
            return True
        locator = getattr(page, "locator", None)
        if locator is not None:
            for selector in (
                "input[type='password']",
                "iframe[src*='recaptcha']",
                "[data-sitekey]",
                "[class*='captcha']",
            ):
                try:
                    if await locator(selector).count():
                        return True
                except Exception:
                    pass
        text_content = getattr(page, "visible_text", None)
        if callable(text_content):
            text = (await text_content()).casefold()
            return any(marker in text for marker in (
                "access denied", "human verification", "verify you are human", "xác minh", "truy cập bị từ chối",
            ))
        return False


    def remaining_seconds(deadline_at: float) -> float:
        return deadline_at - asyncio.get_running_loop().time()


    async def wait_for_unique_response(
        queue: asyncio.Queue[Any], deadline_at: float, quiet_seconds: float, page: Any
    ) -> tuple[Any | None, str]:
        """Use one deadline for response, challenge polling, and uniqueness quiet window."""
        selected = None
        while selected is None:
            if await visible_runtime_challenge(page):
                return None, "ACCESS_CHALLENGE"
            remaining = remaining_seconds(deadline_at)
            if remaining <= 0:
                return None, "DETAIL_RESPONSE_TIMEOUT"
            try:
                selected = await asyncio.wait_for(queue.get(), timeout=min(remaining, 0.10))
            except TimeoutError:
                continue
        quiet_deadline = asyncio.get_running_loop().time() + quiet_seconds
        if quiet_deadline > deadline_at:
            return None, "UNIQUENESS_NOT_PROVEN"
        while True:
            if await visible_runtime_challenge(page):
                return None, "ACCESS_CHALLENGE"
            remaining = min(remaining_seconds(deadline_at), quiet_deadline - asyncio.get_running_loop().time())
            if remaining <= 0:
                return selected, "UNIQUE"
            try:
                await asyncio.wait_for(queue.get(), timeout=min(remaining, 0.10))
            except TimeoutError:
                continue
            return None, "INTEGRITY_MISMATCH"


    async def capture_exact_response(
        page: Any,
        navigate,
        sample: M0Sample,
        contract: DetailRequestContract,
        deadline_at: float,
        quiet_seconds: float,
    ) -> tuple[Any | None, str]:
        queue: asyncio.Queue[Any] = asyncio.Queue()

        def listener(response: Any) -> None:
            if request_binds(response.request, sample, contract):
                queue.put_nowait(response)

        page.on("response", listener)
        try:
            navigation = await asyncio.wait_for(navigate(), timeout=max(remaining_seconds(deadline_at), 0))
            if navigation is None:
                return None, "RETRIEVAL_FAILED"
            navigation_state = detail_status(int(getattr(navigation, "status", 0)))
            if navigation_state != "SUCCESS":
                return None, navigation_state
            if await visible_runtime_challenge(page):
                return None, "ACCESS_CHALLENGE"
            if remaining_seconds(deadline_at) <= 0:
                return None, "DETAIL_RESPONSE_TIMEOUT"
            return await wait_for_unique_response(queue, deadline_at, quiet_seconds, page)
        except TimeoutError:
            return None, "RETRIEVAL_FAILED"
        finally:
            page.off("response", listener)


    def base_report() -> dict[str, Any]:
        return {
            "samples": [],
            "terminal_outcome": "NOT_STARTED",
            "REAL_RESPONSE_ENVELOPE": "NOT_PROVEN",
            "REAL_DETAIL_OBJECT_PATH": "NOT_PROVEN",
            "REAL_IDENTITY_BINDING": "NOT_PROVEN",
            "REAL_NOTIFYNO_REVISION_UUID_RELATION": "NOT_PROVEN",
            "REAL_LOCATION_DTO_PATH": "NOT_PROVEN",
            "REAL_SEMANTIC_LOCATION_VALUE": "NOT_PROVEN",
            "M0_REAL_PROVINCE_CITY_VALUE": "NOT_PROVEN",
            "M0_IDENTITY_BINDING": "FAIL",
            "M0_DETAIL_OBJECT_PATH": "FAIL",
            "M0_LOCATION_DTO_PATH": "FAIL",
            "M0_ACCESS_POLICY": "NOT_PROVEN",
            "M0_RAW_SECRET_EXCLUSION": "NOT_PROVEN",
            "M0_PROVINCE_GATE": "FAIL",
        }


    def exit_zero_requires_all_gates(report: dict[str, Any]) -> bool:
        required = (
            "M0_IDENTITY_BINDING", "M0_DETAIL_OBJECT_PATH", "M0_LOCATION_DTO_PATH",
            "M0_ACCESS_POLICY", "M0_RAW_SECRET_EXCLUSION", "M0_PROVINCE_GATE",
        )
        return all(report.get(key) == "PASS" for key in required)


    def apply_sample_outcome(report: dict[str, Any], item: dict[str, Any]) -> None:
        report["samples"].append(item)
        if item.get("M0_RAW_SECRET_EXCLUSION") == "HOLD":
            report["M0_RAW_SECRET_EXCLUSION"] = "HOLD"


    async def one(
        fetcher: Any, limiter: Any, url: str, sample: M0Sample, contract: DetailRequestContract,
        raw_root: Path, deadline_seconds: float, quiet_seconds: float,
    ) -> dict[str, Any]:
        await fetcher.ensure_browser_access_allowed(url)
        await limiter.wait(url)
        deadline_at = asyncio.get_running_loop().time() + deadline_seconds
        page = await fetcher.new_page()
        try:
            response, capture_state = await capture_exact_response(
                page,
                lambda: page.goto(url, wait_until="domcontentloaded"),
                sample,
                contract,
                deadline_at,
                quiet_seconds,
            )
            if capture_state != "UNIQUE":
                return {"sample": sample.key, "outcome": capture_state, "REAL_IDENTITY_BINDING": "NOT_PROVEN"}
            status_state = detail_status(response.status)
            binding = {
                "method": contract.method.upper(),
                "sanitized_route": contract.route,
                "expected_notify_id": sample.expected_notify_id,
                "binding_result": "PASS",
            }
            base = {
                "sample": sample.key,
                "official_notify_no": sample.source_id,
                "revision": sample.revision,
                "source_revision_id": sample.source_revision_id,
                "notify_id": sample.expected_notify_id,
                "exact_request_binding": binding,
                "response_status": response.status,
                "sanitized_response_route": safe_url(response.url),
                "captured_at": datetime.now(UTC).isoformat(),
            }
            if status_state == "ACCESS_CHALLENGE":
                return base | {"outcome": "ACCESS_CHALLENGE", "REAL_IDENTITY_BINDING": "NOT_PROVEN"}
            if status_state != "SUCCESS":
                return base | {"outcome": "RETRIEVAL_FAILED", "REAL_IDENTITY_BINDING": "NOT_PROVEN"}
            remaining = remaining_seconds(deadline_at)
            if remaining <= 0:
                return base | {"outcome": "DETAIL_BODY_TIMEOUT", "REAL_IDENTITY_BINDING": "NOT_PROVEN"}
            try:
                body = await asyncio.wait_for(response.body(), timeout=remaining)
            except TimeoutError:
                return base | {"outcome": "DETAIL_BODY_TIMEOUT", "REAL_IDENTITY_BINDING": "NOT_PROVEN"}
            digest = hashlib.sha256(body).hexdigest()
            try:
                payload = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                return base | {
                    "outcome": "PARSER_FAILED",
                    "RAW_RESPONSE_SHA256": digest,
                    "stop_reason": sanitize_error(error),
                }
            raw_path = raw_root / f"{sample.source_id}-{sample.revision}-{digest}.json"
            persisted_digest, raw_written = persist_raw_if_secret_free(raw_path, body)
            if not raw_written:
                return base | {
                    "outcome": "RAW_SECRET_HOLD",
                    "RAW_RESPONSE_SHA256": persisted_digest,
                    "M0_RAW_SECRET_EXCLUSION": "HOLD",
                }
            detail_path, location, location_state = supported_location_path(payload)
            envelope = {
                "root_type": type(payload).__name__,
                "root_keys": sorted(payload) if isinstance(payload, dict) else [],
            }
            base |= {
                "REAL_RESPONSE_ENVELOPE": envelope,
                "REAL_DETAIL_OBJECT_PATH": detail_path or "NOT_PROVEN",
                "REAL_IDENTITY_BINDING": "EXACT_REQUEST_CONTRACT",
                "RAW_RESPONSE_SHA256": digest,
                "raw_response_written": True,
                "M0_RAW_SECRET_EXCLUSION": "PASS",
            }
            if location_state == "SOURCE_HAS_NO_LOCATION":
                return base | {
                    "outcome": "SOURCE_HAS_NO_LOCATION",
                    "location_state": location_state,
                    "REAL_LOCATION_DTO_PATH": location["location_path"],
                    "REAL_SEMANTIC_LOCATION_VALUE": "NOT_PROVEN",
                    "location_dtos": [],
                    "selected_container": location["selected_container"],
                    "container_resolution": location["container_resolution"],
                }
            if location_state != "PROVEN":
                return base | {
                    "outcome": location_state,
                    "location_state": location_state,
                    "REAL_LOCATION_DTO_PATH": "NOT_PROVEN",
                    "REAL_SEMANTIC_LOCATION_VALUE": "NOT_PROVEN",
                }
            dtos = location["location_dtos"]
            confirmed = [dto for dto in dtos if dto["province_city"]]
            return base | {
                "outcome": "PROVEN" if confirmed else "PARTIAL",
                "REAL_LOCATION_DTO_PATH": location["location_path"],
                "REAL_SEMANTIC_LOCATION_VALUE": confirmed[0]["province_city"] if confirmed else "NOT_PROVEN",
                "location_dtos": dtos,
                "selected_container": location["selected_container"],
                "container_resolution": location["container_resolution"],
            }
        finally:
            await page.close()


    def write_terminal_report(report_path: Path, report: dict[str, Any]) -> None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


    def parse_contract(value: str) -> DetailRequestContract:
        data = json.loads(value)
        required = ("origin", "method", "route", "identity_field")
        if not isinstance(data, dict) or any(not isinstance(data.get(key), str) or not data[key] for key in required):
            raise ValueError("detail contract must contain origin, method, route, identity_field")
        return DetailRequestContract(**{key: data[key] for key in required})


    async def run(
        args: argparse.Namespace,
        *,
        fetcher_factory: Any | None = None,
        limiter_factory: Any | None = None,
        config_loader=read_config_side_effect_free,
        sample_runner=one,
    ) -> int:
        report = base_report()
        fetcher = None
        try:
            if args.max_samples != 3 or args.concurrency != 1 or len(args.detail_url) != 3:
                raise ValueError("M0 is exactly three approved sequential samples and concurrency one")
            raw_root = args.raw_root.resolve()
            if not raw_root_inside_temp(raw_root):
                report["terminal_outcome"] = "FAILED_BEFORE_START"
                report["stop_reason"] = "RAW_ROOT_OUTSIDE_TEMP"
                raise RuntimeError("RAW_ROOT_OUTSIDE_TEMP")
            urls = dict(value.split("=", 1) for value in args.detail_url)
            if set(urls) != {sample.key for sample in SAMPLES}:
                raise ValueError("each exact sample requires a Work-Order-supplied official detail URL")
            contract = parse_contract(args.detail_contract)
            config = config_loader(args.config)
            enforce_access_policy(config)
            enforce_official_origin(config, contract)
            report["M0_ACCESS_POLICY"] = "PASS"
            from qi_crawler.compliance import AccessDenied, DomainRateLimiter
            if fetcher_factory is None:
                from qi_crawler.browser import BrowserFetcher
                fetcher_factory = BrowserFetcher
            fetcher = fetcher_factory(config)
            await fetcher.start(headed=True)
            deadline = config.crawl.browser_timeout_seconds
            limiter = (limiter_factory or DomainRateLimiter)(min(config.crawl.requests_per_minute, 12))
            for sample in SAMPLES:
                try:
                    item = await sample_runner(fetcher, limiter, urls[sample.key], sample, contract, raw_root, deadline, 0.25)
                except AccessDenied as error:
                    report["samples"].append({"sample": sample.key, "outcome": "ACCESS_CHALLENGE"})
                    report["M0_ACCESS_POLICY"] = "HOLD"
                    report["stop_reason"] = sanitize_error(error)
                    break
                except Exception as error:
                    report["samples"].append({"sample": sample.key, "outcome": "RETRIEVAL_FAILED"})
                    report["stop_reason"] = sanitize_error(error)
                    continue
                apply_sample_outcome(report, item)
                if item["outcome"] == "ACCESS_CHALLENGE":
                    report["M0_ACCESS_POLICY"] = "HOLD"
                    report["stop_reason"] = "ACCESS_CHALLENGE"
                    break
                if item["outcome"] in {
                    "INTEGRITY_MISMATCH", "DETAIL_OBJECT_AMBIGUOUS",
                    "CONFLICTING_LOCATION_CONTAINERS", "RAW_SECRET_HOLD",
                }:
                    report["stop_reason"] = item["outcome"]
                    break
                if item["outcome"] == "PROVEN":
                    report.update(
                        {
                            "REAL_RESPONSE_ENVELOPE": item["REAL_RESPONSE_ENVELOPE"],
                            "REAL_DETAIL_OBJECT_PATH": item["REAL_DETAIL_OBJECT_PATH"],
                            "REAL_IDENTITY_BINDING": item["REAL_IDENTITY_BINDING"],
                            "REAL_LOCATION_DTO_PATH": item["REAL_LOCATION_DTO_PATH"],
                            "REAL_SEMANTIC_LOCATION_VALUE": item["REAL_SEMANTIC_LOCATION_VALUE"],
                            "REAL_NOTIFYNO_REVISION_UUID_RELATION": {
                                "official_notify_no": sample.source_id,
                                "revision": sample.revision,
                                "source_revision_id": sample.source_revision_id,
                                "notify_id": sample.expected_notify_id,
                            },
                            "M0_REAL_PROVINCE_CITY_VALUE": "PROVEN",
                            "M0_IDENTITY_BINDING": "PASS",
                            "M0_DETAIL_OBJECT_PATH": "PASS",
                            "M0_LOCATION_DTO_PATH": "PASS",
                            "M0_RAW_SECRET_EXCLUSION": item["M0_RAW_SECRET_EXCLUSION"],
                            "M0_PROVINCE_GATE": "PASS",
                        }
                    )
                    break
            else:
                report["stop_reason"] = "CANDIDATES_EXHAUSTED"
            report["terminal_outcome"] = "COMPLETED"
        except Exception as error:
            report["terminal_outcome"] = report["terminal_outcome"] if report["terminal_outcome"] != "NOT_STARTED" else "FAILED_BEFORE_START"
            report["stop_reason"] = sanitize_error(error)
        finally:
            if fetcher is not None:
                try:
                    await fetcher.close()
                except Exception as error:
                    report["terminal_outcome"] = "CLEANUP_FAILED"
                    report["stop_reason"] = sanitize_error(error)
                    report["cleanup_failed"] = True
            try:
                write_terminal_report(args.report, report)
            except Exception as error:
                report["report_write_failed"] = True
                report["terminal_outcome"] = "REPORT_WRITE_FAILED"
                report["stop_reason"] = sanitize_error(error)
                return 2
        return 0 if exit_zero_requires_all_gates(report) and not report.get("cleanup_failed") else 2


    def main() -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", required=True, type=Path)
        parser.add_argument("--detail-url", action="append", required=True)
        parser.add_argument("--detail-contract", required=True)
        parser.add_argument("--max-samples", required=True, type=int)
        parser.add_argument("--concurrency", required=True, type=int)
        parser.add_argument("--raw-root", required=True, type=Path)
        parser.add_argument("--report", required=True, type=Path)
        raise SystemExit(asyncio.run(run(parser.parse_args())))


    if __name__ == "__main__":
        main()
### M0 procedure

1. Human/Planner supplies the exact official frontend navigation URLs and spike-proven JSON detail-request contract for this process only. No route, API endpoint, identity field, or source-to-URL mapping may be inferred by the harness.
2. The harness validates its temporary raw-root and configuration before starting a browser. It then validates the allowed HTTPS origin, official navigation URL, and robots policy before navigation.
3. Register the exact-response listener before navigation. A response qualifies only when its request has the supplied official origin, exact method, exact route, and parsed payload identity field equal to the candidate UUID. A UUID in an unrelated field, query text, or arbitrary JSON string does not bind identity.
4. After rate limiting, one active browser-timeout deadline covers frontend navigation, visible-runtime challenge checks, exact-response wait, the bounded uniqueness quiet window, and response-body read. A missing navigation response is RETRIEVAL_FAILED/NOT_PROVEN; a frontend 401/403/429 is ACCESS_CHALLENGE and stops the whole batch immediately; another frontend 4xx/5xx is RETRIEVAL_FAILED and may advance. A late exact response is valid only inside that same deadline. If the quiet window or body cannot complete inside it, the candidate is non-proving (UNIQUENESS_NOT_PROVEN or DETAIL_BODY_TIMEOUT). A second exact response during the quiet window is INTEGRITY_MISMATCH. Always remove the listener and close the page.
5. Check a visible runtime access gate after navigation and while awaiting an exact response. Login/sign-in redirects, a visible password input or challenge widget, and visible access-denied/human-verification text are ACCESS_CHALLENGE; static grecaptcha/recaptcha script references alone are not. Only a 2xx selected detail response is eligible for proof. HTTP 401/403/429 is ACCESS_CHALLENGE and stops M0. Other 4xx/5xx responses are RETRIEVAL_FAILED, are recorded, and may advance to the next bounded candidate; they never prove a REAL field.
6. Compute a raw SHA-256 in memory, parse and scan explicit credential-bearing keys (including normalized grecaptcharesponse, recaptcharesponse, recaptchatoken, and captchatoken) and Bearer material, then write exact raw bytes only after that scan passes and only under the temporary raw-root. On suspicious content, write nothing and set M0_RAW_SECRET_EXCLUSION = HOLD. All errors and every reported route are sanitized to omit credentials, query, and fragment.
7. Bind exactly one detail object. Preserve every meaningful location DTO. A missing or malformed supported container is SCHEMA_UNSUPPORTED and may advance; multiple detail objects are DETAIL_OBJECT_AMBIGUOUS and hold; conflicting nonempty containers are CONFLICTING_LOCATION_CONTAINERS and hold. Within one object, select semantically identical mirrors deterministically, select the usable one when the other is empty, and never merge conflicts. A structurally supported empty container, or structurally valid DTOs whose province/district/ward are all empty, is SOURCE_HAS_NO_LOCATION: preserve detail/container paths, never prove a province, and continue to the next candidate.
8. A province/city gate considers only DTOs with meaningful provName, but partial district/ward DTOs remain in location_dtos even when confirmed DTOs exist. SOURCE_HAS_NO_LOCATION after every candidate finishes with M0_PROVINCE_GATE = FAIL. M0 never auto-authorizes M1–M6.

### M0 proof and stop contract

The `run()` lifecycle, not a detached helper, emits the terminal report for config failure, browser-start failure, page failure, response-body failure, timeout, parser failure, cleanup failure, or normal completion. It attempts BrowserFetcher.close() whenever initialization reached a closable state, records a sanitized CLEANUP_FAILED result and returns nonzero if close fails, then writes the report. If report writing itself fails, it returns nonzero and makes no durability claim.

The report records only source/revision identifiers, method, sanitized route, expected UUID, binding result, status, raw SHA-256, location evidence, and sanitized terminal reason. A zero exit requires every required proof gate to be PASS; a lock or verifier result never replaces Human approval.

    M0_REAL_PROVINCE_CITY_VALUE = PROVEN only after a 2xx, exact-bound, secret-clean response
    M0_IDENTITY_BINDING = PASS only after exact contract binding
    M0_DETAIL_OBJECT_PATH = PASS only after one unambiguous detail object
    M0_LOCATION_DTO_PATH = PASS only after a supported, usable location container
    M0_ACCESS_POLICY = PASS only after side-effect-free config and access-policy gates
    M0_RAW_SECRET_EXCLUSION = PASS only after selected bytes pass the explicit scan
    M0_PROVINCE_GATE = PASS only when a direct meaningful province/city exists

ACCESS_CHALLENGE, identity mismatch, duplicate matching response, ambiguous detail objects, conflicting containers, unsafe raw content, robots uncertainty, or access-control interruption stop M0 without bypass. SCHEMA_UNSUPPORTED, SOURCE_HAS_NO_LOCATION, retrieval-failed, parser-failed, and bounded body/uniqueness failures record bounded evidence and may continue. Missing direct province/city after all candidates yields M0_REAL_PROVINCE_CITY_VALUE = NOT_PROVEN and M0_PROVINCE_GATE = FAIL, then stops for Planner. The mandatory sequence remains M0 evidence → Planner audit → Human decision; M0 does not auto-authorize M1–M6.

### M0 radius and evidence

    IMPACT_RADIUS = BrowserFetcher, AccessPolicy, official e-GP frontend response envelope, exact request binding, location DTOs, terminal report.
    EDIT_RADIUS = temporary raw responses and the one sanitized M0 report after explicit authorization.
    TEST_RADIUS = temporary fake response/request harness tests only; no production test changes.

Commit durable evidence only if a later Planner order authorizes it: docs(evidence): record R2B M0 browser proof.

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
