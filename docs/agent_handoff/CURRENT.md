# QI-Crawler Agent Handoff

## Task

CI-Hardening-1 — Technical CI Foundation & Runtime Document Git Safety

## Status

PASS — local verification and remote GitHub CI both passed.

## Previous verified checkpoint

- WP2.6-R4.3A / P0-A Warehouse Bundle Guard: PASS.
- Verified commit: `74cab1f`
- Pushed to: `origin/main`
- P0-B implementation has NOT started.

## What was done

- Added Git protection for runtime HSMT/user documents under `data/documents/`.
- Expanded GitHub CI from the previous single Ubuntu/Python 3.12 job.
- Added separately named CI jobs:
  - Code Quality
  - Tests Ubuntu 3.12
  - Tests Windows 3.12
  - Compatibility Ubuntu 3.11
- Changed Ruff CI scope from `src tests` to the canonical repository-wide `ruff check .`.
- Corrected stale P0-A Git checkpoint information in the handoff.
- No production Python/business/extraction behavior was changed.

## Files changed

- `.github/workflows/ci.yml`
- `.gitignore`
- `docs/agent_handoff/CURRENT.md`

## Architecture / contracts affected

- CI-Hardening-1 establishes the first technical layer of the locked 3-Tier Quality Gate v2.
- `data/documents/` is runtime/user data and must never be committed to Git.
- Windows 3.12 is now represented as a first-class CI test environment.
- Ubuntu 3.11 is a compatibility environment.
- Canonical Ruff scope is repository-wide.

## Database / runtime data

- Migration: NO
- Runtime data modified: NO
- Existing user data deleted: NO
- `data/documents/` content modified: NO
- `data/documents/` is now Git-ignored.

## Local Verification

- `python -m pytest`: 307 passed in 225.78s
- Test collection regression: NONE (verified baseline = 307)
- `python -m ruff check .`: PASS
- `git diff --check`: PASS
- `git diff --name-status`: PASS
- Changed files: exactly 3 intended files

## Remote CI Verification

- Functional commit SHA: `80ece6ebeca56d4ea8a4b813131d5d0c9df74ecc`
- Branch: `ci/hardening-1`
- Code Quality: PASS
- Tests Ubuntu 3.12: PASS
- Tests Windows 3.12: PASS
- Compatibility Ubuntu 3.11: PASS
- Overall remote CI: PASS

## Known issues / blockers

- Remote GitHub CI still needs to validate the new workflow.
- Branch Protection has not yet been configured.
- Architecture Contract Gate, Semantic Safety Gate, and Golden HSMT Gate are not part of CI-Hardening-1.

## Explicitly NOT done

- No P0-B implementation.
- No Vault / Package Shelf / Recovery implementation.
- No P0-C Bundle Completeness implementation.
- No R4.3B / SupplyItemParser 13→8 fix.
- No Semantic Safety implementation.
- No Golden HSMT CI Gate.
- No installer build.
- No release.

## Next recommended task

After CI-Hardening-1 is remotely verified:

`WP2.6-R4.3A / P0-B1 — Managed Storage Independence Regression`

Prove that after successful Document Intake, deleting the original external file does not break the crawler-managed stored document.

## Git state

- Base branch: `main`
- Verified base commit: `74cab1f`
- Current working branch: `ci/hardening-1`
- Functional commit created: YES
- Functional commit SHA: `80ece6ebeca56d4ea8a4b813131d5d0c9df74ecc`
- Push performed: YES
- Remote branch: `origin/ci/hardening-1`
- PR: NONE
- CI-Hardening-1: PASS