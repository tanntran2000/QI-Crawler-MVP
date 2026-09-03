# QI Agent Workbench

## 1. Purpose

QI Agent Workbench is a small, manual set of governed skills and references
for orienting, routing, verifying, and handing off bounded QI-Crawler work.
It packages repeatable execution discipline without creating a second SDLC
authority or changing Crawler behavior.

## 2. What it is not

`WORKBENCH != AUTHORITY`. The canonical Human-approved Work Order, repository
Spine, and live Git state remain authoritative. The Workbench is not an
autonomous agent, scheduler, daemon, MCP service, external connector,
auto-Spine, auto-merge, or auto-release system.

## 3. Boot flow

QI Boot is read-only. It resolves checkout, role, baseline, scope, protected
paths, Spine context, and live Git before reporting `READY` or `ENTRY_HOLD`.
Role resolution is `Human explicit assignment -> approved Work Order ->
governed CURRENT`; `ROLE > MODEL NAME`.

## 4. Task Envelope

The Task Envelope is a compact subordinate view of an approved Work Order. It
preserves role, baseline, scope, exclusions, invariants, acceptance,
required skills/tools, verification, and next authority. It cannot widen or
reinterpret scope and never grants edit authority.

## 5. Skill routing

- Python behavior: QI Boot, impact map, Python Change, Evidence Check, Review Handoff.
- Bug/test failure: QI Boot, impact map, systematic debugging, TDD, Evidence Check, Review Handoff.
- Migration/schema: QI Boot, impact map, canonical migration/data-safety contract, Evidence Check, Review Handoff.
- Governance docs: QI Boot, Task Envelope, Evidence Check, Review Handoff.
- Bounded security: QI Boot, impact map, Work-Order-approved security skill/tool, Evidence Check, Review Handoff.

Routing names candidate skills only; `ROUTER != SCOPE_AUTHORITY`.

## 6. Impact, edit, and test radii

`impact_radius != edit_radius != test_radius`. CodeGraph is impact
intelligence only. If unavailable, the skill reports
`TOOL_UNAVAILABLE → governed manual fallback`; it never grants scope.
`CODEGRAPH_IMPACT != EDIT_SCOPE`.

## 7. Evidence verification

Evidence Check distinguishes baseline/negative proof, targeted local, full
local, Ruff/diff, hosted CI, unverified claim, and limitation.
`BUILDER CLAIM != MACHINE EVIDENCE`; a claim without a reproducible command,
exact object, and result remains unverified.

## 8. Reviewer handoff

Review Handoff supplies the exact checkout, `BASE_SHA`, `HEAD_SHA`, changed
paths, contract coverage, verification, deviations, unresolved findings,
Spine impact, Git state, one next action, and next authority. The Reviewer is
independent, audits the exact object/diff/evidence, and refuses to edit the
audited candidate.

## 9. Integrity lock and verifier

`skills-lock.json` records SHA-256 for the nine approved Workbench skill and
reference artifacts. `verify_lock.py` is deterministic, local, read-only,
fail-closed, and has no network, registry, auto-fix, or auto-sync behavior.
Missing artifacts, digest mismatches, and malformed manifests fail with
distinct non-zero results. `LOCK_VERIFY_PASS != HUMAN_APPROVAL` and
`MACHINE_VERIFIED != HUMAN_APPROVED`.

## 10. Evaluation corpus

`plugins/qi-agent-workbench/evals/README.md` maps six real failure candidates
to the existing executable tests. `EVALUATION_CORPUS != GOVERNANCE_AUTHORITY`
and `FAILURE_CANDIDATE != AUTOMATIC_RULE`.

## 11. Manual pilot result

The approved seven-scenario pilot reproduced every expected disposition:
`7_OF_7_PASS`, zero authority violations, zero scope widening, and zero
product mutation. The runner is:

```powershell
.venv\Scripts\python.exe -m pytest tests/agent_workbench/ -q
```

## 12. Known limitations

The Workbench is manual and repository-local. It does not install skills,
contact external registries, run background orchestration, mutate Spine
automatically, promote Failure Memory, or replace independent review and
Human A0 decisions.

## 13. Human authority boundary

`SKILL != WORK_ORDER` and `TASK_ENVELOPE != WORK_ORDER`. `FAILURE_MEMORY !=
SELF_MODIFYING_WORKBENCH`; `GROUND_TRUTH != AUTOMATIC_GOVERNANCE_RULE`.
Planner reconciliation and Human approval remain required for governance
promotion, merge, release, or product work.
