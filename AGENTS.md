# QI-Crawler repository guardrails

## Repository map

- Production: `src/qi_crawler/`; tests: `tests/`; migrations: `alembic/versions/`
- Packaging: `packaging/`; scripts: `scripts/`; docs: `docs/`; templates: `templates/`
- Important root helpers: `evaluate_qi_crawler.py`, `pyproject.toml`, `alembic.ini`, tracked build/release scripts.
- Generated only: `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `build/`, `dist/`, `release_staging/`, approved `.tmp/` children.

## Workspace policy

- Use one canonical checkout: `egp-crawler-python`.
- Work in place on one active short-lived feature branch at a time; never create any Git worktree anywhere, including sibling or project-local/nested `.worktrees/` or `worktrees/`, sibling clones, or WP-named folders.
- After an approved merge, return to `main`, fast-forward from `origin/main`, and delete the merged local branch.

## Release and version governance

Any change affecting a user-visible feature, GUI, packaged runtime, database
compatibility, installer behavior, or Team Bid workflow requires a
**RELEASE IMPACT ASSESSMENT**. A Team Bid release is one release, one version,
one Git SHA, and one build identity; the canonical app/package version, GUI,
installer, `BUILD_INFO`, and release manifest must agree. A mismatch is a
release-gate failure.

Use semantic versioning: PATCH for bug or stability corrections without new
capability, MINOR for new capability or significant GUI/workflow change, and
MAJOR for a breaking user/data/runtime contract. Docs-only, test-only,
CI-only, and internal refactor commits without user-visible effect do not
automatically require a version bump. Human authority approves the official
Team Bid release/publish. Git main/new commit and `CHANGELOG.md` are not, by
themselves, a Team Bid release.

Every user-visible merged change updates `CHANGELOG.md` or `Unreleased` when
appropriate. Every approved Team Bid release records the canonical application
version, exact Git SHA, immutable annotated tag `vX.Y.Z`, GitHub Release
`vX.Y.Z`, release notes, installer/EXE hashes, and `BUILD_INFO` or a release
manifest. A Git commit or `CHANGELOG.md` entry alone is not a release.
Historical tags and releases must never be silently moved.

## Safety rules

1. Unknown is **KEEP**. Never delete a tracked file without the user's exact request.
2. Never infer generated status from a `.py`, `.ps1`, `.toml`, `.ini`, `.md`, or migration filename.
3. Before deletion: check `git status`, `git ls-files`, reproducibility, and an explicit allowlist. Never recursively delete the repository root.
4. Never delete `src/`, `tests/`, `alembic/`, `packaging/`, `scripts/`, `docs/`, `templates/`, fixtures, or tracked root helpers.
5. Use `scripts/clean_dev.ps1 -WhatIf` first. Permission/ACL errors must warn and skip; never take ownership or elevate.
6. Small task: inspect only relevant source/tests. Avoid unrelated modules and speculative refactors; stop if scope expands unexpectedly.
7. Validation: targeted `python -m pytest` → `python -m pytest` → `ruff check .` → `git diff --check` → `git diff --name-status`.
8. A task fails on unexpected source deletion. Never commit/push unless explicitly asked; never alter stable tags.

## Engineering governance laws

1. **LAW 1 — PLAN-FIRST**: Planner creates the design/work-order; Planner does not code.
2. **LAW 2 — SEPARATION OF RESPONSIBILITIES**: Planner -> Independent Reviewer/Auditor -> Single Writer -> Machine Verifier -> Human Merge Approver.
3. **LAW 3 — SYSTEMIC LESSONS ONLY**: Record durable architectural lessons; do not pollute lessons with minor typos.
4. **LAW 4 — PROOF-GATED DEFINITION OF DONE**: Verify against the explicit Work Order contract; never claim unqualified perfection.
5. **LAW 5 — MINIMAL COMPLETE FIX**: Fix at root cause with the smallest complete change; no masking or speculative refactoring.
6. **LAW 6 — BOUNDED AUTONOMY**: Single Writer operates strictly inside the Work Order scope; stop immediately on blocker.
7. **LAW 7 — SINGLE WRITER**: Only ONE agent writes production/test code in any micro-WP.
8. **LAW 8 — ADAPTIVE VERIFICATION**: Before judging implementation correctness, the Reviewer must verify that the current CI/test contract matches the current Work Package's capability under change, risk profile, acceptance criteria, and maturity stage.

9. **LAW 9 — HANDOFF READ-IN & CONTINUITY**: `READ → VERIFY → ENTRY REVIEW → ONE APPROVAL → EXECUTE MANY`. Approval leases a bounded Work Package, not individual commands. Re-approval is required only when scope, baseline, handoff authority, writer, or a material blocker changes.

For a **NEW AGENT**, **NEW PARENT WP**, **WRITER TAKEOVER**,
**PLANNER/REVIEWER TAKEOVER**, or **MATERIAL ARCHITECTURE CHANGE**, the agent
must fully read `docs/agent/MASTER_ROADMAP.md` before declaring READY. Future
material Work Orders must include the roadmap's `ARCHITECTURE_LAYER_CONTRACT`
in addition to the CI Fitness Contract. The roadmap classifies the Product
House and its layers; the Work Order authorizes construction scope. A Builder
must not infer edit authorization from the roadmap alone.

### Adaptive verification rules

The Reviewer must not ask only *"Does the code pass CI?"*, but first *"Does this CI verify the right contracts for this WP?"*.

- **CI Fitness Classifications:** `FIT`, `FIT_WITH_ADDITION`, `OVERBROAD`, `STALE`, `UNSTABLE`.
- **Preserve baseline gates:** Retain core quality gates that protect platform integrity.
- **Minimum complete WP gates:** Add only the minimum specific gates required to prove the active Work Order.
- **No stale gate baggage:** Do not carry obsolete phase-specific gates forward indefinitely.
- **No premature future gates:** Do not activate future-phase gates before their capability is built.
- **Phase Evolution Examples:**
  - *Crawler Core:* discovery, pagination, retry/resume, dedup, persistence.
  - *Warehouse:* SHA content-addressing, Package/Revision, managed storage, Vault, Shelf, recovery, bundle integrity.
  - *HSMT Extraction:* multi-page tables, boundary rows, structured facts, completeness, fail-closed handling (`SOURCE_DOCUMENT_MISSING`, `SOURCE_CONFLICT`, `NEEDS_REVIEW`).
  - *Evidence:* evidence locators, page/sheet/row provenance.
  - *Ground Truth:* verified corrections, Golden HSMT regression.
  - *AI:* authority boundary, deterministic fallback, confidence-gated routing.

## CI runtime & triage governance

1. **Finite Adaptive Budgets:** Every required CI job must have a finite, job-specific, evidence-based runtime budget defined by the active CI Fitness Contract.
2. **Timeout / Stall Triage:** If a required job reaches its configured finite budget or stalls, HOLD verification and begin root-cause triage:
   - **HOLD** verification immediately.
   - **Root-Cause Triage:** Classify as `WP_CODE_DEFECT`, `CI_INFRASTRUCTURE_DEFECT`, `DEPENDENCY/NETWORK_DEFECT`, `PRE-EXISTING_TECH_DEBT`, or `UNKNOWN`.
   - If transient CI infrastructure: at most **ONE** rerun. If repeated, stop rerunning and create a bounded CI-hardening task.
   - A fast explicit failure is strictly preferred over an unbounded hang.
   - Never increase a budget merely to mask defects or instability.

## Local staged integration governance

Detailed micro-WP review, audited commit freeze, forward correction, remote
feature-branch checkpoints, Parent-WP integration, hosted-CI waiver, retro-CI
recovery, and release blocking are defined in
`docs/agent/LOCAL_STAGED_INTEGRATION.md`.

- A feature-branch push without an open PR is a remote checkpoint only; it is
  not CI evidence and must never be reported as `CI PASS`.
- Local machine execution may supply machine-verifier evidence when hosted CI
  is unavailable; the Independent Reviewer/Auditor remains a separate role and
  does not become a runtime runner.
- A merge performed under a verified hosted-CI infrastructure waiver accrues
  `PENDING_RETRO_CI = YES` until CI Recovery passes.
- `PENDING_RETRO_CI > 0` blocks official Team Bid release/publish unless a later
  explicit Human decision establishes a separate bounded exception.

## Work Order CI fitness contract requirement

Every future Work Order must define its CI Fitness Contract before implementation:

```text
CI FITNESS CONTRACT
-------------------
CURRENT WP:
CAPABILITY UNDER CHANGE:
CRITICAL RISKS:
BASELINE GATES TO KEEP:
WP-SPECIFIC GATES REQUIRED:
GATES NOT REQUIRED YET:
MAX JOB RUNTIME: <finite WP/job-specific budget>
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: YES / NO
RATIONALE:
```

## Plugin execution contract

For technical Work Packages where applicable:

- Invoke Superpowers skills before the action they govern.
- Use CodeGraph for relevant impact discovery before edits.
- Evidence plugin execution; naming CodeGraph/Superpowers alone is insufficient.
- Incidents require systematic-debugging before a fix; behavior changes require
  TDD RED → GREEN; PASS/DONE requires verification-before-completion.
- Report CodeGraph impact radius separately from edit and test radius.
- If a plugin is unavailable, report `TOOL_UNAVAILABLE` and use the documented
  fallback; never disable or remove a plugin to bypass its workflow.

## Test collection integrity

At the beginning of a coding task:
- Record current pytest collection count.

At final verification:
- Collection must not unexpectedly decrease.
- Any decrease requires root-cause investigation.
- Never add/duplicate tests merely to satisfy a numeric count.
- Historical test counts are informational unless tied to a verified commit.
- Zero collection errors and zero failing tests are mandatory.
