# QI-Crawler Agent Handoff

## Task

Governance + Adaptive CI Verification + Branch Hygiene Checkpoint

## Status

READY_FOR_CHATGPT_REAUDIT — Governance institutionalized in AGENTS.md, stale remote branches cleaned, PR topology verified.

## Previous verified checkpoint

- CI-Hardening-2A: PASS (PR #14 merged into `main` at commit `7909ccd`)
- P0-B1: PR #13 OPEN (functional verification PASS, awaiting final integration)

## What was done

- **Governance Institutionalization:** Added **LAW 8 — Adaptive Verification** to `AGENTS.md` requiring CI/test contracts to match the active Work Package's capability, risk profile, and maturity stage.
- **Role-Based Separation of Responsibilities:** Formalized **LAW 2** as a durable role-based contract (Planner → Independent Reviewer/Auditor → Single Writer → Machine Verifier → Human Merge Approver).
- **CI Runtime & Triage Governance:** Governance mandates a 15-minute maximum runtime budget for every required CI job. Explicit workflow enforcement currently exists on the two Linux test jobs; Code Quality and Windows 3.12 require a separate bounded CI follow-up. Enforced a 5-way root-cause triage workflow for stalls (`WP_CODE_DEFECT`, `CI_INFRASTRUCTURE_DEFECT`, `DEPENDENCY/NETWORK_DEFECT`, `PRE-EXISTING_TECH_DEBT`, `UNKNOWN`).
- **Work Order CI Fitness Contract:** Mandated explicit CI Fitness Contracts in every future Work Order before implementation.
- **Branch Hygiene:**
  - Safely deleted 5 obsolete merged remote branches: `ci/hardening-1`, `ci/hardening-2a-apt-resilience`, `codex/v071-release`, `codex/fix-dependency-graph`, `codex/windows-installer-v070`.
  - Kept active branches: `main` and `p0-b1-managed-storage-independence` (PR #13).
  - Pruned remote-tracking refs and removed local merged branch `ci/hardening-2a-apt-resilience`.

## Files changed

- `AGENTS.md`
- `docs/agent_handoff/CURRENT.md`

## Architecture / contracts affected

- Project-wide engineering governance updated to enforce phase-adaptive CI evaluation.
- No application source code, tests, migrations, or database schema were modified.

## Database / runtime data

- Migration: NO
- Runtime data modified: NO
- Existing user data deleted: NO
- `data/documents/` touched: NO

## Local Verification

- Full regression suite: 307 passed
- `python -m ruff check .`: PASS (`All checks passed!`)
- `git diff --check`: PASS (0 errors)
- `git diff --name-status`: exactly 2 intended files (`AGENTS.md`, `docs/agent_handoff/CURRENT.md`)

## Active Pull Requests

- PR #15: `Governance: institutionalize Adaptive Verification and branch hygiene` (OPEN on `governance/adaptive-ci-and-branch-hygiene`)
- PR #13: `P0-B1: prove managed storage independence` (OPEN on `p0-b1-managed-storage-independence`)

## CI Fitness — Current Phase (Warehouse / Managed Storage / Integrity)

- **Classification:** `FIT_WITH_ADDITION`
- **Rationale:** Technical quality/test gates are appropriate for the Warehouse/Core phase; Linux apt resilience is fixed; all four CI jobs pass; but explicit 15-minute workflow timeout enforcement is incomplete for Code Quality and Windows 3.12.

## Known issues / blockers

1. Code Quality lacks explicit 15-minute workflow timeout in `ci.yml`.
2. Windows 3.12 lacks explicit 15-minute workflow timeout in `ci.yml`.
3. This must be handled in a separate CI-only micro-task before starting the next feature WP.

## Explicitly NOT done

- No P0-B2 SHA Vault implementation.
- No P0-B3 Canonical Package Shelf implementation.
- No P0-B4 Missing / Recoverable / Safe Restore implementation.
- No P0-C Bundle Completeness implementation.
- No R4.3B / SupplyItemParser 13→8 fix.
- No Semantic Extraction changes.
- No installer / release changes.

## Next recommended task

1. ChatGPT re-audit PR #15.
2. Human merge PR #15 if PASS.
3. Separate bounded CI task to complete global 15-minute enforcement.
4. ChatGPT audit that CI task.
5. Human merge CI task.
6. Synchronize/revalidate P0-B1 against updated main.
7. Close P0-B1.
8. Only then start P0-B2.

## Git state

- Base branch: `main`
- Verified base commit: `7909ccd`
- Working branch: `governance/adaptive-ci-and-branch-hygiene`
- Commit created: YES
- Push performed: YES
- PR #15: OPEN (https://github.com/tanntran2000/QI-Crawler-MVP/pull/15)
