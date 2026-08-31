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
CURRENT_EVIDENCE = tests/conftest.py:11-22 monkeypatches require_current_schema and Database.create_all
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
ROOT_CAUSE = Verified root-cause class is material GitHub-hosted Windows runner performance variance across otherwise equivalent executions. The exact underlying host resource mechanism (CPU scheduling, disk I/O, VM contention or equivalent) is REQUIRES_VERIFICATION because available GitHub telemetry does not expose it directly. Filesystem, temporary SQLite and repeated Alembic test lifecycle work are demonstrated runtime amplifiers, not proven production defects.
WHY_EXISTING_TESTS_MISSED_IT = Functional correctness tests detect assertion failures but do not prove a stable hosted-runner runtime envelope. The test suite can remain correct while infrastructure/runtime variance exhausts the CI job budget.
CI_IMPLICATION = A repeated timeout or cancellation is not PASS and is not automatically a product regression. Preserve exact-run timing evidence, compare healthy and degraded executions, perform bounded attribution, and only then alter a runtime budget. Hosted CI waiver is not justified while hosted CI itself is functioning.
FIX = Raise only the Windows 3.12 hard job ceiling from 25 to 35 minutes after root-cause-class investigation; retain full regression and runtime attribution unchanged.
FIX_HEAD = db19f42985030f2b154804f959fca615c523a06e
REGRESSION_GUARD = The full Windows 3.12 required gate remains mandatory. A future execution that exceeds the 45-minute ceiling must HOLD and reopen runtime/test-harness investigation instead of recursively increasing the timeout.
INDEPENDENT_AUDIT = PASS
CURRENT_EVIDENCE = PR #64 merged feature head db19f42985030f2b154804f959fca615c523a06e; merge commit d10445fc2ffc92e810f0d6258160151efc1c846f; exact-head local 628 passed in 253.40s; exact merged-head Python CI run 32987119489 passed all four required jobs with no CI waiver; Windows 3.12 passed under the bounded 35-minute ceiling. Earlier evidence remains: exact investigated head 269a6d19539091eab5b903e2684b66ebdf9116ae; healthy hosted Windows 628 PASS in approximately 709s; two hosted executions reached 620 PASS in approximately 1404-1425s before cancellation without assertion failure; migration benchmark showed fresh upgrade_database() median approximately 0.8973s versus current-schema verification approximately 0.0018s; no process leak or real-network dependency was reproduced locally.
FORWARD_CORRECTION = PR #82 changed only the Windows 3.12 timeout from 35 to 45 minutes after the two reproduced 35-minute cancellations; product and test behavior were unchanged.
FORWARD_CORRECTION_HEAD = 03056fe147c3263cf8fb2ea39e63dc239e35fffe
EXACT_HEAD_PYTHON_CI = 33381474192 / PASS
POST_MERGE_MAIN_PYTHON_CI = 33384009634 / PASS
POST_MERGE_MAIN_CODEQL = 33384009691 / PASS
CURRENT_WINDOWS_CEILING = 45_MINUTES
PERMANENT_PREVENTION = Treat timeout boundaries as symptoms until runtime attribution is complete. Retain this failure together with FM-008 and systemic lessons as evidence for future test-harness and CI architecture improvement. Another material breach of the 45-minute ceiling requires renewed attribution and HOLD; do not recursively inflate the timeout.
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

## Routing

Read only entries relevant to the active capability or failure path. A new
Parent reads affected layers; an incident reads the matching symptom/path; a
material audit or recovery may broaden the read. For an unrelated Micro-WP,
`N/A` is acceptable. This file does not authorize implementation, alter
Ground Truth, or close the full-repository audit by itself.
