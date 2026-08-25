# Engineering Failure Memory

This file is a routed organizational memory of material engineering failures.

```text
KNOWN_FAILURE_MODES != CURRENT
KNOWN_FAILURE_MODES != PROJECT_MEMORY
KNOWN_FAILURE_MODES != GROUND_TRUTH
KNOWN_FAILURE_MODES != MASTER_ROADMAP
KNOWN_FAILURE_MODES != FEEDBACK_LEDGER
KNOWN_FAILURE_MODES != LESSONS
```

Authority order remains:

```text
live Git / merged code / verified source
> active handoff
> engineering failure-memory entry
```

An outdated failure entry must not override live source evidence. `OPEN
FAILURE != AUTOMATIC GLOBAL BLOCKER`: an entry blocks work only when its
affected capability/layer intersects the active Work Package or a governance /
release contract explicitly makes it a gate.

When an open failure intersects the active Work Package's capability or layer,
the Reviewer must revalidate `CURRENT_EVIDENCE` against the exact active/audit
Git objects before using the entry as blocker, closure evidence or proof.
Stale line locators or stale source claims must be updated or marked
`REQUIRES_VERIFICATION`. Failure Memory is routing evidence, not a substitute
for current source inspection.

## Entry schema

Every entry uses these fields exactly once:

```text
ID
TITLE
STATE
SEVERITY_AT_DETECTION
DISPOSITION
DETECTED_BY
AFFECTED_BASELINE
PRODUCT_HOUSE_LAYER
SYMPTOM
ROOT_CAUSE
WHY_EXISTING_TESTS_MISSED_IT
CI_IMPLICATION
FIX
FIX_HEAD
REGRESSION_GUARD
INDEPENDENT_AUDIT
CURRENT_EVIDENCE
PERMANENT_PREVENTION
```

Allowed `STATE` values are `OPEN`, `RESOLVED_LOCAL`, `AUDITED`, `MERGED`, and
`WAIVED_BY_HUMAN`. Unsupported root-cause claims are recorded as
`REQUIRES_VERIFICATION`.

## FM-001 — SQLite migration backup omitted committed WAL state

```text
ID = FM-001
TITLE = SQLite migration backup omitted committed WAL state
STATE = MERGED
SEVERITY_AT_DETECTION = CRITICAL
DISPOSITION = RESOLVED
DETECTED_BY = FULL_REPO_AUDIT / P0 WAL backup correction
AFFECTED_BASELINE = pre-migration SQLite backup on WP-MI-TBMT-02B
PRODUCT_HOUSE_LAYER = INFRASTRUCTURE / PERSISTENCE
SYMPTOM = a file copy of an active WAL database could omit committed rows
ROOT_CAUSE = backup copied only the main database file instead of a coherent SQLite snapshot
WHY_EXISTING_TESTS_MISSED_IT = prior coverage did not prove committed WAL rows survived an independent backup open
CI_IMPLICATION = local migration/backup regression required; no hosted CI claim
FIX = use sqlite3.Connection.backup(); remove partial output and propagate errors fail-closed
FIX_HEAD = cbda73692dfe6b99c6a2045b2306b57e1e4136fb
REGRESSION_GUARD = WAL committed-row, normal backup, restore and failure-path tests
INDEPENDENT_AUDIT = Parent cumulative re-verification and independent re-audit PASS
CURRENT_EVIDENCE = merged PR #55; P0 mechanism is sqlite3.Connection.backup()
PERMANENT_PREVENTION = keep coherent SQLite backup tests and never replace them with raw file copying
```

## FM-002 — Windows publisher schema revision drift

```text
ID = FM-002
TITLE = Windows publisher schema revision drift
STATE = OPEN
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RELEASE_BLOCKER
DETECTED_BY = FULL_REPO_AUDIT
AFFECTED_BASELINE = main at detection: d199e3203c172e525e20d86bddab7c23f830c7b4
PRODUCT_HOUSE_LAYER = INFRASTRUCTURE / DELIVERY
SYMPTOM = publisher and installer tests still validate Alembic 0013
ROOT_CAUSE = scripts/publish_windows_release.ps1:56-57,69 pins 0013 while src/qi_crawler/db.py:14 declares 0015_add_opportunity_review_events
WHY_EXISTING_TESTS_MISSED_IT = release mechanics were not part of the 02B product integration gate
CI_IMPLICATION = release candidate must be blocked until publisher, manifest and installer checks agree with current schema
FIX = reconcile release publisher and tests in a bounded release Work Package
FIX_HEAD = NOT_FIXED
REGRESSION_GUARD = tests/test_windows_installer.py:163,179,236 must assert the current head after repair
INDEPENDENT_AUDIT = FULL_REPO_AUDIT finding; not independently resolved here
CURRENT_EVIDENCE = scripts/publish_windows_release.ps1:56-70 and tests/test_windows_installer.py:163-236 reference 0013
PERMANENT_PREVENTION = derive or verify release schema metadata from the canonical migration head
```

## FM-003 — Domain Core depended on Opportunity Radar application projection

```text
ID = FM-003
TITLE = Domain Core depended on Opportunity Radar application projection
STATE = MERGED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED
DETECTED_BY = FULL_REPO_AUDIT / FC2 architecture correction
AFFECTED_BASELINE = WP-MI-TBMT-02B source-neutral review contract
PRODUCT_HOUSE_LAYER = DOMAIN CORE / APPLICATION BACKEND
SYMPTOM = a domain contract imported an application projection
ROOT_CAUSE = dependency direction was inverted at the review boundary
WHY_EXISTING_TESTS_MISSED_IT = functional tests did not enforce Product House layer direction
CI_IMPLICATION = architecture guard and targeted review tests are required
FIX = mapping ownership moved to Application Backend; Domain Core owns its contract
FIX_HEAD = b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a
REGRESSION_GUARD = architecture guard plus domain/application boundary tests
INDEPENDENT_AUDIT = FC2 independent architecture re-audit PASS
CURRENT_EVIDENCE = merged Parent 02B evidence and exact audited code head
PERMANENT_PREVENTION = keep explicit layer ownership and guard imports at the boundary
```

## FM-004 — Architecture regression guard allowed equivalent absolute-import bypass

```text
ID = FM-004
TITLE = Architecture regression guard allowed equivalent absolute-import bypass
STATE = MERGED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED
DETECTED_BY = FULL_REPO_AUDIT / FC2 architecture guard hardening
AFFECTED_BASELINE = Product House dependency guard
PRODUCT_HOUSE_LAYER = ENGINEERING TOOLBOX / ARCHITECTURE GOVERNANCE
SYMPTOM = equivalent import identities could evade the guard
ROOT_CAUSE = guard compared only one import spelling rather than normalized identities
WHY_EXISTING_TESTS_MISSED_IT = regression coverage did not include relative, absolute and plain forms together
CI_IMPLICATION = the guard must execute as a bounded static regression
FIX = normalize relative, absolute and plain import identities before comparison
FIX_HEAD = b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a
REGRESSION_GUARD = architecture guard tests cover all equivalent import forms
INDEPENDENT_AUDIT = FC2 independent architecture re-audit PASS
CURRENT_EVIDENCE = merged Parent 02B evidence and exact audited code head
PERMANENT_PREVENTION = treat semantic import identity, not spelling, as the guard key
```

## FM-005 — Legacy machine GO/HOLD/win authority remains reachable

```text
ID = FM-005
TITLE = Legacy machine GO/HOLD/win authority remains reachable
STATE = OPEN
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = AUTHORITY_DEBT
DETECTED_BY = FULL_REPO_AUDIT
AFFECTED_BASELINE = main at detection: d199e3203c172e525e20d86bddab7c23f830c7b4
PRODUCT_HOUSE_LAYER = APPLICATION BACKEND / DELIVERY CLI
SYMPTOM = legacy bid_intelligence exposes evaluate_bid_gate, estimate_win_likelihood and GO/HOLD/NO-GO output
ROOT_CAUSE = src/qi_crawler/bid_intelligence.py:184-324 remains imported by src/qi_crawler/cli.py:23-29 and reachable through bid-gate/danh-gia commands
WHY_EXISTING_TESTS_MISSED_IT = compatibility and legacy command coverage preserve reachability rather than asserting authority quarantine
CI_IMPLICATION = no future AI or SOP release may treat this legacy path as approved authority
FIX = create a bounded authority-quarantine decision before changing or removing the legacy surface
FIX_HEAD = NOT_FIXED
REGRESSION_GUARD = add an explicit reachability/authority-boundary test in the future bounded WP
INDEPENDENT_AUDIT = FULL_REPO_AUDIT finding; no deletion or quarantine claimed
CURRENT_EVIDENCE = bid_intelligence.py:184-324 and cli.py:23-29, 866-897, 1149-1169
PERMANENT_PREVENTION = distinguish legacy compatibility assets from approved Human/SOP authority
```

## FM-006 — API bypasses Application Backend through direct ORM/DB access

```text
ID = FM-006
TITLE = API bypasses Application Backend through direct ORM/DB access
STATE = OPEN
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = API_HOLD
DETECTED_BY = FULL_REPO_AUDIT
AFFECTED_BASELINE = main at detection: d199e3203c172e525e20d86bddab7c23f830c7b4
PRODUCT_HOUSE_LAYER = DELIVERY API / INFRASTRUCTURE
SYMPTOM = src/qi_crawler/api.py creates Database and queries ORM models directly in route handlers
ROOT_CAUSE = API routes bypass the Application Backend boundary
WHY_EXISTING_TESTS_MISSED_IT = API evolution is held and existing tests focus on endpoint output rather than dependency direction
CI_IMPLICATION = API work remains HOLD until a bounded backend-first contract exists
FIX = route API behavior through Application Backend services in a separate approved WP
FIX_HEAD = NOT_FIXED
REGRESSION_GUARD = architecture/import guard and API delegation tests in the future API WP
INDEPENDENT_AUDIT = FULL_REPO_AUDIT finding; no API repair claimed
CURRENT_EVIDENCE = api.py:3-22,30-74,77-121,124-171,174-238 directly import models/Database and call session/query
PERMANENT_PREVENTION = keep transport code thin and forbid direct ORM access in API delivery surfaces
```

## FM-007 — Bid Radar source-integrity SHA enforcement exists only at delivery/GUI boundary

```text
ID = FM-007
TITLE = Bid Radar source-integrity SHA enforcement exists only at delivery/GUI boundary
STATE = RESOLVED_LOCAL
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED_LOCAL_AUDITED_REMOTE_CHECKPOINTED_PENDING_MERGE
DETECTED_BY = FULL_REPO_AUDIT
AFFECTED_BASELINE = source-sensitive Bid Radar import/export flow at detection; exact main SHA was not recorded in the original finding
PRODUCT_HOUSE_LAYER = APPLICATION BACKEND / DESKTOP DELIVERY
SYMPTOM = derived output could be invoked outside the GUI without rechecking the imported source SHA
ROOT_CAUSE = source integrity was enforced only by GUI state; application export paths lacked a shared backend precondition
WHY_EXISTING_TESTS_MISSED_IT = GUI regression coverage can pass while non-GUI callers remain unguarded
CI_IMPLICATION = derived export must remain blocked until source identity is enforced at the authoritative backend boundary
FIX = added source_integrity.verify_source_integrity() and required it before source-neutral and GUI delivery exports; GUI passes the loaded path and SHA through the worker boundary
FIX_HEAD = 30d9b977000cbc4c4abcc20125fe501344d7e935
REGRESSION_GUARD = source A/source B same-path export regression at application backend, GUI adapter and GUI boundaries; missing source fails closed
INDEPENDENT_AUDIT = PASS
CURRENT_EVIDENCE = source_integrity.py; confirmed_opportunity_export.py; opportunity_intelligence.py; gui_services.py; gui.py; tests/test_confirmed_opportunity_export.py; tests/test_bid_radar_gui.py; audited remote handoff 4bd2c91463571494b4750f8a99dbd1fe522c3101
PERMANENT_PREVENTION = make source identity a backend precondition for every derived export path
```

## FM-008 — tests/conftest.py lifecycle shim masks missing production Database.create_all

```text
ID = FM-008
TITLE = tests/conftest.py lifecycle shim masks missing production Database.create_all
STATE = OPEN
SEVERITY_AT_DETECTION = MINOR
DISPOSITION = TEST_DEBT
DETECTED_BY = FULL_REPO_AUDIT
AFFECTED_BASELINE = main at detection: d199e3203c172e525e20d86bddab7c23f830c7b4
PRODUCT_HOUSE_LAYER = ENGINEERING TOOLBOX / TEST INFRASTRUCTURE
SYMPTOM = the autouse fixture monkeypatches Database.create_all to run migrations
ROOT_CAUSE = tests/conftest.py:11-22 supplies a compatibility shim for a production method that is not present
WHY_EXISTING_TESTS_MISSED_IT = the shim keeps older tests green while hiding whether production callers use the obsolete lifecycle API
CI_IMPLICATION = test green does not prove production create_all compatibility
FIX = inventory callers and either remove the obsolete test seam or add an explicit compatibility contract in a bounded test-debt WP
FIX_HEAD = NOT_FIXED
REGRESSION_GUARD = test that production startup/migration does not depend on the shim
INDEPENDENT_AUDIT = FULL_REPO_AUDIT finding; no shim removal claimed
CURRENT_EVIDENCE = tests/conftest.py:11-22 monkeypatches require_current_schema and Database.create_all
PERMANENT_PREVENTION = keep production lifecycle tests separate from compatibility fixtures and audit shim reachability
```

## Routing

Read only entries relevant to the active capability or failure path. A new
Parent reads affected layers; an incident reads the matching symptom/path; a
material audit or recovery may broaden the read. For an unrelated Micro-WP,
`N/A` is acceptable. This file does not authorize implementation, alter
Ground Truth, or close the full-repository audit by itself.
