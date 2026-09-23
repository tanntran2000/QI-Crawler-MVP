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

## FM-010 — Secondary checkout caused false exact-object audit failure

```text
ID = FM-010
TITLE = Secondary checkout caused false exact-object audit failure
STATE = MERGED
SEVERITY = IMPORTANT
DISPOSITION = RESOLVED_BY_FORWARD_CANONICAL_AUTHORITY_CORRECTION
DETECTED_BY = WP-WH-OPS-01 independent audit
BASELINE = post-PR71 / WP-WH-OPS-01 local audit
LAYER = ENGINEERING TOOLBOX / GOVERNANCE / GIT PROVENANCE
SYMPTOM = Reviewer reported WRONG_OBJECT / COMMIT_ABSENT for 42c09df... because
  the audit ran in a secondary D: checkout while the Builder used canonical C:.
ROOT_CAUSE = The prior one-checkout rule named a repository but did not require
  absolute path, git-common-dir or origin identity proof. Existing tests did not
  cover cross-checkout governance provenance.
CI_IMPLICATION = NONE_DIRECT
FIX_HEAD = 41b7a1056b9bb2d69922a60282bba9846e7e2128
FIX = Require the canonical checkout identity gate before object conclusions;
  the Work Order declares WHERE and Builder/Reviewer independently prove WHERE
  plus WHAT.
PREVENTION = WRONG_CHECKOUT is an ENTRY_HOLD and is not baseline drift,
  COMMIT_ABSENT or AUDIT_OBJECT_ABSENT.
AUTHORITATIVE_CORRECTION = D was Human-authorized canonical but stale.
MERGE_EVIDENCE = 2826f8c6735fcf68f405a01386d6ab4e63476e57
INDEPENDENT_AUDIT = GOV-BOOT-D4 PASS
CANONICAL_AUTHORITY = HUMAN / GOVERNED HANDOFF AUTHORITY
CANONICAL_AUTHORITY != FRESHEST_CHECKOUT
NEWEST_OBJECT_LOCATION != CANONICAL_AUTHORITY
FORMER_C_CHECKOUT = PHYSICALLY_REMOVED
LESSON_12 = UNCHANGED
```

### Forward correction for FM-010 — canonical authority reclassification (GOV-BOOT-D3)

```text
CORRECTION_FOR = FM-010
CORRECTION_STATE = MERGED
CORRECTION_AUTHORITY = HUMAN_A0 / GOV-BOOT-D
CORRECTED_ROOT_CAUSE = Canonical checkout authority regression caused by
  confusing local Git-object availability with Human/governed checkout authority.
HISTORICAL_SYMPTOM = D lacked an object that existed in C.
INCORRECT_HISTORICAL_INFERENCE = D therefore must be the wrong/secondary checkout.
CORRECT_INTERPRETATION = D was canonical but stale.
REQUIRED_RESPONSE = sync D from origin + controlled exact-object transfer for
  unpushed history + re-audit on D; never promote C to canonical.
PERMANENT_PREVENTION = CANONICAL_AUTHORITY = HUMAN / GOVERNED HANDOFF AUTHORITY;
  CANONICAL_AUTHORITY != FRESHEST_CHECKOUT;
  NEWEST_OBJECT_LOCATION != CANONICAL_AUTHORITY;
  OBJECT_MISSING_ON_CANONICAL → HOLD / SYNC / CONTROLLED TRANSFER.
RECOVERY_EVIDENCE = D0 PASS; D1 PASS; PR72–PR80 REVALIDATED_ON_D;
  PRODUCT_DEFECT NONE; REMOTE_EVIDENCE PRESERVED;
  FORMER_C_CHECKOUT PHYSICALLY_REMOVED.
MERGE_EVIDENCE = PR #81 / 2826f8c6735fcf68f405a01386d6ab4e63476e57
HISTORY_PRESERVED = YES; Lesson 12 remains valid and unchanged.
```

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
STATE = MERGED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED
DETECTED_BY = FULL_REPO_AUDIT
AFFECTED_BASELINE = main at detection: d199e3203c172e525e20d86bddab7c23f830c7b4
PRODUCT_HOUSE_LAYER = INFRASTRUCTURE / DELIVERY
SYMPTOM = publisher and installer tests still validate Alembic 0013
ROOT_CAUSE = scripts/publish_windows_release.ps1:56-57,69 pins 0013 while src/qi_crawler/db.py:14 declares 0015_add_opportunity_review_events
WHY_EXISTING_TESTS_MISSED_IT = release mechanics were not part of the 02B product integration gate
CI_IMPLICATION = release candidate must be blocked until publisher, manifest and installer checks agree with current schema
FIX = reconcile release publisher and tests in a bounded release Work Package
FIX_HEAD = 628d19004f1c4d3bc14652424cba92ec09742ef3
REGRESSION_GUARD = tests/test_windows_installer.py:163,179,236 must assert the current head after repair
INDEPENDENT_AUDIT = PASS
CURRENT_EVIDENCE = PR #87 merged audited head 628d19004f1c4d3bc14652424cba92ec09742ef3; merge commit 6a16eaca9ac84ea568a104e4e0594c0e77db07f1; post-merge Python CI 33604333004 / SUCCESS_4_OF_4; post-merge CodeQL 33604332143 / SUCCESS
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
STATE = MERGED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED
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
CURRENT_EVIDENCE = source_integrity.py; confirmed_opportunity_export.py; opportunity_intelligence.py; gui_services.py; gui.py; tests/test_confirmed_opportunity_export.py; tests/test_bid_radar_gui.py; audited remote handoff 4bd2c91463571494b4750f8a99dbd1fe522c3101; PR #60; merge commit 82013b0bc1a4b3a62a12567d3d4cc02974f93ec9; independent Parent audit PASS; independent Spine audit PASS
MERGE_CONTEXT = merged under hosted-CI infrastructure waiver; CI PASS not claimed; retro-CI debt remains (PENDING_RETRO_CI = YES)
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
CURRENT_EVIDENCE = tests/conftest.py:11-22 retains the Database.create_all compatibility shim while Micro-B prepares a per-session real-Alembic template and copy-per-test file-backed databases; production Database still has no create_all lifecycle method
PERMANENT_PREVENTION = keep production lifecycle tests separate from compatibility fixtures and audit shim reachability
```

## FM-009 — Windows hosted CI runtime amplification exceeds required-gate budget

```text
ID = FM-009
TITLE = Windows hosted CI runtime amplification exceeds required-gate budget
STATE = MERGED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED
DETECTED_BY = PR #64 exact-head hosted CI / bounded root-cause triage
AFFECTED_BASELINE = 269a6d19539091eab5b903e2684b66ebdf9116ae
PRODUCT_HOUSE_LAYER = ENGINEERING TOOLBOX / CI / TEST INFRASTRUCTURE
SYMPTOM = Windows 3.12 had a healthy hosted execution of 628 tests in about 709 seconds, while two later equivalent executions reached only 620 passed after about 1404-1425 seconds and were cancelled at the 25-minute job boundary without an assertion failure.
ROOT_CAUSE = Primary root cause is normal application tests repeatedly executing full Alembic upgrade chains through the autouse Database.require_current_schema test shim. The correction prepares one real-Alembic migrated SQLite template per pytest session, copies a fresh file-backed database per test, and retains a real migration fallback for existing, legacy, non-file and sidecar cases. Filesystem and hosted-runner variance remain bounded execution factors, not production defects.
HOSTED_RUNNER_VARIANCE = OBSERVED_SECONDARY_VARIABILITY_NOT_PRIMARY_RUNTIME_DRIVER
WHY_EXISTING_TESTS_MISSED_IT = Functional correctness tests detect assertion failures but do not prove a stable hosted-runner runtime envelope. The test suite can remain correct while infrastructure/runtime variance exhausts the CI job budget.
CI_IMPLICATION = A repeated timeout or cancellation is not PASS and is not automatically a product regression. Preserve exact-run timing evidence, compare healthy and degraded executions, perform bounded attribution, and only then alter a runtime budget. Hosted CI waiver is not justified while hosted CI itself is functioning.
FIX = Micro-A adds phase-aware Windows runtime attribution. Micro-B adds one real-Alembic migrated SQLite template per pytest session, copy-per-fresh-file-backed SQLite DB, a per-test prepared DB registry, real migration fallback for existing/legacy/non-file/sidecar cases, and preserves original require_current_schema verification.
FIX_HEAD = 5732684ec5959093854bd29ae8ce1c52024b8a5b
REGRESSION_GUARD = The full Windows 3.12 required gate remains mandatory. A future execution that exceeds the 45-minute ceiling must HOLD and reopen runtime/test-harness investigation instead of recursively increasing the timeout.
INDEPENDENT_AUDIT = PASS
CURRENT_EVIDENCE = PR #64 merged feature head db19f42985030f2b154804f959fca615c523a06e; merge commit d10445fc2ffc92e810f0d6258160151efc1c846f; exact merged-head Python CI run 32987119489 passed all four required jobs with no CI waiver. Earlier timeout evidence remains: exact investigated head 269a6d19539091eab5b903e2684b66ebdf9116ae; healthy hosted Windows 628 PASS in approximately 709s; two equivalent executions reached 620 PASS in approximately 1404-1425s before cancellation without assertion failure; migration benchmark showed fresh upgrade_database() median approximately 0.8973s versus current-schema verification approximately 0.0018s; no process leak or real-network dependency was reproduced locally. Micro-A/B audited PASS and same-head robustness run 33581232930 produced three Windows PASS samples with 787 tests each. Final PR #85 feature head a3f946066a448911bfa6f2874628639bce4f9506 merged to main at c4e08558f54274cf6115f0bf4e966c44edcdff33; post-merge Python CI 33586520758 passed 4/4 and CodeQL 33586520695 passed.
FORWARD_CORRECTION = PR #82 changed only the Windows 3.12 timeout from 35 to 45 minutes after the two reproduced 35-minute cancellations; product and test behavior were unchanged.
FORWARD_CORRECTION_HEAD = 03056fe147c3263cf8fb2ea39e63dc239e35fffe
EXACT_HEAD_PYTHON_CI = 33381474192 / PASS
POST_MERGE_MAIN_PYTHON_CI = 33384009634 / PASS
POST_MERGE_MAIN_CODEQL = 33384009691 / PASS
FINAL_MERGED_FEATURE_HEAD = a3f946066a448911bfa6f2874628639bce4f9506
FINAL_MERGE_COMMIT = c4e08558f54274cf6115f0bf4e966c44edcdff33
FINAL_POST_MERGE_PYTHON_CI = 33586520758 / SUCCESS_4_OF_4
FINAL_POST_MERGE_CODEQL = 33586520695 / SUCCESS
CURRENT_WINDOWS_CEILING = 45_MINUTES
RECURRENCE_MAIN_HEAD = 3ebea845589fedf860afb94f69959413a819b176
RECURRENCE_RUN = 33498316251
RECURRENCE_WINDOWS_JOB = 99825528311
RECURRENCE_RESULT = 394_PASSED_IN_2609.54S_BEFORE_CANCELLATION
RECURRENCE_TERMINAL = KEYBOARD_INTERRUPT / OPERATION_CANCELLED
ASSERTION_FAILURE_OBSERVED_BEFORE_CANCEL = NO
OTHER_REQUIRED_JOBS = 3_OF_3_SUCCESS
HISTORICAL_TIMEOUT_PROGRESSION = 25_MINUTES → 35_MINUTES → 45_MINUTES
DO_NOT_RECURSIVELY_INCREASE_TIMEOUT = YES
ROBUSTNESS_RUN = 33581232930
ROBUSTNESS_SAMPLE_1 = ATTEMPT_1 / WINDOWS_JOB_100095769552 / NORTHCENTRALUS / 787_PASSED / PYTEST_413.62S / JOB_8M07S / PASS
ROBUSTNESS_SAMPLE_2 = ATTEMPT_2 / WINDOWS_JOB_100102238045 / EASTUS / 787_PASSED / PYTEST_336.21S / JOB_6M47S / PASS
ROBUSTNESS_SAMPLE_3 = ATTEMPT_3 / WINDOWS_JOB_100103941651 / WESTCENTRALUS / 787_PASSED / PYTEST_322.40S / JOB_6M30S / PASS
ROBUSTNESS = 3_OF_3_PASS
ROBUSTNESS_THRESHOLD = 35_MINUTES
CURRENT_WINDOWS_HARD_CEILING = 45_MINUTES
RECURRENCE_STATUS = MERGED_RESOLVED
PERMANENT_PREVENTION = Treat timeout boundaries as symptoms until bounded attribution is complete. Retain phase-aware attribution and per-session database preparation with the full regression guard. Another material breach of the 45-minute ceiling requires renewed attribution and HOLD; do not recursively inflate the timeout.
```

## FM-011 — Mutable URL-keyed raw HTML evidence

```text
ID = FM-011
TITLE = Mutable URL-keyed raw HTML evidence
STATE = MERGED
SEVERITY_AT_DETECTION = CRITICAL
DISPOSITION = RESOLVED
DETECTED_BY = Independent audit of WP-HARDEN-SOURCE-INTEGRITY-01
AFFECTED_BASELINE = PR #74 pre-fix source capture path
PRODUCT_HOUSE_LAYER = SOURCE ADAPTERS / INFRASTRUCTURE / PERSISTENCE
SYMPTOM = Repeated captures at one URL could overwrite or truncate prior raw HTML evidence.
ROOT_CAUSE = URL/locator-derived storage identity was mutable rather than content-addressed.
FIX = Immutable content-addressed raw capture with collision and partial-output guards.
FIX_HEAD = faebb2d8a113a0a8d56d10d4021e68b974c1e3fe
REGRESSION_GUARD = Same URL with different bytes stores both objects; same bytes are idempotent; a corrupt content-address collision fails closed.
INDEPENDENT_AUDIT = PASS
CURRENT_EVIDENCE = PR #74; merge commit bcf5ca60fe933a82c097c6575fd50de63acfca4c; independent implementation audit PASS; final remote audit PASS; post-merge Python CI and CodeQL PASS.
PERMANENT_PREVENTION = URL or locator is never immutable evidence identity; preserve immutable content-addressed source bytes.
```

## FM-012 — Cross-source notice-code aliasing

```text
ID = FM-012
TITLE = Cross-source notice-code aliasing
STATE = MERGED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED
DETECTED_BY = Independent audit of WP-HARDEN-SOURCE-INTEGRITY-01
AFFECTED_BASELINE = PR #74 pre-fix notice identity path
PRODUCT_HOUSE_LAYER = DOMAIN CORE / SOURCE ADAPTERS / PERSISTENCE
SYMPTOM = Equal notice codes from different sources could alias to one record.
ROOT_CAUSE = Source name was omitted from notice identity.
FIX = Scope notice identity by source plus source-local business identity and revision semantics.
FIX_HEAD = faebb2d8a113a0a8d56d10d4021e68b974c1e3fe
REGRESSION_GUARD = Same code across two sources yields two rows; same source/code/revision is one row; different revisions are different rows.
INDEPENDENT_AUDIT = PASS
CURRENT_EVIDENCE = PR #74; merge commit bcf5ca60fe933a82c097c6575fd50de63acfca4c; independent implementation audit PASS; final remote audit PASS; post-merge Python CI and CodeQL PASS.
PERMANENT_PREVENTION = Source-local identifiers are never global identities.
```

## FM-013 — Partial semantic hash diverged from persisted source state

```text
ID = FM-013
TITLE = Partial semantic hash diverged from persisted source state
STATE = MERGED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED
DETECTED_BY = Independent audit of WP-HARDEN-SOURCE-INTEGRITY-01
AFFECTED_BASELINE = PR #74 pre-fix semantic hash path
PRODUCT_HOUSE_LAYER = DOMAIN CORE / APPLICATION BACKEND / PERSISTENCE
SYMPTOM = A semantic hash could remain unchanged while persisted source-derived state changed.
ROOT_CAUSE = Hash input was a subset of the persisted Notice, Attachment and TenderItem state.
FIX = Deterministic canonical serialization covers the persisted source-derived state before hashing.
FIX_HEAD = faebb2d8a113a0a8d56d10d4021e68b974c1e3fe
REGRESSION_GUARD = Notice changes, Attachment filename/state changes and TenderItem persisted-field changes alter the hash; ordering is stable; identical state remains unchanged.
INDEPENDENT_AUDIT = PASS
CURRENT_EVIDENCE = PR #74; merge commit bcf5ca60fe933a82c097c6575fd50de63acfca4c; independent implementation audit PASS; final remote audit PASS; post-merge Python CI and CodeQL PASS.
PERMANENT_PREVENTION = Canonical semantic hashing must cover the persisted source state, not a convenient subset.
```

## FM-014 — Authoritative source snapshot was not reconciled with persisted child membership

```text
ID = FM-014
TITLE = Authoritative source snapshot was not reconciled with persisted child membership
STATE = MERGED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED
DETECTED_BY = Independent Reviewer finding FB-0026 followed by runtime reproduction V2
AFFECTED_BASELINE = main c90e86d6b7a27ecb5a1fb681747bd4c3140de97d
PRODUCT_HOUSE_LAYER = SOURCE ADAPTERS / APPLICATION BACKEND / PERSISTENCE
SYMPTOM = Attachment/TenderItem absent from a later authoritative snapshot remained persisted as current source child state.
ROOT_CAUSE = upsert_parsed_notice() performed additive child upserts without reconciling persisted children absent from the authoritative current snapshot.
WHY_EXISTING_TESTS_MISSED_IT = existing source-integrity tests validated identity/hash/persisted-field change but lacked present→absent and stale-current-membership regressions.
CI_IMPLICATION = semantic hash/current parsed state is insufficient if persisted active membership is not reconciled; current-state consumers and automatic processing must use active membership semantics.
FIX = source lifecycle fields + authoritative active-set reconciliation + inactive automatic-download/retry guards while preserving historical evidence.
FIX_HEAD = 1020ad2b7ab706e586ad3983cd8f7703185f992c
REGRESSION_GUARD = present→absent; partial reconciliation; reactivation; downloaded evidence preservation; inactive download/retry guard; revision isolation; idempotence; hash/active-state alignment.
INDEPENDENT_AUDIT = PASS local + PASS final remote
CURRENT_EVIDENCE = PR #76; merged feature head ad25adf2939fd54f36d4411a1dff526c21dcff76; merge commit 823e33dd34c43dccece8a2d70d248db12c9ee516; post-merge Python CI 33240243556 PASS; CodeQL 33240243744 PASS; Windows 703 passed in 1188.84s.
PERMANENT_PREVENTION = authoritative current snapshots must reconcile active membership explicitly; historical row/evidence retention must remain separate from current source membership.
```

## FM-015 — Windows frozen Qt ICU collision and release smoke false-positive

```text
ID = FM-015
TITLE = Windows frozen Qt ICU collision and release smoke false-positive
STATE = MERGED
SEVERITY_AT_DETECTION = CRITICAL
DISPOSITION = RESOLVED
DETECTED_BY = REL-B fresh Windows candidate build + bounded Phase-3 loader diagnosis
AFFECTED_BASELINE = 6a16eaca9ac84ea568a104e4e0594c0e77db07f1
PRODUCT_HOUSE_LAYER = DELIVERY / PACKAGING / RELEASE ENGINEERING
SYMPTOM = Frozen QI-Crawler failed importing PySide6.QtCore with "The specified procedure could not be found"; prior release smoke could still allow candidate metadata creation despite the frozen process failure.
ROOT_CAUSE = Two proven release-boundary defects: A) PyInstaller collected a foreign Poppler ICU 78 icuuc.dll whose exports were incompatible with the unversioned ICU imports required by Qt6Core.dll. B) build_installer.ps1 did not reliably bind candidate acceptance to the actual frozen child process exit result.
WHY_EXISTING_TESTS_MISSED_IT = Installer tests asserted release-script structure but did not guard native-binary ownership/collision or prove timeout + real child ExitCode semantics.
CI_IMPLICATION = Windows release candidate is blocked until corrected frozen Qt startup and actual-process smoke are independently audited.
FIX = Filter foreign unversioned ICU binaries at PyInstaller packaging ownership boundary; use explicit bounded process wait and actual child ExitCode for standalone smoke.
FIX_HEAD = 4f8d4bb666622de4c4c372796ac114480a524d84
REGRESSION_GUARD = tests/test_windows_installer.py ICU ownership/exclusion contract + explicit process wait/timeout/nonzero-exit release-gate tests + contaminated-host frozen build proof.
INDEPENDENT_AUDIT = PASS
CURRENT_EVIDENCE = Correction audited head 4f8d4bb666622de4c4c372796ac114480a524d84; PR #88 merged; merge commit bf46dbce7501ddf0ae0a7115ddde28eb3b137f62; post-merge Python CI 33645881211 / SUCCESS_4_OF_4; post-merge CodeQL 33645880242 / SUCCESS; REL-B fresh candidate from main independently audited; foreign Poppler ICU absent; frozen Qt 6.11.2 PASS; real smoke ExitCode 0; REL-C installed the exact audited EXE into D:\QI-Crawler; clean second independent REL-C re-audit PASS; no unexplained production data change.
PERMANENT_PREVENTION = Native dependencies with colliding names must be admitted according to package ownership rather than host discovery accident; candidate acceptance must depend on the real frozen process exit result.
```

## FM-016 — Repeated F5 runtime copies exhausted development storage

```text
ID = FM-016
TITLE = Repeated F5 runtime copies exhausted development storage
STATE = RESOLVED_VERIFIED
SEVERITY_AT_DETECTION = CRITICAL
DISPOSITION = GUARD_IMPLEMENTED_LOCALLY / NOT_MERGED
DETECTED_BY = AO-04-C3 capacity preflight and F5-GUARD transition
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = Repeated full runtime copies accumulated across sandbox and evidence trials, causing material development-disk exhaustion and requiring emergency cleanup before AO-04-C3 could continue.
ROOT_CAUSE = Trial tooling allowed repeated runtime or sandbox materialization without sufficient lifecycle and capacity enforcement.
WHY_EXISTING_GATES_MISSED_IT = A storage preflight described available capacity but did not reserve or bound later artifact creation, retries, or concurrent trial materialization.
CI_IMPLICATION = Capacity and artifact-lifecycle claims require point-of-write evidence; a dry-run or available-space snapshot is not proof that a real F5 trial is safe.
FIX = F5-only existing-sandbox route; no new runtime copy; one concurrent trial; zero automatic retries; pre-trial and pre-material-write capacity checks; mid-write failure terminalization; execution-identity binding; external orchestrator lock.
FIX_HEAD = BASE_GIT_HEAD e7dea5c6e07662e963401f795da0cff623be832c6 + LOCAL_FROZEN_WORKTREE_FALLBACK
REGRESSION_GUARD = Independent audit must verify the frozen guard files, exact input identity, capacity gates, no-copy route, single-trial/retry bounds, lock ownership outside the killed process tree, and fail-closed terminalization before any real F5 authorization.
INDEPENDENT_AUDIT = PENDING
CURRENT_EVIDENCE = AO-04-C3-F5-GUARD-01 evidence directory release_staging/evidence/AO-04-C3-F5-GUARD-20260911T043852887Z; frozen guard patch fa29c15ab1db933dcbeb345164693968a64c04cd821396b415fc8eccec29561c; REAL_F5 remains NOT_RUN.
PERMANENT_PREVENTION = Treat preflight capacity as a gate, not a reservation; bound materialization, concurrency and retries at the write point; keep lifecycle ownership outside any process intentionally killed by the experiment; defer general retention/capacity law to a separate governance WP.
```

## FM-017 — Windows PowerShell 5.1 relative-path API incompatibility in F5 guard

```text
ID = FM-017
TITLE = Windows PowerShell 5.1 relative-path API incompatibility in F5 guard
STATE = AUDITED
SEVERITY_AT_DETECTION = IMPORTANT
DISPOSITION = RESOLVED_VERIFIED_BY_INDEPENDENT_REVIEWER
DETECTED_BY = INDEPENDENT_REVIEWER AO-04-C3-F5-GUARD-01
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = F5 guard and probe failed under the target Windows PowerShell 5.1 runtime before corrected dry-run verification.
ROOT_CAUSE = The guard/probe invoked System.IO.Path.GetRelativePath, which is unavailable in Windows PowerShell 5.1, instead of using a bounded compatibility helper.
WHY_EXISTING_TESTS_MISSED_IT = Earlier tests could select pwsh or did not force the target powershell.exe host, so the target runtime API surface was not exercised.
CI_IMPLICATION = No hosted-CI or production claim; the corrected target-runtime regression must remain a required local gate before independent F5 audit.
FIX = Replace the unavailable relative-path call with canonical path-boundary helpers and a .NET SHA-256 stream helper; add powershell.exe boundary, sibling-prefix, nested-descendant and trailing-root regressions while preserving fail-closed containment.
FIX_HEAD = BASE_GIT_HEAD e7dea5c6e07662e963401f795da0cff623be832c + AO-04-C3-F5-GUARD-C1 LOCAL FROZEN WORKTREE FALLBACK
REGRESSION_GUARD = 17-test F5 guard targeted suite under powershell.exe; three-script Windows PowerShell 5.1 parse; full 1088-test suite; no active GetRelativePath/Get-FileHash runtime uses.
INDEPENDENT_AUDIT = AO-04-C3-F5-GUARD-C1 INDEPENDENT RE-AUDIT PASS FOR POWERSHELL_5_1 CORRECTION
CURRENT_EVIDENCE = AO-04-C3-F5-GUARD-C1 independently verified compatibility correction; REAL_F5 remains NOT_RUN; A3 production and power-loss safety remain NOT_PROVEN.
PERMANENT_PREVENTION = Treat the declared Windows PowerShell 5.1 host as an explicit compatibility contract; test actual powershell.exe, keep path containment fail-closed, and require independent audit of the frozen correction before F5 authorization.
```

## FM-018 — Incomplete sandbox reuse bypass through caller-selected EvidenceRoot

```text
ID = FM-018
TITLE = Incomplete sandbox reuse bypass through caller-selected EvidenceRoot
STATE = OPEN
SEVERITY_AT_DETECTION = CRITICAL
DISPOSITION = CORRECTION_LOCALLY_VERIFIED / NOT_MERGED / PENDING_INDEPENDENT_REAUDIT
DETECTED_BY = AO-04-C3-F5-GUARD-C1 independent review / AO-04-C3-F5-GUARD-C2 I1 reproduction
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = An incomplete trial could be retried against the same sandbox by changing EvidenceRoot and RunId because lifecycle state was stored only under the caller-selected evidence directory.
ROOT_CAUSE = Trial lifecycle authority was keyed by per-run EvidenceRoot instead of a stable sandbox resource identity outside the evidence root.
WHY_EXISTING_TESTS_MISSED_IT = Existing coverage exercised incomplete state only within one evidence root and did not vary both the evidence root and run identifier for the same sandbox.
CI_IMPLICATION = No F5, production, or hosted-CI claim; independent audit must verify stable state authority, atomic persistence, fail-closed corruption handling and real filesystem failure behavior.
FIX = Derive a normalized sandbox_resource_id, store lifecycle state and the sandbox lock under the stable control root, atomically replace state files, reject unresolved/corrupt/mismatched state, and keep EvidenceRoot as per-run evidence only.
FIX_HEAD = BASE_GIT_HEAD e7dea5c6e07662e963401f795da0cff623be832c + AO-04-C3-F5-GUARD-C2 LOCAL FROZEN WORKTREE FALLBACK
REGRESSION_GUARD = Same sandbox/different EvidenceRoot and RunId; stale RUNNING; stale POST_KILL_VERIFICATION; corrupt state; different-sandbox isolation; completed reuse; real test-owned filesystem failure with persisted incomplete state; Windows PowerShell 5.1 parse/runtime; input and point-of-use revalidation.
INDEPENDENT_AUDIT = PENDING
CURRENT_EVIDENCE = AO-04-C3-F5-GUARD-C2 local correction evidence; REAL_F5 remains NOT_RUN; A3 production and power-loss safety remain NOT_PROVEN.
PERMANENT_PREVENTION = Lifecycle state must be derived from canonical sandbox identity and never from caller-selected EvidenceRoot; unresolved or unreadable state fails closed and no automatic reconciliation unblocks a sandbox.
```

## FM-019 — Real F5 route unavailable behind the audited existing-sandbox guard

```text
ID = FM-019
TITLE = Real F5 route unavailable behind the audited existing-sandbox guard
STATE = RESOLVED_VERIFIED
SEVERITY_AT_DETECTION = CRITICAL
DISPOSITION = CANONICAL_ROUTE_CORRECTION_INDEPENDENTLY_VERIFIED / REAL_F5_TRIAL_AUTHORIZED_SEPARATELY
DETECTED_BY = AO-04-C3-F5-01 execution-route review
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = The audited guard and probe could select only DryRun; direct RealF5 entry was unavailable, while Sequential mode created forbidden runtime copies.
ROOT_CAUSE = The guard had no explicit handoff object binding lifecycle RUNNING, sandbox, manifest, guard/probe identities and the outer lock to the probe dispatch boundary.
FIX = Add one explicit Invoke-F5CanonicalRoute implementation behind the guard-issued execution context; route F5Only through the existing sandbox without New-Trial, sandbox creation or runtime copy; keep Sequential setup outside the canonical function and call the same P1-P5 implementation after setup; retain context, RUNNING lifecycle, manifest, point-of-use and outer-lock guards; keep the test checkpoint inside the canonical function before real effects.
FIX_HEAD = BASE_GIT_HEAD e7dea5c6e07662e963401f795da0cff623be832c + AO-04-C3-F5-RUNNER-C1 LOCAL FROZEN WORKTREE FALLBACK
REGRESSION_GUARD = RED/GREEN canonical reachability; one-function source proof; Sequential/F5Only shared-call proof; canonical failure propagation; direct-probe context negatives; context drift; lifecycle-not-running; lock-not-held; guarded existing-sandbox dispatch without runtime copy; exclusive-lock contention; C1/C2 guard suite; PowerShell 5.1 parse.
INDEPENDENT_AUDIT = AO-04-C3-F5-RUNNER-C1 INDEPENDENT_PASS
CURRENT_EVIDENCE = AO-04-C3-F5-RUNNER-C1 exact frozen snapshot independently reconciled; AO-04-C3-F5-01-R2 was terminalized before probe dispatch because the nested guard capacity authority returned free=0; production and power-loss safety remain NOT_PROVEN.
PERMANENT_PREVENTION = Real F5 may enter only through a fresh external Work Order using a newly revalidated guard-issued context and the single canonical route; no caller-selected EvidenceRoot, RunId, sandbox or script identity may bypass the outer guard, and F5Only must never fall back to historical setup or create a runtime copy.
```

## FM-020 — Nested PowerShell capacity authority returns a false zero

```text
ID = FM-020
TITLE = Nested Windows PowerShell reports zero free bytes on an otherwise available volume
STATE = RESOLVED_VERIFIED
SEVERITY_AT_DETECTION = CRITICAL
DISPOSITION = R2_TERMINALIZED_FAIL_CLOSED / CAPACITY_C1_INDEPENDENTLY_VERIFIED / R3_AUTHORIZED_SEPARATELY
DETECTED_BY = AO-04-C3-F5-01-R2; AO-04-C3-F5-CAPACITY-C1
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = The outer preflight observed 25913290752 free bytes on D:, while the nested guard process returned Get-PSDrive D Free=0 and rejected the trial at CAPACITY_INSUFFICIENT.
ROOT_CAUSE = The nested guard used Get-PSDrive, whose PowerShell-drive view was not a stable authority for the filesystem volume used by the outer preflight; the same D: volume was available through System.IO.DriveInfo.
FIX = AO-04-C3-F5-CAPACITY-C1 replaces the PowerShell-drive lookup with the Windows PowerShell 5.1-compatible System.IO.DriveInfo.AvailableFreeSpace authority, canonicalized from the absolute filesystem path; invalid/unavailable measurements fail closed as CAPACITY_MEASUREMENT_ERROR and numeric zero remains valid.
CURRENT_EVIDENCE = AO-04-C3-F5-01-R2 terminal evidence; AO-04-C3-F5-CAPACITY-C1 independently verified with targeted guard tests 44 PASS, PowerShell 5.1 parse PASS, and nested outer/child capacity probe PASS. The later R3 one-trial authority was consumed and failed closed at P0; no new RealF5 trial is authorized.
PERMANENT_PREVENTION = Treat contradictory capacity observations as UNKNOWN/FAIL-CLOSED; bind the exact filesystem authority and execution context used at the write gate, require nested Windows PowerShell regression coverage, and require independent review before retrying a critical trial.
```

## FM-021 — RealF5 pre-execution contract incomplete

```text
ID = FM-021
TITLE = RealF5 invocation lacks a complete sandbox-layout and material-write contract
STATE = RESOLVED_VERIFIED
SEVERITY_AT_DETECTION = CRITICAL
DISPOSITION = C2_RECOVERY_AND_FIXTURE_AUTHORITY_CORRECTED_INDEPENDENTLY_VERIFIED
DETECTED_BY = AO-04-C3-F5-01-R3 pre-execution rejection
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = RealF5 reached the guard without a frozen finite capacity peak contract, while the assigned existing sandbox contained runtime/ only and lacked install/, data/, and transaction/.
ROOT_CAUSE = The pre-execution seam did not bind the canonical route's substantive layout and all material write peaks to one audited trial object.
WHY_EXISTING_TESTS_MISSED_IT = Earlier guard tests exercised synthetic dispatch and capacity values but did not require a frozen contract or validate the actual existing-sandbox layout before any real route.
FIX = Bind logical schema-0020 authority to the unchanged C1 seed spec and one exact frozen C1-generated artifact (size/SHA/logical digest); prove the exact historical v0.9 smoke command in child-only isolated roots; enforce six material-write classes; remove development pytest temp from P5; bind fixture, seed spec, recovery semantics, layout, capacity, tool and route identities in one FM021 contract. F5 recovery restores pre-migration executable/control state while DB schema 0020 and generation remain unchanged; 0022-to-0020 downgrade is out of scope.
FIX_HEAD = BASE_GIT_HEAD e7dea5c6e07662e963401f795da0cff623be832c + AO-04-C3-FM021-RESOLUTION-01-C2 LOCAL WORKING OBJECT
REGRESSION_GUARD = Seed logical reproducibility plus frozen-artifact SHA; isolated v0.9 compatibility; bounded JSON/text/process output and census; recovery journal bound; exact schema-0020, seed-spec, physical/logical DB and write-class contract negatives; exact 0022 recovery input fails closed without downgrade; existing guard/observer/recovery regressions; Windows PowerShell 5.1 parse/runtime; full Ruff and full pytest once on C2; no RealF5.
INDEPENDENT_AUDIT = PASS_FOR_AO-04-C3-FM021-RESOLUTION-01-C2 / PLANNER_RECONCILED
CURRENT_EVIDENCE = C1's exact historical v0.9 isolated smoke remains valid for the same frozen artifact. C2 independently re-hashed that artifact and recomputed its 0020 logical digest, corrected the contract to distinguish future disposable 0020-to-0022 compatibility from F5 pre-migration recovery, and proved 0022 input fails closed. Cross-environment physical reproducibility is not required. Six bounded material-write classes and capacity values are unchanged. No RealF5, designated-sandbox mutation or production access occurred.
C1_REVIEW_FINDING = HOLD / RECOVERY_CONTRACT_OVERCONSTRAINED_TO_SCHEMA_DOWNGRADE / PHYSICAL_SQLITE_REPRODUCIBILITY_MODEL_OVERCONSTRAINED
PERMANENT_PREVENTION = RealF5 cannot start without one immutable contract whose exact sandbox, route identity, runtime identity, layout, finite material-write peaks, reserves, and bounded copy/retry/concurrency policy are revalidated at point of use; unknown or drifted inputs fail closed and do not create scaffold directories.
DIAGNOSTIC_BOUNDARY_PREVENTION = Any frozen-runtime compatibility launch must bind a disposable QI_CRAWLER_DATA_DIR and QI_CRAWLER_CONFIG_PATH before process creation; an unbound launch is a production-boundary violation and must stop the active phase even when the attempted write is denied.
```

## FM-022 — Canonical RealF5 controller was outside the dedicated Job Object

```text
ID = FM-022
TITLE = Canonical RealF5 used PID/tree termination while its Job Object proof covered a separate helper process
STATE = RESOLVED_VERIFIED
SEVERITY_AT_DETECTION = CRITICAL
DETECTED_BY = AO-04-C3-A3-CLOSURE-01 pre-materialization review
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c plus frozen local A3 route
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = Invoke-F5CanonicalRoute called Stop-SandboxTree on a controller PID, but never assigned that controller to the Job proven by the independent positive-control helper.
ROOT_CAUSE = The Job Object self-test and the RealF5 controller launch were separate paths; PID-descendant discovery was mistaken for termination authority.
FIX = AO-04-C3-F5-JOB-BARRIER-C1 launches the actual controller suspended, assigns it to a dedicated kill-on-close Job, confirms membership before resume, retains the Job handle in the surviving probe, and uses TerminateJobObject with Job-derived active counts. P2 precedes writer/process and stub revalidation, which precede Job kill and P3.
REGRESSION_GUARD = Synthetic controller-child-grandchild containment and termination; owner-exit kill-on-close; canonical route integration and sequence assertions; guard, observer, preexecution-contract, bounded-I/O and recovery tests; no RealF5.
INDEPENDENT_AUDIT = RESOLVED_VERIFIED_PER_AUTHORIZING_WORK_ORDER
CURRENT_EVIDENCE = FM-022 is resolved per the authoritative Planner work order. RealF5 was not run; A3 sandbox feasibility and production/power-loss safety remain unproven.
PERMANENT_PREVENTION = Bind execution-controller identity and Job-helper identity in the trial contract; require Job membership/count evidence for the same controller that drives the canonical route; never accept PID kill or a separate helper self-test as substitute.
```

## FM-023 — RealF5 observer escaped the sandbox-only observation boundary

```text
ID = FM-023
TITLE = Canonical RealF5 observer could hash production executable and classify production process input
STATE = RESOLVED_VERIFIED
SEVERITY_AT_DETECTION = CRITICAL
DETECTED_BY = AO-04-C3-A3-CLOSURE-01-R2 pre-materialization review
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c plus local A3 route
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = Get-RawCensus iterated every Get-Process result and explicitly included D:\QI-Crawler\QI-Crawler.exe in its hash condition; observer config carried production_paths.
ROOT_CAUSE = Sandbox feasibility process evidence was incorrectly coupled to global-machine and production executable identity.
FIX = AO-04-C3-F5-OBSERVER-BOUNDARY-C1 restricts detailed census to owned Job/route PID trees; generic OS discovery uses PID/PPID only; sandbox file hashes require boundary-aware containment and reparse rejection; Python config rejects production_paths; guard binds observer SHA at point of use.
REGRESSION_GUARD = RED/green synthetic production sentinel, outside/sibling path, disposable external process, mocked census no-outside-hash, FM-021 contract identity, FM-022 Job/barrier, guard and full pytest; no RealF5.
INDEPENDENT_AUDIT = PASS_PER_AO-04-C3-A3-CLOSURE-01-R3_PLANNER_RECONCILIATION
CURRENT_EVIDENCE = Observer Boundary C1 exact eight-file snapshot in release_staging/evidence/AO-04-C3-F5-OBSERVER-BOUNDARY-C1-20260913T040125Z independently accepted under the R3 Work Order. That historical one-trial authority was consumed; the successor native-lineage implementation is pending independent re-audit. A3 production and power-loss safety remain NOT_PROVEN.
PERMANENT_PREVENTION = Treat sandbox observer scope as explicit authority; never infer production safety from sandbox census; bind probe/observer/guard bytes and reject out-of-scope paths before read or hash.
```

## FM-024 — Valid empty P0 process census rejected by bounded I/O binding

```text
ID = FM-024
TITLE = Explicit zero-record P0 census rejected before shared bounded-I/O validation
STATE = RESOLVED_VERIFIED
DETECTED_BY = AO-04-C3-A3-CLOSURE-01-R3 failed sandbox trial at P0
AFFECTED_BASELINE = release/v0.10-recon-01 at e7dea5c6e07662e963401f795da0cff623be832c plus frozen local A3 route
PRODUCT_HOUSE_LAYER = DELIVERY / RELEASE ENGINEERING / TEST INFRASTRUCTURE
SYMPTOM = Windows PowerShell 5.1 rejected an explicit empty object[] at the mandatory Records parameter before Assert-F5BoundedRecords could enforce limits. R3 failed closed at P0; P1-P5 were not reached; its one-trial authorization was consumed.
ROOT_CAUSE = The shared bounded-record parameter lacked AllowEmptyCollection, and an empty result from Get-RawCensus could disappear through PowerShell pipeline enumeration. The empty JSON receipt also serialized as a newline rather than a JSON array.
FIX = Accept only an explicit empty collection at the shared bounded helper, preserve the empty array at Get-RawCensus, serialize zero records as [] through the existing byte and write-class ceilings, and continue to reject null, malformed, over-count and over-byte records. Rebind the changed probe/bounded-helper identities in a new technical contract and fixture-set copy without rewriting historical R3 evidence.
REGRESSION_GUARD = Windows PowerShell 5.1 RED/GREEN parameter binding; zero-record bounded JSON; synthetic P0 observer to next pre-P1 boundary; one/max/max+1/null/malformed/byte-overflow; affected guard/observer/Job/preexecution/recovery tests; full pytest and Ruff. P2 controller/Job activity and P3 Job-zero requirements remain unchanged.
CURRENT_EVIDENCE = AO-04-C3-F5-P0-EMPTY-CENSUS-C1 correction resolved per the subsequent authoritative AO-04-C3-F5-FINAL-INTEGRITY-C1 Work Order. Historical R3 evidence remains immutable with P0 FAILED and lifecycle FAILED. A fresh F5 trial is not authorized by this resolution.
PERMANENT_PREVENTION = Model empty collection separately from null at PowerShell parameter boundaries; keep valid empty data inside shared bounded validation and valid JSON serialization. Technical contracts bind inputs but do not grant execution authority; each RealF5 trial requires a fresh external Planner Work Order.
```

## FM-025 — Zero-byte P1 marker rejected at PowerShell parameter binding

```text
ID = FM-025
STATE = RESOLVED_VERIFIED
SYMPTOM = Canonical P1 cannot persist a valid empty marker because mandatory byte[] binding rejects @() before bounded validation.
ROOT_CAUSE = The shared bounded-byte parameter did not distinguish an explicit empty collection from null.
CORRECTION = Allow an explicit empty byte collection through the same path, count, and write-class checks; null and over-limit content remain fail-closed.
EVIDENCE = Native Windows PowerShell 5.1 RED/GREEN and zero-byte, null, over-limit regressions under AO-04-C3-F5-FINAL-INTEGRITY-C1.
LIMIT = Native-lineage C1 synthetic canonical P0-P5 passed with no skip. This failure mode is resolved by Planner reconciliation; historical R5 remains FAIL and any new RealF5 requires separate authority.
```

## FM-026 — Windows command route fails when path contains spaces

```text
ID = FM-026
STATE = RESOLVED_VERIFIED
SYMPTOM = Canonical P4 CMD launch did not preserve a path containing spaces and an argument containing whitespace.
ROOT_CAUSE = Command invocation lacked an identity-preserving process boundary for .cmd artifacts.
CORRECTION = Launch the exact command artifact through Start-Process with bounded argument conversion and propagate non-zero exit/timeout as failure.
EVIDENCE = Native path-with-spaces and plain-path controls, whitespace argument, and distinctive exit 17 regression.
LIMIT = Native-lineage C1 synthetic canonical P0-P5 passed with no skip. This failure mode is resolved by Planner reconciliation; production execution remains unproven.
```

## FM-027 — Recovery evidence was not fully bound to aggregate verdict

```text
ID = FM-027
STATE = RESOLVED_VERIFIED
SYMPTOM = A recovery outcome could be described without proving same-trial receipt, expected post-barrier refusal, final stub, schema 0020, and physical/logical DB invariance together.
ROOT_CAUSE = Canonical aggregate lacked a complete recovery identity and final DB gate.
CORRECTION = Verify same-trial process and P3 observer receipts, expected MAINTENANCE_RECOVERY_REQUIRED exit 2, canonical stub SHA, DB physical manifest, logical digest, and schema before recovery_verified can enter the aggregate.
EVIDENCE = Positive native disposable receipt and negative missing/malformed/stale, bad exit, DB/digest/schema regressions.
LIMIT = This is pre-migration F5; no schema downgrade or production DB mutation. The failure mode is resolved by Planner reconciliation, without production acceptance.
```

## FM-028 — Shortcut persisted before write-budget gate

```text
ID = FM-028
STATE = RESOLVED_VERIFIED
SYMPTOM = Canonical P4 could create a shortcut before checking the route-artifact budget.
ROOT_CAUSE = Write validation occurred after COM Save.
CORRECTION = Validate a conservative prospective bound and destination first, save to a bounded temporary artifact, verify its actual size, then move into place; remove partial temp on fault.
EVIDENCE = Native Windows shortcut positive, insufficient-budget negative with no artifact, and injected partial-write cleanup regression.
LIMIT = The failure mode is resolved by Planner reconciliation. Capacity values and six write classes are unchanged; no production acceptance follows.
```

## FM-029 — Manifest completeness declared before persistence and verification

```text
ID = FM-029
STATE = RESOLVED_VERIFIED
SYMPTOM = Canonical gate could report evidence_manifest_complete before a persisted manifest was read back and matched to required evidence.
ROOT_CAUSE = Completeness was asserted from an in-memory intent, not an authoritative persisted identity.
CORRECTION = Build, bounded-write, read back, verify trial ID, exact pre-aggregate file set, required paths, sizes and SHA-256, then set verified=true. Post-manifest aggregate/summary outputs are separately excluded to avoid a circular manifest.
EVIDENCE = Native persistence/readback plus missing, truncated, malformed, missing-required, SHA-mismatch, and write-budget negatives.
LIMIT = The failure mode is resolved by Planner reconciliation. Any new F5 trial requires separate authorization and exact evidence.
```

## FM-030 — CIM process lineage access denied before canonical P1

```text
ID = FM-030
STATE = RESOLVED_VERIFIED
SYMPTOM = The canonical synthetic route could not obtain PID/PPID lineage through CIM and held before P1 with access denied.
ROOT_CAUSE = Canonical process observation depended on Win32_Process CIM access outside the disposable sandbox's reliable authority boundary.
CORRECTION = Replace canonical CIM lineage calls with native Toolhelp32 PID/PPID observation; bind the helper identity in the successor technical contract. Use launch ownership and Windows Job Objects, not observation alone, for containment and zero authority.
EVIDENCE = AO-04-C3-F5-NATIVE-LINEAGE-P4-C1 source freeze, native adapter regressions, canonical synthetic P0-P5 PASS with no skip, and S1 non-RealF5 contract validation.
LIMIT = CIM access denial is a historical root trigger, not a claim that production is safe. The failure mode is resolved by Planner reconciliation; RealF5 remains prohibited.
```

## FM-031 — Exited parent creates a false-zero P4 lineage observation

```text
ID = FM-031
STATE = RESOLVED_VERIFIED
SYMPTOM = A launcher or intermediate parent can exit while its child remains alive; a fresh rooted PID/PPID snapshot omits that survivor.
ROOT_CAUSE = Process ancestry is observational and cannot by itself prove termination or absence after a parent exits.
CORRECTION = Launch EXE/CMD/shortcut routes through dedicated Job containment, require route Job active-count and target identity evidence, and refuse false zero even when Toolhelp snapshot succeeds.
EVIDENCE = AO-04-C3-F5-NATIVE-LINEAGE-P4-C1 disposable parent-exit and grandchild reproducers, no-false-zero negative controls, 10-case fail-closed matrix, and S1 code-hash freeze.
LIMIT = An escaped or brokered shortcut on another host remains HOLD. The failure mode is resolved by Planner reconciliation, while sandbox completion and production safety remain unproven.
```

## FM-032 — Frozen maintenance stub companion missing at canonical P4

```text
ID = FM-032
STATE = RESOLVED_VERIFIED
SYMPTOM = R5 reached P3 then first canonical P4 exited 1 before a success receipt.
ROOT_CAUSE = Frozen maintenance stub reads adjacent maintenance_stub_state.json; canonical runner had no producer. Hostname-based rehearsal did not exercise this dependency. P4 did not retain child stderr on failure.
CORRECTION = Bound immutable TX_STATE publication and readback before controller start; verify companion/controller hashes at point of use; capture bounded route output and persist failure receipt; exercise exact frozen stub in disposable regression.
EVIDENCE = release_staging/evidence/FM032-HUMAN-CORRECTION-20260914; exact stub SHA 6f6a4cfdb43d6a63236ee707ddf74ac43b65a49cb2d20e371bb920cd81932f34; missing-state A/B exit 1 versus valid-state exit 0; canonical five-route disposable rehearsal and fail-closed regressions.
LIMIT = R5 remains FAIL and authority consumed. No new RealF5, designated-sandbox reset, production access, migration or release. Old immutable contracts require successor rebind and independent review before a separately authorized trial. Default stub entry proof is not resume/controller-recovery or production safety proof.
PLANNER_EVIDENCE_RECONCILIATION = Eight tests cover exact binary A/B, exact-stub rehearsal, bounded diagnostics, four producer negatives (wrong controller SHA; pre-existing state; changed controller; 1-byte write budget), and overflow. Separate malformed-JSON, missing-key and actual 64-KiB boundary tests were not established by that file. Actual errors are immutable bounded artifact already exists and MATERIAL_WRITE_BOUND_EXCEEDED. Companion contains controller_path and controller_sha256; RunId is in STUB_DEPENDENCY receipt. Exact-stub rehearsal requires -UseFrozenStub. Historical manifest is R5_FAILURE_EVIDENCE_MANIFEST.json.
S2_R1_FINDING = Full 1221-test regression passed with no skip and unchanged execution hashes. Candidate successor contract and fixture include state_max_bytes=65536 even though current producer is bounded by TX_STATE max_per_file_bytes=1048576 with no separate 65536 enforcement. Candidate input manifest also retains an execution_code_freeze pointer to historical S1; a separate S2 freeze is present. Do not promote this S2 candidate to final trial input without bounded successor evidence correction and independent audit. Sandbox remains post-R5 FAILED and needs separately authorized recovery.
S2_R2_CORRECTION = New immutable successor fixture and contract bind the effective stub-state limit to TX_STATE.max_per_file_bytes=1048576, companion fields to controller_path/controller_sha256, RunId to receipts/STUB_DEPENDENCY.json, and exact frozen-stub rehearsal to -UseFrozenStub. New non-RealF5 manifest points to the S2 execution freeze, not historical S1. PreflightOnly identity/write-bound/layout/capacity checks passed with no RealF5 or sandbox mutation; historical S1/R1/R5/FM032 evidence hashes remain unchanged. This is Builder evidence pending independent audit, not trial/recovery/production authority; post-R5 sandbox reentry remains REQUIRES_AUTHORIZED_RECOVERY.
S2_R3_CORRECTION = R2 retained historical S1 paths in untracked_execution_inputs and stale R5 one-trial authorization in route metadata. New R3 manifest reconciles current input lists to 19 validation inputs, binds immutable R2 fixture/contract and S2 freeze, and records R5 as HISTORICAL_FAIL / CONSUMED / RETRY_FORBIDDEN with no current execution authority. Metadata assertions and actual PreflightOnly passed. Full 1221/no-skip regression is evidence on the S2-R1 execution object, reusable only for verified frozen execution scope; exact full-test-tree byte identity was not independently proven. R3 manifest is pending independent audit; sandbox still requires authorized recovery.
```

## FM-033 — Pretrial and post-barrier executable identities conflated

```text
ID = FM-033
STATE = IMPLEMENTED_PENDING_INDEPENDENT_AUDIT
SYMPTOM = R2 preexecution identity accepted the maintenance stub at the canonical install path, while authorized rearm requires frozen v0.9 at that same path. A contract-only phase declaration would be ignored by the guard.
ROOT_CAUSE = The historical guard schema had one canonical executable fixture identity and no observed phase enforcement. The controller correctly stages/verifies the stub before BARRIER_CONFIRMED, so stub presence alone cannot mean post-barrier authority.
CORRECTION = Add a successor phase-aware schema and shared read-only phase observer. Fresh preflight requires PRETRIAL v0.9 with no companion/journal; the canonical route asserts CUTOVER_STUB_STAGED at the pre-barrier marker and POST_BARRIER_MAINTENANCE only after barrier confirmation, retaining FM032 and all Job/writer/DB/recovery gates. Historical contracts are preserved as evidence but cannot authorize a new RealF5 trial.
EVIDENCE = release_staging/evidence/AO-04-C3-A3-PHASE-GUARD-C1-20260914T062343Z; RED 3 cases, targeted phase/route regressions, exact frozen-stub disposable rehearsal, full 1238-pass no-skip suite, 12/12 post-test execution hashes, and current R5 sandbox PRETRIAL preflight refusal.
LIMIT = Builder evidence pending independent audit. Current sandbox remains POST_BARRIER_FAILED and requires separately authorized rearm. No RealF5, production access, DB migration or release was authorized or performed.
```

## FM-034 — CI tests implicitly require developer release artifacts

```text
ID = FM-034
STATE = INDEPENDENTLY_REVIEWED_CANDIDATE_AWAITING_HUMAN_INTEGRATION
PRODUCT_HOUSE_LAYER = ENGINEERING TOOLBOX / CI / TEST INFRASTRUCTURE
SYMPTOM = Hosted Windows run 34935783050 at 6069980 failed 23 tests while Linux jobs passed; historical controller and candidate EXE paths did not exist on the runner.
ROOT_CAUSE = Probe release initialization preceded a validated no-execution dispatch checkpoint; synthetic tests loaded an untracked historical controller even without UseFrozenStub.
CORRECTION = Isolate the existing dispatch checkpoint from release payload loading after context/held-lock validation; use a tracked synthetic handshake actor for synthetic canonical tests. Real release and UseFrozenStub paths retain their artifact checks.
PREVENTION = Ordinary product/engineering tests must reproduce from tracked inputs and declared dependencies; inject historical-path refusal in portability regression. Never replace release acceptance with a synthetic PASS.
EVIDENCE = QI-PR103-CI-PORTABILITY-GATES-01 Work Order and Builder report; hosted final verification belongs to live GitHub and integration handoff.
LIMIT = No RealF5, production safety or release acceptance claim. Local artifact presence can mask runner failures; cross-platform CI remains required.
```

## FM-035 — Reused Windows PID creates false process ancestry

```text
ID = FM-035
STATE = INDEPENDENTLY_REVIEWED_CANDIDATE_AWAITING_HUMAN_INTEGRATION
PRODUCT_HOUSE_LAYER = ENGINEERING TOOLBOX / PROCESS OBSERVATION
SYMPTOM = Local full CI-correction suite failed p4_unknown before P1; native tree listed four IDs while the new controller Job Object held two active processes.
ROOT_CAUSE = Bare Toolhelp PPID traversal treated a long-lived unrelated process as a descendant of a newly reused PID. Observed PID 8688 started at 2026-09-15T05:22:03+07:00, before controller Job receipt 2026-09-15T06:53:40Z; that ancestry is impossible.
CORRECTION = Validate candidate parent-child creation chronology in Get-ProcessTreeEvidence. A proven older child is excluded with a rejected-edge receipt; unavailable creation metadata yields PARTIAL/UNRESOLVED. Job membership is not used to suppress unknown ancestry. Raw Toolhelp snapshot success is reported separately from ancestry completeness; an exited parent with unavailable creation identity remains UNRESOLVED.
PREVENTION = PID and PPID alone are not stable process identity. Preserve lifetime evidence and keep unknown metadata fail-closed; retain real Job containment and fault-specific assertions.
EVIDENCE = QI-PR103-CI-PORTABILITY-GATES-01 full.xml failure and retained full-run temp tree; deterministic valid/older-child/unknown-child/unknown-parent regressions in test_a3_native_lineage.py.
LIMIT = No RealF5/release acceptance; no claim that all process identity races are eliminated. Independent audit and fresh hosted verification remain required.
```

## FM-036 - Maintenance ownership outlives failed journal I/O

```text
ID = FM-036
STATE = INDEPENDENTLY_REVIEWED_CANDIDATE_AWAITING_HUMAN_INTEGRATION
PRODUCT_HOUSE_LAYER = ENGINEERING TOOLBOX / FUTURE MAINTENANCE PRIMITIVE
ROOT_CAUSE = Journal writes after SQLite/owner acquisition escaped cleanup; serial rollback/close/release could strand later resources. Recovery selected a pre-lock journal that a current owner could complete before acquisition.
CORRECTION = Protect fallible acquired-resource paths, attempt each cleanup independently while retaining the original exception, publish in-memory COMPLETE only after durable write, and select/read recovery journal under the owner lock.
PREVENTION = Lock ownership covers both decision inputs and writes. Storage-failure tests must prove DB and owner reacquisition, incomplete durable state, independent cleanup and completion interleavings.
EVIDENCE = Independent cumulative review C1/C2 and forward correction tests/test_update_transaction.py; Builder report follow-up.
LIMIT = No runtime caller beyond tests discovered; unintegrated primitive, no current release/data corruption or fully atomic DB+journal commit claim.
```

## FM-037 — Material dispatch used a self-declared authority label while the active handoff was stale

```text
ID = FM-037
STATE = OPEN_GOVERNANCE_PREVENTION_RECORDED
TITLE = MATERIAL_EXECUTION_PROCEEDED_WITH_SELF_DECLARED_AUTHORITY_REF_WHILE_CANONICAL_HANDOFF_WAS_STALE
OBSERVED = The executor evidence contained an authority_ref label, while independent review could not locate the original Human receipt and CURRENT still represented the old rearm-decision state.
IMPACT = Pre-execution Human authority provenance cannot be independently verified.
NONCLAIM = This does not prove that Human never authorized the execution.
PREVENTION = PRE_DISPATCH_AUTHORITY_GATE requires: (1) current CURRENT authority state; (2) an immutable locator to the original Human decision; (3) receipt predating dispatch; (4) receipt scope matching the WP; (5) matching baseline; (6) matching run/trial budget; and (7) independent Builder/Reviewer resolution. SELF_DECLARED_AUTHORITY_REF_ONLY is INSUFFICIENT. STALE_CURRENT_AT_MATERIAL_DISPATCH is ENTRY_HOLD.
EVIDENCE = Reviewer governance verdict HOLD_GOVERNANCE_AUTHORITY_EVIDENCE for RunId A3-F5-REALF5-20260917T065744Z; Human A0 post-execution disposition dated 2026-09-17.
LIMIT = The post-execution disposition retains technical evidence and the governance hold. It is not retroactive preauthorization. If a valid original receipt is found, the next action is documentary authority reaudit only; no RealF5 rerun.
```

## FM-038 — Successful RealF5 path emitted a contradictory not-executed marker

```text
ID = FM-038
STATE = OPEN_TRACKED_REPORTING_DEFECT
TITLE = REALF5_SUCCESS_PATH_EMITS_F5_EXECUTED_NO
OWNER = RELEASE_ENGINEERING
SYMPTOM = The successful guarded route emitted REAL_F5_DISPATCH=PASS and F5_EXECUTED=NO for the same run.
IMPACT = A Human operator or future machine parser may misclassify an executed trial as not executed.
HISTORICAL_TRIAL_DISPOSITION = Execution is established by lifecycle PREPARED/RUNNING/COMPLETED, the RealF5 execution context, P0-P5 receipts, BARRIER_CONFIRMED journal and final POST_BARRIER_MAINTENANCE physical state.
CONSUMER_AUDIT = Producers found in tools/release/a3_f5_guard.ps1 and tools/release/a3_probe_windows.ps1; assertions found in tests/test_a3_f5_guard.py; one historical handoff reference found; active machine parser NOT_FOUND.
PREVENTION = Give markers single documented meanings that distinguish PREFLIGHT_NOT_EXECUTED, TEST_CHECKPOINT_NOT_EXECUTED, REALF5_DISPATCHED, REALF5_TRIAL_EXECUTED and REALF5_FINAL_RESULT. Never emit a generic false marker on a successfully executed RealF5 path.
FIX_METHOD = SEPARATE_TDD_MICRO_WP
REALF5_RERUN = FORBIDDEN_FOR_LOG_COSMETICS
LIMIT = Preserve the contradictory historical output and durable execution evidence. Fix reporting semantics separately without rewriting the trial or claiming A3/F5 clean close.
```

## FM-039 — Equivalent synthetic seeds produced different physical SHA values

```text
ID = FM-039
STATE = IMPLEMENTED_PENDING_INDEPENDENT_AUDIT
PRODUCT_HOUSE_LAYER = ENGINEERING TOOLBOX / A3 SYNTHETIC SEED
SYMPTOM = Synthetic schema-0020 seeds could have identical logical identity, revision, size, PRAGMA state and integrity but intermittently different physical SHA values on Windows.
ROOT_CAUSE = The physical canonicalizer replayed sqlite3 iterdump schema-object ordering without normalizing order-insensitive post-table index and trigger DDL.
TRIGGER = Equivalent sqlite_schema index serialization order differed between otherwise equivalent seed generations.
CORRECTION = Preserve complete iterdump statements as atomic units while deterministically sorting CREATE INDEX, CREATE UNIQUE INDEX and CREATE TRIGGER statements before replay and COMMIT.
PREVENTION = A regression creates equivalent databases with opposite index-creation orders and proves one-pass physical convergence, logical preservation and idempotence; the generator contract samples six independent seeds without weakening physical identity checks.
EVIDENCE = V10D2 isolated 4,767 differing bytes on pages 120 and 151 with identical logical digest and integrity; V10D3 RED reproduced different post-canonicalization SHA values, then GREEN converged after deterministic post-schema ordering. Focused seed suite, three independent six-seed runs, 48 adjacent A3 tests and the 1,336-test full repository suite passed.
LIMIT = This correction covers the proven schema-object ordering boundary. It does not claim that all SQLite physical nondeterminism is eliminated, does not alter user data, and grants no RealF5, candidate-build, migration, release or promotion authority.
```

## FM-040 — WAL-backed source drift bypassed a main-file-only candidate guard

```text
ID = FM-040
STATE = IMPLEMENTED_PENDING_INDEPENDENT_REAUDIT
PRODUCT_HOUSE_LAYER = RELEASE ENGINEERING / CANDIDATE DATA SAFETY
SYMPTOM = A concurrent SQLite WAL commit could change the logical source database while the main egp.db SHA remained unchanged, allowing candidate preparation to emit COMPLETE from separately observed schema, document and backup states.
ROOT_CAUSE = Candidate preparation used separate source connections for metadata and backup, and treated main-file SHA equality as the database quiescence signal.
CORRECTION = Use one persistent read-only/query-only source connection, pin one explicit read transaction for schema, Document tuples and Online Backup, verify the candidate schema and exact tuples before rebase, end the transaction, then compare same-connection PRAGMA data_version. Bound backup progress with a 30-second monotonic deadline and record main/WAL/SHM observations without treating SHM byte activity as business mutation.
PREVENTION = Deterministic barriers commit real WAL transactions after metadata and after backup; both must fail closed even when the main DB SHA is unchanged. Static committed WAL state must clone successfully without a source checkpoint, and deadline expiry must leave an INCOMPLETE receipt.
EVIDENCE = PR116-AUDIT-CORRECTION-R2 targeted candidate-data regression; exact correction head and hosted CI are re-resolved at independent re-audit.
LIMIT = Synthetic candidate preparation only. No real Team Bid clone, migration, source checkpoint, working-data mutation, candidate build or release was performed.
```

## FM-041 — Publisher accepted mutually inconsistent release provenance

```text
ID = FM-041
STATE = IMPLEMENTED_PENDING_INDEPENDENT_REAUDIT
PRODUCT_HOUSE_LAYER = RELEASE ENGINEERING / PROVENANCE
SYMPTOM = A candidate could pass publisher validation when release_manifest.json, release_artifact_receipt.json and BUILD_INFO.txt disagreed on source SHA, branch, timestamp or other release identity fields.
ROOT_CAUSE = Publisher validation checked only a subset of JSON fields and searched BUILD_INFO using loose substring matches rather than an exact key/value parser.
CORRECTION = Require and validate supported schemas plus product, canonical SemVer, 40-hex source SHA, non-empty branch, normalized UTC timestamp, expected Alembic head and 64-hex hashes; cross-check every shared manifest/receipt field; parse BUILD_INFO as unique non-empty key=value records and require exact manifest equality.
PREVENTION = Negative tests cover missing, empty, malformed, duplicate and mixed provenance, including every shared identity field and both artifact hashes, while preserving a valid publish/rotation control.
EVIDENCE = PR116-AUDIT-CORRECTION-R2 Windows publisher regressions; exact correction head and hosted CI are re-resolved at independent re-audit.
LIMIT = This validates declared provenance consistency. Matching the declared source SHA to the future frozen build source remains a mandatory candidate-build acceptance gate.
```

## FM-042 — Candidate migration provenance trusted a caller-declared Git SHA

```text
ID = FM-042
STATE = AUDITED
PRODUCT_HOUSE_LAYER = RELEASE ENGINEERING / CANDIDATE MIGRATION
SYMPTOM = A migration receipt could name source commit X while executing migration scripts or controlling Python orchestration from a different or dirty checkout.
ROOT_CAUSE = Stage 2 initially trusted a caller-provided source_git_sha, then proved checkout and migration-script identity without proving that the actually loaded candidate-readiness, candidate-data, migration and database modules came from the same frozen Git object.
CORRECTION = Require an explicit source repository root and expected frozen commit; verify exact worktree root, commit object, HEAD and whole tracked-tree cleanliness; bind every executed migration script, actually loaded controlling Python module, alembic.ini and alembic/env.py to its canonical path and Git blob before backup or Alembic execution.
PREVENTION = Reject foreign module origins, same-path byte drift, replaced callable origins and Alembic configuration drift; retain detached exact-HEAD, untracked-output, wrong-head, dirty-source, missing-repo and migration-blob regressions; persist and revalidate execution-code identity in the migration receipt.
EVIDENCE = PR117 final F01 correction; 53 candidate-readiness tests, 86 adjacent tests and the full 1422-test repository suite passed locally at correction code head 747cf9f.
INDEPENDENT_FINAL_F01_REAUDIT = PASS
AUDITED_CODE_HEAD = 747cf9faac95a3bb98840e9b721207993e049ab9
AUDITED_PR_HEAD = 81e9ab97643a430609995d8e0301aa18fd573dcc
F05_REGRESSION_CHECK = RESOLVED_UNCHANGED
LIMIT = Verification has an accepted controlled-build TOCTOU limitation: the Single Writer, clean frozen checkout and no-concurrent-source-mutation contract must hold after verification. Evidence remains synthetic; final source freeze, real business-data migration, candidate build and release remain unauthorized and unproven.
```

## FM-043 — Portable readiness depended on an installer-only receipt schema

```text
ID = FM-043
STATE = AUDITED
PRODUCT_HOUSE_LAYER = RELEASE ENGINEERING / PORTABLE ARTIFACT IDENTITY
SYMPTOM = Stage 3 expected an installer receipt containing installer_sha256 even though the installer gate was explicitly deferred.
ROOT_CAUSE = Portable and installer artifacts shared one lifecycle identity, leaving no legitimate producer for portable-only acceptance without a placeholder installer hash.
CORRECTION = Add write-once portable_artifact_receipt.json with qi-crawler-portable-artifact-v1, generated from the actual EXE, release manifest and BUILD_INFO; reject missing, installer-only, extra-field and mismatched identities.
PREVENTION = Keep portable and installer receipts separate; portable readiness contains no installer SHA and does not require Inno Setup.
EVIDENCE = PR117 readiness correction F02; producer/consumer and tamper regressions plus full 1415-test repository suite passed locally at correction code head 3b031ec.
INDEPENDENT_READINESS_REAUDIT = PASS
F05_REGRESSION_CHECK = RESOLVED_UNCHANGED
LIMIT = This proves the synthetic portable identity contract, not a final PyInstaller artifact, installer, packaging acceptance, publication or promotion.
```

## FM-044 — Unaccepted candidate direct start could fall back to working user data

```text
ID = FM-044
STATE = AUDITED
PRODUCT_HOUSE_LAYER = APPLICATION / RELEASE RUNTIME GATE
SYMPTOM = Double-clicking an INTERNAL_CANDIDATE EXE could reach standalone runtime preparation and default to %LOCALAPPDATA%\QI-Crawler before Stage 3 acceptance; a failed first Popen also made the write-once acceptance unusable for retry.
ROOT_CAUSE = Candidate authorization occurred only in the external controlled launcher, after the raw GUI entry path had already selected its data root; acceptance creation and process-start success were conflated.
CORRECTION = Identify the frozen candidate from adjacent release metadata before runtime preparation; fail closed on missing/malformed governed-layout metadata; require and validate immutable acceptance for normal direct start; bind candidate data/config roots; allow only explicitly isolated preacceptance smoke. Preserve acceptance after launch failure and reuse it after validation. Current operational DB bytes may change after acceptance.
PREVENTION = Test preacceptance refusal before preparation, no LOCALAPPDATA fallback, foreign/tampered acceptance, accepted direct binding, post-start DB mutation, isolated smoke, GUI gate ordering and launch retry.
EVIDENCE = PR117 readiness correction F03/F04; 226 adjacent regressions and full 1415-test repository suite passed locally at correction code head 3b031ec.
INDEPENDENT_READINESS_REAUDIT = PASS
F05_ADJACENT_HARDENING = PASS
LIMIT = Synthetic/runtime-entry verification only. Actual frozen-process B04 cases remain mandatory after a real candidate build; no business GUI startup or user-data mutation was performed.
```

## FM-045 — Accepted candidate database environment override escaped candidate root

```text
ID = FM-045
STATE = AUDITED
PRODUCT_HOUSE_LAYER = APPLICATION / RELEASE RUNTIME ISOLATION
SYMPTOM = An accepted candidate could bind candidate DATA_DIR and CONFIG_PATH while QI_CRAWLER_DATABASE_URL inherited from the process or loaded from .env later selected a database outside the candidate boundary.
ROOT_CAUSE = Candidate bound data/config roots but EnvSettings could later override the effective database target.
CORRECTION = Bind the candidate DATABASE_URL and validate the post-load effective database target before Database construction.
PREVENTION = Regressions cover inherited environment, .env, both override sources together, direct startup, controlled launcher, isolated smoke, invalid effective targets, no Database construction on rejection, and preservation of ordinary non-candidate overrides.
EVIDENCE = PR117 F05 correction RED reproduced all four missing boundaries; GREEN passed 13 focused tests, 131 adjacent tests and the full 1433-test repository suite at code head b4d38baabd8b9473f7d9079a2b59e1d888c6af3a.
INDEPENDENT_F05_REAUDIT = PASS_F05_RUNTIME_DB_ISOLATION_REAUDIT
AUDITED_CODE_HEAD = b4d38baabd8b9473f7d9079a2b59e1d888c6af3a
AUDITED_PR_HEAD = 08b405f5789959d146f300e6f161c04a76043435
NON_CANDIDATE_COMPATIBILITY = PRESERVED
LIMIT = Synthetic runtime-boundary verification only. No real candidate, working database, user data, migration, build, release or promotion was accessed or performed. This audit state does not mean merged.
```

## FM-046 — Legacy standalone source config omitted document_dir and blocked candidate clone

```text
ID = FM-046
STATE = AUDITED
PRODUCT_HOUSE_LAYER = RELEASE ENGINEERING / CANDIDATE DATA COMPATIBILITY
SYMPTOM = Real operational v0.9 source at schema 0020 could not enter isolated candidate clone because its config omitted storage.document_dir.
ROOT_CAUSE = candidate_data parsed raw YAML as though document_dir were mandatory instead of preserving the legacy standalone default semantics.
CORRECTION = Apply the omitted-field fallback source/data/documents, retain source and managed-record containment and reparse guards, and record explicit-vs-legacy source-root provenance in the COMPLETE clone receipt.
PREVENTION = TDD regressions cover omitted, explicit-relative, explicit-absolute, external, empty, null, invalid-type, zero-document, reparse, stored-path escape and source-config immutability cases.
INDEPENDENT_COMPAT_AUDIT = PASS_LEGACY_SOURCE_CONFIG_COMPAT_AUDIT
AUDITED_CODE_HEAD = 1105ebd4e5a0cf48dd8c0ba036455ed4773de14a
AUDITED_PR_HEAD = 168867f52dd1f2036c6ffcccb22088b2c14406f4
LIMIT = Synthetic correction until independent audit and Build Attempt #2. No real Team Bid clone, migration, acceptance, startup, build retry, source-data mutation, release or promotion was performed.
```

## FM-047 — Frozen execution binding rejected clean Windows CRLF checkout

```text
ID = FM-047
STATE = AUDITED
INDEPENDENT_EOL_COMPAT_AUDIT = PASS_FROZEN_EXECUTION_EOL_COMPAT_AUDIT
CORRECTION_MERGED = YES
MERGED_MAIN_SHA = f6782d7eefb292870f8c78404e6c3e83f5fab1e2
PRODUCT_HOUSE_LAYER = RELEASE ENGINEERING / FROZEN EXECUTION PROVENANCE
SYMPTOM = Build Attempt #2 passed portable build, B04 and real isolated clone, then migration execution binding rejected a clean exact frozen Windows checkout before Alembic execution.
ROOT_CAUSE = Frozen execution identity required raw working-tree bytes to equal Git blob bytes while candidate-readiness tests forced core.autocrlf=false. A legitimate Windows core.autocrlf=true checkout stores LF in Git but materializes CRLF in the working tree.
CORRECTION = Retain exact HEAD, tracked-clean, path, callable and Git-object binding while accepting only RAW_EXACT or narrowly proven CRLF_WORKTREE_EQUIVALENT content.
PREVENTION = Real temporary Git tests cover clean LF and clean CRLF worktrees plus substantive tamper rejection for execution modules, Alembic configuration and migration scripts.
LIMIT = Synthetic correction only until independent audit and a future Build Attempt #3. Attempt #2 was not retried.
```

## FM-048 — Operational promotion persisted staging storage paths after cutover

```text
ID = FM-048
STATE = LOCAL_CORRECTION_PENDING_INDEPENDENT_AUDIT
PRODUCT_HOUSE_LAYER = RELEASE ENGINEERING / OPERATIONAL CONFIG
SYMPTOM = The one-shot v0.10 promotion reported PROMOTED_LIVE, but the live persisted config still pointed its database and storage directories at the removed staging root; runtime acceptance was stopped before app launch.
ROOT_CAUSE = Staging config was rewritten with absolute stage paths, then only receipt paths were rebound after directory rotation. Final acceptance checked config existence, not its persisted bindings.
CORRECTION = Validate the stage first, rebind staged config to future final paths before rotation, validate that binding without writes, and require the same binding during final/startup acceptance.
PREVENTION = Synthetic promotion and negative config tests cover all seven keys, malformed/missing values, outside paths, pre-cutover ordering and final acceptance; symlink tests are conditional on host permission.
LIMIT = Source/test correction only. Existing live config was not changed, the app was not started, and independent audit plus a separate live remediation remain pending.
```

## FM-049 — Immutable DB SHA blocked legitimate operational restart

```text
ID = FM-049
STATE = LOCAL_CORRECTION_PENDING_INDEPENDENT_AUDIT
PRODUCT_HOUSE_LAYER = APPLICATION / OPERATIONAL DATABASE STARTUP
SYMPTOM = A fixture-backed real authorization path rejected startup after one committed legitimate SQLite write with OPERATIONAL_DATABASE_SHA_MISMATCH.
ROOT_CAUSE = Startup compared the current mutable DB file SHA to the immutable cutover acceptance SHA.
CORRECTION = Treat acceptance.database_sha256 as historical promotion-baseline evidence equal to migration_receipt.output_db_sha256; retain exact path, schema/readability, release identity and migration receipt checks.
PREVENTION = RED/GREEN restart regression proves persisted write survives; wrong schema, unusable DB and tampered receipt controls remain fail-closed. A new application build cannot truthfully reuse the v1 receipt's coupled source/migration SHA without a separate update contract.
LIMIT = No live startup, DB mutation, app replacement or new promotion. Startup schema/readability is not a full SQLite integrity scan; Windows symlink creation was unavailable in the local test host.
```

## Routing

Read only entries relevant to the active capability or failure path. A new
Parent reads affected layers; an incident reads the matching symptom/path; a
material audit or recovery may broaden the read. For an unrelated Micro-WP,
`N/A` is acceptable. This file does not authorize implementation, alter
Ground Truth, or close the full-repository audit by itself.
