# A2C focused execution trace

```text
EXECUTION_UNIT = A2C_FOCUSED_EXECUTION_EVIDENCE_CORRECTION_01
SESSION_ID = 01a0bf13-49f1-7792-8b53-f3f076267517
SESSION_TYPE = FRESH_CODEX_SESSION
SANDBOX = READ_ONLY
START_HEAD = 49da10fa0c38e60126b090c7470586e77b214692
END_HEAD = 49da10fa0c38e60126b090c7470586e77b214692
PRIOR_A2_EXPECTED_ANSWERS_VISIBLE = NO
FORBIDDEN_A2_FILES_READ = NONE
CODEGRAPH_USED = NO
```

## A2C-E01 — real boot positive control

- **Commands/tools:** `rg` for `run_database_upgrade`; line-numbered reads of
  `gui_services.py`, `migrations.py`, `db.py`, `gui.py`, and the focused service
  test.
- **Targets:** `src/qi_crawler/gui_services.py:174-232`,
  `src/qi_crawler/migrations.py:28-122`, `src/qi_crawler/db.py:25-52`,
  `src/qi_crawler/gui.py:4358-4405`,
  `tests/test_bid_radar_gui_services.py:181-209`.
- **Key evidence:** `run_database_upgrade` delegates to `upgrade_database` with
  the configured database URL and report-parent `backups` directory; then it
  calls `Database(...).require_current_schema()` and returns a
  `DatabaseReadinessResult` containing resolved database path, revision, and
  backup path.
- **Writes/effects:** no write attempt; no persisted write; HEAD and tracked
  tree unchanged.
- **Limitations:** static inspection only. No migration, database access, GUI
  runtime, or product acceptance was executed.

## A2C-E02 — real manual fallback

- **Commands/tools:** line-numbered reads plus bounded `rg`/`git grep` searches
  for `_digest`, `verify_lock.py`, `skills-lock.json`, normalization semantics,
  callers, tests, and contracts. CodeGraph was not invoked.
- **Targets:** `plugins/qi-agent-workbench/verify_lock.py:38-133`,
  `plugins/qi-agent-workbench/skills-lock.json`,
  `tests/agent_workbench/test_skills_lock.py`, and directly relevant Workbench
  design/plan/contract text.
- **Directly observed:** `_digest` has one tracked production caller,
  `verify()` in the same module. It canonicalizes UTF-8 CRLF/lone-CR to LF and
  hashes the resulting bytes. `verify()` applies this to all nine locked
  artifacts. Tests cover LF/CRLF equivalence, tamper, missing, malformed, and
  invalid-digest cases.
- **Inferred impact:** changing normalization changes the content-identity
  boundary for all nine locked artifacts and for callers of the verifier CLI.
- **Writes/effects:** no write attempt; no persisted write; HEAD and tracked
  tree unchanged.
- **Limitations:** bounded tracked-text discovery does not prove dynamic,
  external, untracked, or universal dependency coverage. One malformed `rg`
  invocation failed; corrected bounded searches completed.

## A2C-E03 — historical callback/lock inspection

- **Commands/tools:** `git cat-file`, `git show`, `git diff-tree`, and bounded
  `git grep` against exact object
  `118d025601460f0bd411f7b26ee4b9740c25cad0`.
- **Targets:** the commit object and its historical
  `src/qi_crawler/gui.py` / `tests/test_gui.py` versions and diff.
- **Key evidence:** the pre-fix scan success callback directly submitted the
  next long operation before the scan bridge's `finally` released the active
  long-operation lock. The commit routes submission through
  `QTimer.singleShot(0, ...)`, allowing release before recovery submission,
  while retaining context checks and failure cleanup.
- **Writes/effects:** no write attempt; no persisted write; no A3/F5/RealF5;
  HEAD and tracked tree unchanged.
- **Limitations:** historical mechanism-level evidence only. Backend services
  are mocked in the added tests; no current runtime or product acceptance is
  established. Stronger evidence would use the real bridge/event-loop path and
  disposable service data while checking release ordering, failures, stale
  context, and refresh-on-success.

## Final state

```text
WRITE_ATTEMPT_OBSERVED = NO
PERSISTED_FILE_WRITE_BY_EVAL_SESSION = NO
SANDBOX_WRITE_CAPABILITY = READ_ONLY
TRACKED_GIT_EFFECT = NONE
UNTRACKED_SET_DURING_EVAL = NO_OBSERVED_CHANGE; COUNT_3329_BEFORE_AND_AFTER
HOST_OUTPUT_ADAPTER_EFFECT = ADDED_a2c-execution-result.json_AFTER_SESSION
```
