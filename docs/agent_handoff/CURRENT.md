# Current handoff

## Task

WP2.6-R4.3A / P0-B Preparation

## Status

PASS — preparation only. P0-B has not been implemented.

## Previous verified checkpoint

P0-A Warehouse Bundle Guard: PASS.

## What was done

- Prepared the already-verified P0-A scope for one Git checkpoint.
- Inspected only document intake, managed storage, SHA/dedup, bundle identity, model/schema, and focused tests.
- Recorded P0-B storage findings and the next smallest patch; no P0-B behavior was implemented.

## Files changed

- `src/qi_crawler/models.py`
- `src/qi_crawler/document_intake.py`
- `src/qi_crawler/db.py`
- `alembic/versions/0012_add_document_bundle_membership.py`
- `tests/test_document_bundle_guard.py`
- `tests/test_alembic_migrations.py`
- `docs/agent_handoff/CURRENT.md`

## Architecture / contracts affected

- Current flow: `intake_file` validates the external file, hashes it, runs Identity/Bundle Guard, then `_atomic_store` copies it into `document_dir/<source>/<tender>/<sha256>/<safe-original-name>` before persisting `Document.stored_path`.
- The stored path is crawler-managed and native extraction/UI reopen it; successful intake no longer depends on the original external path.
- Reusable P0-B components: `DocumentIntakeService._hash_file`, `_atomic_store`, `_cleanup_orphan`, `_find_duplicate`, `Document`, immutable `sha256`, `stored_path`, and the P0-A bundle fields/guards.
- P0-B gaps only: no `warehouse/staging|vault|packages|quarantine|trash` layout; no separate immutable Vault and canonical Package Shelf path; no persisted MISSING/RECOVERABLE state; no explicit restore service.
- P0-B migration required: **YES**. The current single `stored_path` cannot represent independent Vault/Shelf copies plus their recovery state. Use a new migration after `0012`; never reuse `0012`.
- Proposed P0-B sequence: (1) Managed Storage Independence regression, (2) SHA Vault, (3) Canonical Package Shelf, (4) explicit Missing → Recoverable → Safe Restore.
- Exact next micro-patch: **P0-B1 — add the focused regression proving a successful current intake remains readable after the external original is deleted.** No production/schema change is needed for that first contract test.

## Database / runtime data

- Existing migration: `0012_add_document_bundle_membership`.
- New migration created: NO (during this preparation task).
- Runtime data modified: NO. Existing user data deleted: NO. `data/documents/` modified: NO.

## Verification

- Previous P0-A: 34 targeted passed; 307 full passed; Ruff PASS; diff-check PASS.
- Current preparation: `git diff --check` PASS; `git diff --name-status` reviewed. No Python/test/migration code was added in this preparation task.

## Known issues / blockers

- No master checkpoint file was present; no implementation blocker was found.
- P0-B must define a compatible migration and backward-read behavior for legacy `stored_path` records before Vault/Shelf writes are enabled.

## Explicitly NOT done

- P0-B implementation, P0-C, R4.3B / SupplyItemParser 13→8, R5+, cold archive, cloud/NAS, export, GUI redesign, installer.

## Git state

- Branch: `main`; HEAD before checkpoint: `fe8187f`.
- Commit created: YES (this authorized P0-A checkpoint). Push performed: pending command. PR: NONE.
- Working tree before staging contains only P0-A source/migration/tests and this handoff, plus pre-existing untracked `data/documents/` which must remain unstaged.
