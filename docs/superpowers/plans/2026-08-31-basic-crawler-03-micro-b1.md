# WP-TB-BASIC-CRAWLER-03 Micro-B1 implementation plan

## Scope

Implement controlled folder candidate discovery and package-scoped short
managed naming without changing schemas, migrations, source crawlers, or
TenderCase authority. Folder scans remain read-only until each candidate is
explicitly confirmed by a Human with role, zone, authority, and evidence.

## RED → GREEN → REFACTOR

1. **Candidate discovery (RED):** add tests proving recursive scans return
   immutable candidates, rescan discovers new files without persistence, and a
   direct directory passed to `add_path_to_zone` is rejected with zero writes.
2. **Candidate discovery (GREEN):** add the read-only candidate model/scanner
   and make direct directory intake fail closed while preserving explicit file
   intake.
3. **Candidate confirmation (RED):** add tests proving only explicitly
   confirmed candidates are ingested, unselected candidates cause zero writes,
   and a changed file is rejected after scan.
4. **Candidate confirmation (GREEN):** add the bounded confirmation API,
   revalidate candidate SHA and exact release/package authority, and reuse the
   existing intake/membership path only after confirmation.
5. **Role/package guards (RED → GREEN):** add tests for foreign package
   rejection, same-base different-revision hold, and explicit foreign
   `REFERENCE_ONLY` handling, then implement only those guards.
6. **Managed naming (RED → GREEN):** add tests and implementation for
   `pkg:<RAW>|role:<ROLE>|seq:<NN>` slots, per-release reset, preserved original
   filename/bytes, same-SHA cross-release memberships, and restart stability.
7. **GUI/service seam (RED → GREEN):** add focused tests and thin adapters so
   folder selection/rescan scan only, zero selection does not intake, and only
   selected confirmed candidates invoke intake. No watcher or redesign.

## Verification checkpoints

- Run targeted workspace-intake, workspace, workspace-ops and focused GUI
  tests after each green stage.
- Run `ruff check .`, `git diff --check`, and the full `.venv` pytest suite.
- Confirm only the authorized files changed and schema/migrations are untouched.
