# QI-Crawler repository guardrails

## Repository map

- Production: `src/qi_crawler/`; tests: `tests/`; migrations: `alembic/versions/`
- Packaging: `packaging/`; scripts: `scripts/`; docs: `docs/`; templates: `templates/`
- Important root helpers: `evaluate_qi_crawler.py`, `pyproject.toml`, `alembic.ini`, tracked build/release scripts.
- Generated only: `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `build/`, `dist/`, `release_staging/`, approved `.tmp/` children.

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

1. **15-Minute Budget:** Every required CI job must have a maximum runtime budget of 15 minutes.
2. **Timeout / Stall Triage:** If a required job exceeds 15 minutes or stalls:
   - **HOLD** verification immediately.
   - **Root-Cause Triage:** Classify as `WP_CODE_DEFECT`, `CI_INFRASTRUCTURE_DEFECT`, `DEPENDENCY/NETWORK_DEFECT`, `PRE-EXISTING_TECH_DEBT`, or `UNKNOWN`.
   - If transient CI infrastructure: at most **ONE** rerun. If repeated, stop rerunning and create a bounded CI-hardening task.
   - A fast explicit failure is strictly preferred over an unbounded hang.

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
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: YES / NO
RATIONALE:
```

## Test collection integrity

At the beginning of a coding task:
- Record current pytest collection count.

At final verification:
- Collection must not unexpectedly decrease.
- Any decrease requires root-cause investigation.
- Never add/duplicate tests merely to satisfy a numeric count.
- Historical test counts are informational unless tied to a verified commit.
- Zero collection errors and zero failing tests are mandatory.
