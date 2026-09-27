# WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01 rev3

## Mission and authority

- **Role:** `BUILDER_SINGLE_WRITER`; one writer, no delegation.
- **State:** Human A0 approved rev3; `AUTHORIZED → BUILDER_RUNNING`.
- **Human intent provenance:** Human A0 explicit approval relayed in Planner task `/root` on 2026-09-27. Add Codebase Memory readiness and coverage routing to the canonical QI impact skill; do not add a role or skill; graph output grants no scope or authority; this approval grants no B09 engine authority.
- **Roadmap node:** Engineering Toolbox / Plugins; supporting Cross-cutting Windows / Team Bid delivery. Product frontier remains Unified Tender Warehouse / PARTIAL. This WP does not promote product capability maturity.
- **Relevant Delta:** RD-0013 / `OPTION_C_OPERATIONAL_UPDATE` / B09 Bridge A and PR #131 reconciliation. Preserve historical WIP/HOLD records and append the later verified state.
- **Repository:** `D:\QI Technology\QI Crawler\egp-crawler-python`; expected origin `https://github.com/tanntran2000/QI-Crawler-MVP.git`.
- **Verified Builder base:** `51d2e9efc7d96334b629dc0ea97c6feb97966355`; live parent `origin/main` at entry `51463a1ba01af9cd499e0b7c7cc961c19771bbf4`. Preserve the storage-consolidation branch and commits. Create `codex/workbench-impact-readiness-01` from reconciled lineage only after entry checks pass.
- **Remote authority:** No push, PR, merge, release, or other remote mutation in this lease. A later Planner follow-up is required after Tester, Reviewer, and Planner reconciliation.

## Architecture layer contract

```text
ARCHITECTURE_LAYER_CONTRACT
PRODUCT_LANE: Engineering Toolbox / Plugins; supports Cross-cutting Windows / Team Bid delivery. No product capability promotion.
HUMAN_CONSUMER: Human and Planner use a bounded, auditable impact-routing contract.
MACHINE_CONSUMER: qi-impact-map static skill and its Markdown contract test.
DOMAIN_CORE: OUT_OF_SCOPE; no product-domain behavior.
APPLICATION_BACKEND: OUT_OF_SCOPE; no application behavior.
SOURCE_ADAPTERS: OUT_OF_SCOPE; no crawler adapter behavior.
PERSISTENCE_INFRA: OUT_OF_SCOPE; no product storage or persistence changes.
DELIVERY_ADAPTERS: OUT_OF_SCOPE; no product delivery adapter changes.
DESKTOP_FRONTEND: OUT_OF_SCOPE.
CLI: OUT_OF_SCOPE.
API: OUT_OF_SCOPE.
AI_CONSUMER: OUT_OF_SCOPE for product AI capability; skill documentation only.
ENGINEERING_TOOLS: required; canonical QI impact skill and static contract test.
DEPENDENCY_DIRECTION_CHECK: PASS; tests/docs/skill consume evidence tools, but no product-layer dependency or runtime router is introduced.
RATIONALE: This is engineering-tool support and organizational state reconciliation only.
```

## Bounded scope

Implementation allowlist:

1. `plugins/qi-agent-workbench/skills/qi-impact-map/SKILL.md`
2. `tests/agent_workbench/test_execution_skills_contract.py`
3. `docs/agent/QI_AGENT_WORKBENCH.md`
4. `plugins/qi-agent-workbench/skills-lock.json`

Governance allowlist for the approved transitions:

5. `docs/superpowers/plans/WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01.md`
6. `docs/agent_handoff/CURRENT.md`
7. `docs/agent/MASTER_ROADMAP_DELTA.md`
8. `docs/agent/PATH_REGISTRY.yaml`
9. `docs/agent/FEEDBACK_LEDGER.md`

All other edits are out of scope. Do not edit AGENTS, hooks/user config, MCP implementation, CI workflow, dependencies, skills other than the listed skill, or any B09 source/test. No Codex restart, cleanup, live DB/candidate/rollback/acceptance-root action, shortcut or AppData access.

## Readiness assessment and storage boundaries

- Read prior diagnostics first. Planner read-in references `aborted_previous_preserved`, but the raw packet was unavailable. Search only bounded relevant governed evidence/config/log locators; never inspect raw conversations or secrets and never scan the whole machine.
- Prior MCP evidence: version 0.11.0; callable; zero listed projects; `auto_index=false`, `auto_watch=true`, `watcher_enabled=true`; repository `.codebase-memory` absent. Planner shell could not observe Codex-config-declared `CBM_CACHE_DIR`/`CBM_RUNTIME_DIR`; exact MCP process cache path is UNKNOWN.
- Storage contract: `INDEX_STORAGE=TOOL_MANAGED_LOCAL_CACHE`; `REPOSITORY_GRAPH_EXPORT=DISABLED_BY_PERSISTENCE_FALSE`; `INDEX_GENERATED_REPO_BYTES=0`. `persistence=false` does not prove no tool-managed disk writes. Do not claim a total disk cap when exact cache/runtime path is unobservable.
- Check for a project with the same canonical root before any index attempt. A new attempt is allowed only after a materially changed input or a new discriminating measurement relative to the prior diagnostics. Renaming or repeating a command is insufficient. Maximum two attempts; attempt two needs a specific probe supported by attempt one diagnostics.
- If eligible, use exact repository root, `mode=fast`, `persistence=false`, stable name after duplicate-root check; maximum 15 minutes and tool-reported DB size cap 1 GiB. Record project list before/after, repository export existence, observable cache locations/bytes, tool-reported DB size, and D: free bytes. Do not exclude source/tests to force PASS. Never delete any index/cache/project; unknown or shared cache is KEEP.
- On successful indexing, smoke-check exact root, `classify_operational_update_state`, exact source snippet equality, a real caller/import relation, relevant pagination, and one batched `check_index_coverage` over all relied-on paths. Read missed/stale/partial ranges directly. Only then report `CODEBASE_MEMORY_SMOKE=PASS`, exact `VERIFIED_SCOPE`, `INDEX_MODE=fast`, and `FULL_REPOSITORY_COVERAGE=NOT_CLAIMED` only if proved.
- If not eligible or unsuccessful, report `CODEBASE_MEMORY_READINESS=HOLD_WITH_DIAGNOSIS`. Continue routing/reconciliation with CodeGraph and bounded source fallback where sufficient. Do not claim operational Codebase Memory.

## Routing contract

`qi-impact-map` owns detailed routing. For structural exploration, check Codebase Memory readiness. If `.codegraph/` exists, invoke CodeGraph first. If the CBM index is ready, use relevant graph tools without duplicating every query; batch `check_index_coverage` for all evidence files. Partial, stale, or unknown gaps require direct source fallback. Graph absence is not proof of no caller, dead code, or deletion authority. Continue with fallback when sufficient and HOLD the material claim when insufficient. Graph output never grants scope or authority.

`QI_AGENT_WORKBENCH.md` records only the principle, canonical ownership pointer, and authority boundary. Static Markdown tests prove only `STATIC_ROUTING_CONTRACT_VERIFIED`; they do not prove runtime enforcement. Update only digests that actually change in `skills-lock.json`; artifact count stays unchanged.

## B09 governance reconciliation

Verify PR #131 Git/GitHub facts when read/network access is available. Exact local required objects: merge `3ba8403f707de9710aff6b08d9df82c0d0a424c4`, PR head `ea5d84a07a34794b91fa4b42f433f3b88555264e`, code/test head `94209cb83e8b10fcdf3445ba2ba2cd0026a787b3`; all must be contained in main. Do not re-audit or edit B09 code/tests.

Reconcile CURRENT narrowly: Bridge A merged scope is the read-only state/recovery classifier plus Windows DB/WAL/SHM capture with local/hosted verification. Broader B09, Bridges B/C/D, mutation engine, startup integration, and live update remain incomplete/unproven; there is no active B09 writer or technical authority. Append/supersede Delta state without rewriting historical WIP/HOLD evidence. Record the Human routing decision in FEEDBACK with provenance.

## CI Fitness Contract

```text
CURRENT WP: WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01 rev3
CAPABILITY UNDER CHANGE: Static impact-analysis routing guidance, its static contract test, and bounded governance reconciliation.
CRITICAL RISKS: False claims of completeness/dead code; duplicated graph queries; stale/partial index reliance; graph mistaken for authority; stale B09 merged-state memory; unintentional product maturity promotion.
BASELINE GATES TO KEEP: Initial/final pytest collection integrity; targeted/full pytest; Ruff; diff and scope checks; plugin lock verification.
WP-SPECIFIC GATES REQUIRED: Discriminating RED/GREEN Markdown contract test; lock test and verifier; agent_workbench suite; full sequential pytest; exact B09 ancestry and PR state reconciliation; no new skip/xfail or collection decrease.
GATES NOT REQUIRED YET: Runtime router enforcement, B09 technical implementation, live update, product capability acceptance, or CI workflow changes.
MAX JOB RUNTIME: Targeted contract <=5 min; agent_workbench <=10 min; full sequential pytest <=30 min; repo-wide Ruff <=10 min; one infra rerun only after infra classification.
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO.
RATIONALE: Existing local contracts are sufficient; scope is static skill/docs plus governance and does not warrant CI workflow changes.
```

## Stages and acceptance

**A — Entry/baseline:** Re-resolve cwd, top-level, git-dir/common-dir, origin, branch, HEAD, origin/main, ancestry, tracked/untracked state, and writer conflict. Pass Roadmap and Role Entry gates. Record `pytest --collect-only -q` count and zero collection errors before test edit. Record exact tracked/untracked state without inspecting unknown untracked contents. Create the authorized branch only after reconciliation.

**B — Readiness:** Perform the bounded Codebase Memory assessment above. Attempts remain zero absent an eligible new diagnostic. Keep CodeGraph evidence, edit radius, and test radius distinct.

**C — Routing TDD:** Invoke `skill-creator` before skill edit. Add a discriminating RED static contract test first, observe its expected failure, then make the minimum GREEN skill change. Keep the workbench overview concise. Update only the changed lock digest.

**D — B09 governance:** Verify exact PR #131 facts where possible and local ancestry. Update only CURRENT/Delta/Feedback/registry as authorized and preserve historical records.

**Cumulative local gates:** Targeted contract test; `tests/agent_workbench/test_skills_lock.py`; full `tests/agent_workbench`; `python plugins/qi-agent-workbench/verify_lock.py`; full sequential pytest; `python -m ruff check .`; `git diff --check`; exact `git diff --name-status` and scope audit. Full pytest runs at most 30 minutes. If repo-wide Ruff fails because of preserved unrelated untracked paths, record the full exact result; supplemental scoped Ruff cannot replace it. Do not remove unrelated artifacts to pass.

Scratch is `.tmp/WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01/{run_id}/`, run ID UTC `YYYYMMDDTHHMMSSZ`; max incremental 2 GiB and 10,000 files per run. Preserve at least 10 GiB free on D:. Preserve scratch unless explicitly authorized later. No collection decrease, skip/xfail, assertion weakening, or gate reduction.

## Stop conditions

Wrong checkout/origin/baseline; loss risk to `51d2e9e`; writer conflict; out-of-scope edit required; index needs repository export, user config/hook/MCP edit, or restart; no qualifying index measurement; budget exhaustion; graph and fallback insufficient for a material claim; a required gate red without authorized resolution; B09 source/test or live mutation needed; or any destructive/cleanup action.

## Plugin applicability and evidence

| Plugin | Applicability | Purpose / expected evidence |
| --- | --- | --- |
| `qi-context-boot` | REQUIRED | Read-in and entry gates. |
| `skill-creator` | REQUIRED | Skill-change design before edit. |
| CodeGraph | REQUIRED | Structural and B09 impact discovery before edits; evidence-only. |
| `codebase-memory` | REQUIRED_ACTION: READINESS_ASSESSMENT | Use readiness contract; successful index is not required for routing pass. |
| `test-driven-development` | REQUIRED | Static contract RED then GREEN. |
| `verification-before-completion` | REQUIRED | Fresh final gates and evidence. |
| `systematic-debugging` | REQUIRED only if a new eligible index attempt fails/aborts | Diagnose that new failure; no trigger without an attempt. |
| Computer Use hook mutation | NOT_APPLICABLE | No hook mutation. |
| B09 live/runtime tools | NOT_APPLICABLE | No live/runtime action. |

Each applicable evidence record reports plugin, purpose, invocation, result, fallback, impact radius, edit radius, test radius, and limitations. If the installed `codebase-memory` skill source cannot be read, report `TOOL_SKILL_READ_UNAVAILABLE`; do not claim it was invoked. Graph and static tests are not runtime authority.

## Builder return packet

Return exact role/entry gates; base/head/branch; changed paths and semantic commits; read/dirty state; tool/plugin invocation/result/fallback/radii/limitations; prior diagnostic disposition and index attempts/changed inputs/cache/storage observations/smoke scope or HOLD diagnosis; initial/final collection; every required command, exit and result; mandatory gate state; exact B09 reconciliation; `SPINE_IMPACT`, `SPINE_TARGET_FILES`, `SPINE_SYNC_STATE`; scratch/bytes/free space; unknown untracked names preserved; remote effects (none); `ROUTING_AND_RECONCILIATION`; `CODEBASE_MEMORY_READINESS`; `OVERALL`; blockers; exactly one next action and next authority.

Overall may be `COMPLETED_WITH_OPEN_INDEX_LIMITATION` only if routing and reconciliation pass while readiness remains HOLD. Builder stops after returning to Planner `/root`; Planner assigns Tester and Reviewer. No remote action in this lease.

## Correction 01 — Tester reconciliation and verification-failure disposition

- **Authority and provenance:** Human approved this bounded docs-only correction in the Human packet relayed by Planner `/root` on 2026-09-28, after admission of Tester report `WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01-TESTER-20260927T1600Z` from `/root/workbench_impact_readiness_tester`. The approval extends this rev3 Work Order only for the three exact files below; it does not revise prior execution evidence or history.
- **Correction scope:** `docs/superpowers/plans/WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01.md`, `docs/agent/KNOWN_FAILURE_MODES.md`, and `docs/agent_handoff/CURRENT.md` only. Append this addendum, add the next sequential failure-mode record for the discovered scratch file-count breach, and replace the Builder-return handoff with the Tester-reconciled held-candidate handoff.
- **Admitted Tester evidence:** scoped static routing PASS; targeted contract 25 passed after a Tester-only scratch-parent setup correction; lock test 13 passed; Agent Workbench 65 passed; lock verifier passed with 10 artifacts; full sequential pytest remains RED; scratch file-count budget FAIL; Codebase Memory readiness HOLD; repository-wide Ruff is Builder-reported RED and was not independently log-verified by Tester. Tester disposition is scoped routing PASS / whole WP HOLD pending Planner failure-memory disposition and independent Reviewer audit.
- **Limits:** docs-only. No implementation or test edits, pytest/Ruff/CI rerun, Codebase Memory index attempt, cleanup, remote action, merge, release, B09 source/test/live action, or new technical authority is granted. Do not retrospectively increase the 10,000-file limit, rewrite prior records, call prevention implemented, or attribute all 65 failing tests to either environment or product. The remaining 276-character A3 rerun path means the known Windows path risk is not established as eliminated.
- **Handoff:** after these records are committed and checked, hand the exact code and document objects to `REVIEWER_AUDITOR` for an independent audit of the held candidate, including the verification-contract failures. Reviewer handoff is not whole-WP PASS and does not authorize remote integration.
