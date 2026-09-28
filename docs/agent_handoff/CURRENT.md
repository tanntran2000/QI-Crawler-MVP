# QI-Crawler Agent Handoff

## G1-C01 — single-node setup diagnosis active

The Tester consumed the one authorized full sequential run, but its output lost the shared setup traceback: 1,780 setup errors, one skip, two warnings, exit 1. Planner authorized one bounded diagnostic test node to recover the common traceback. The cause remains UNKNOWN until that evidence is read. No replacement full-suite run is authorized. G1 remains a local candidate; no build, release, publication, installed launch, operational update, shortcut edit, migration, restore, real legacy archive, cleanup, or product capability promotion occurred. The prior installed-startup recovery backup remains `KEEP_RECOVERY`.

~~~text
HANDOFF_ID = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-G1-C01-BUILDER-DIAGNOSTIC-20260929
WORK_ORDER_ID = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01 rev2-corr1
ROLE = BUILDER_SINGLE_WRITER
HANDOFF_TO = BUILDER_SINGLE_WRITER; PLANNER-ASSIGNED G1-C01 DIAGNOSTIC
CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
BUILDER_GIT_TOPLEVEL = D:/QI Technology/QI Crawler/egp-crawler-python
BUILDER_GIT_DIR = D:/QI Technology/QI Crawler/egp-crawler-python/.git
BUILDER_GIT_COMMON_DIR = .git
BUILDER_ORIGIN = https://github.com/tanntran2000/QI-Crawler-MVP.git
CHECKOUT_IDENTITY_GATE = PASS
ACTIVE_BRANCH = codex/single-installation-legacy-root-retirement-01
INTEGRATION_BASE = origin/main caf983691da60d4eaf990d09e9e1788692aabaac
PARENT_ENTRY_HEAD = 211c0ddbfdcfc7fb249cebd2b449f65d6ea91186
CARRIED_GOVERNANCE_RANGE = caf983691da60d4eaf990d09e9e1788692aabaac..211c0ddbfdcfc7fb249cebd2b449f65d6ea91186; TEN COMMITS PRESERVED IN ORDER
LIVE_ORIGIN_MAIN = UNVERIFIED; git ls-remote COULD NOT CONNECT; LOCAL origin/main REMAINS caf983691da60d4eaf990d09e9e1788692aabaac; NO REMOTE MUTATION
PREVIOUS_BRANCH = codex/installed-startup-recovery-01 at 211c0ddbfdcfc7fb249cebd2b449f65d6ea91186; PRESERVED
PREVIOUS_WP = WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01 rev2; STAGE 2 RETURNED; SHORTCUT EDIT INELIGIBLE
PREVIOUS_PARENT_SNAPSHOT = docs/agent_handoff/history/CURRENT_parent_installed_startup_recovery_stage2_20260928.md; EXACT PARENT CURRENT COPY; SHA256 6283734080D991AEEFBF4232AD87D39C55EF87038D132A9E5700774AAAEC4863
ROADMAP_REVISION = 1.3
ROADMAP_BASELINE_SHA = 7e092f02ce646ca7e4336b4a9b005b30229745b7
ROADMAP_DELTA_BASELINE_SHA = 77bba2be7bec628ce7f014a20ff02a564f4f2ffc
PRODUCT_FRONTIER = UNIFIED TENDER WAREHOUSE; PARTIAL; NO CAPABILITY MATURITY PROMOTION
ROADMAP_NODE = CROSS-CUTTING WINDOWS / TEAM BID DELIVERY; ENGINEERING TOOLBOX / PLUGINS SUPPORTING
ROADMAP_ENTRY_GATE = PASS; FULL READ AT PARENT ENTRY; ALIGNED
ROLE_ENTRY_GATE = PASS; HUMAN-ASSIGNED BUILDER + APPROVED WORK ORDER + CURRENT RECONCILE
HANDOFF_CAPTURE_BASE = a3c5d63342bec5d564ee930151c2aa7d53f54b0f; VERIFIED LOCAL PRE-SYNC HEAD FOR THIS BLOCKER TRANSITION
LOCAL_PRE_SYNC_HEAD = a3c5d63342bec5d564ee930151c2aa7d53f54b0f; PRE-SYNC ONLY; DO NOT PREDICT THE CURRENT COMMIT
LIVE_GIT_HEAD = a3c5d63342bec5d564ee930151c2aa7d53f54b0f; VERIFIED LOCAL PRE-SYNC HEAD; RE-RESOLVE AT READ-IN
AUDIT_TARGET_CODE_HEAD = 795c554246c13b838e4cb9a6d434159ab09efbfe; exact G1.2 source/test commit; awaits Tester/Reviewer audit
LAST_AUDITED_CODE_HEAD = 0d9a3c41e71d368aa4c21aefdd970dc41343e6af; PR #130 source correction merged/reviewed; G1 candidate commits are not independently audited
AUDIT_TARGET_DOC_HEAD = a3c5d63342bec5d564ee930151c2aa7d53f54b0f; latest committed G1 governance candidate before this blocker sync; this sync itself is not yet audited
LAST_AUDITED_DOC_HEAD = e637e111174ada3e12a032227afb211a46eebd44; prior Workbench document audit only; not a G1 review
ACTIVE_PARENT_WP = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01 rev2-corr1
ACTIVE_MICRO_WP = G1-C01-FULL-SUITE-SETUP-DIAGNOSIS; SAME PARENT/ROLE/LEASE
G1_COMMITS = 795c554246c13b838e4cb9a6d434159ab09efbfe feat(release): archive app-only candidate artifacts; a7af42241619d68d9e01043aced00631ad24fc20 docs(governance): define G1.2 artifact lifecycle; a3c5d63342bec5d564ee930151c2aa7d53f54b0f docs(handoff): return G1 candidate to Planner
BRANCH_STATE = LOCAL CANDIDATE; TRACKED/INDEX CLEAN BEFORE THIS SYNC; UNKNOWN UNTRACKED NAMES PRESERVED
REMOTE_CHECKPOINT = NONE; NO PUSH
PR_STATE = NO PR FOR THIS WP
MERGE_STATE = NOT MERGED; NOT AUTHORIZED
VERIFICATION_STATE = TESTER COLLECTION 1,781 / ZERO ERRORS; ONE AUTHORIZED FULL SEQUENTIAL RUN EXIT 1 WITH 1,780 SETUP ERRORS, 1 SKIP, 2 WARNINGS IN 52.63s; OUTPUT LOST SHARED TRACEBACK; CAUSE UNKNOWN; NO RERUN
WHOLE_WP_STATE = HOLD; SETUP FAILURE ROOT CAUSE UNKNOWN; G1-C01 ONE-NODE DIAGNOSTIC AUTHORIZED; REPLACEMENT FULL SUITE NOT AUTHORIZED
HOSTED_CI_STATE = NONE FOR G1 CANDIDATE
DOC_SYNC_STATE = PASS_FOR_G1-C01_DIAGNOSTIC_ENTRY; WORK ORDER, DELTA AND CURRENT RECORD TESTER RESULT AND PLANNER ASSIGNMENT; ROOT CAUSE NOT YET CLAIMED
PATH_REGISTRY_STATE = revision 1.0.23; 65 unique PATH_IDs; 21 unique WP bindings; prior B09 UPDATE_VOLUME bindings unchanged and excluded
G1_SOURCE_STATUS = G1.1 journaled app-only update/recovery candidate committed; G1.2 repository artifact publisher, clean-dev root guard, internal source metadata 0.10.1 and governance candidate committed
LIVE_OPERATIONAL_STATUS = ZERO LIVE MUTATION; installed 0.10.0 runtime not rebuilt or updated; no EXE launch, migration, restore, shortcut or database action
PUBLISHER_STATUS = EXACT REPO-LOCAL `release_staging/published`; exact repository candidate root; clean main/source identity; immutable collision-rejected artifact; path/reparse checks; no Current/Previous/sibling install or Data clone
ROOT_LIFECYCLE = SOLE OPERATIONAL ROOT D:\QI-Crawler; `.update/<update_id>` finite transient; success requires cleanup disposition/next action, deletion separately authorized; failure/RECOVERY_REQUIRED retained; journals and LKG durable
FUTURE_G3 = ROOT-LOCAL ARCHIVE/RECEIPT PATHS RESERVED; SYNTHETIC/LOCATOR CONTRACT ONLY; NO REAL ARCHIVE OR CLEANUP
TEST_RUN_INVALID = 159 collected; 147 passed / 3 skipped / 9 failed; INVALID_FOR_ACCEPTANCE due long basetemp Windows path failures; retained under `.tmp/WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01/20260929T1Z/affected`
TEST_RUN_VALID_SHORT = 159 collected; 155 passed / 3 skipped / 1 failed; only remaining failure was the legacy 0.10.0 test using the default 0.10.1 validator; see exact-node correction
TEST_RUN_EXACT_NODE = `test_live_promotion_success_is_coherent_and_preserves_source`; expected LIVE_VERSION explicitly; 1 passed, 1 non-failing `.pytest_cache` WinError 5 warning; 3.03s
SCRATCH_TOKEN = `w3` maps `.tmp/w3/<six-hex-run-id>/t` to this Parent; `d29f6c` affected and `e36fc2` exact node
SCRATCH_INVENTORY = invalid run 1,721 files / 29,135,568 bytes; valid affected 1,757 / 31,850,472 bytes; exact node 16 / 3,659,972 bytes; all retained, no cleanup
D_FREE_AFTER_VERIFICATION = 18,849,902,592 bytes; greater than 10 GiB reserve
TESTER_FULL_SUITE = `.venv\Scripts\python.exe -m pytest -n 0 --basetemp=.tmp/w3/d9e71b/t`; exit 1; 1,781 collected; 1,780 setup errors / 1 skipped / 2 warnings; 52.63s; common setup traceback lost; root cause UNKNOWN
TESTER_REPORT_ID = NOT_SUPPLIED_IN_PLANNER_PACKET; SOURCE=PLANNER-ADMITTED TESTER SUMMARY
TESTER_RUN_SCRATCH = `.tmp/w3/d9e71b` absent after run; 0 files / 0 bytes; D: free 18,849,390,592 bytes; no cleanup reported
TESTER_REMOTE_STATUS = live origin/main unverified because git ls-remote could not connect; local origin/main remains expected base
PYTEST_WARNING = PytestCacheWarning WinError 5 writing repository `.pytest_cache`; non-failing and retained as environment limitation
FULL_SEQUENTIAL_PYTEST = TESTER RUN CONSUMED; EXIT 1; 1,780 SETUP ERRORS / 1 SKIP / 2 WARNINGS / 52.63s; REPLACEMENT RUN NOT AUTHORIZED
RUFF = CHANGED PYTHON FILES PASS; REPO-WIDE RUFF NOT RUN; first invocation incorrectly included PowerShell and was corrected to Python-only paths
CODEBASE_MEMORY_READINESS = HOLD_WITH_DIAGNOSIS; Builder list_projects returned zero projects; Builder index calls=0; Planner accidentally issued three index_repository calls, all aborted_previous_preserved; zero projects/artifacts; no retry
PARENT_STARTUP_LIMITATIONS = ORIGINAL_DIRECT_STARTUP_FAILURE UNRESOLVED ON INSTALLED OLD BINARY; PR130 SOURCE FIX MERGED; NEW RUNTIME BINARY REQUIRED BUT NOT BUILT/DEPLOYED; SHORTCUT EDIT INELIGIBLE
PARENT_WORKBENCH_LIMITATIONS = LOCAL FULL PYTEST RED; SCRATCH CAP FAILED TWICE; REPO-WIDE RUFF LIMITATION; CBM HOLD; NO WHOLE-PARENT PASS
FAILURE_MEMORY = FM-049 SOURCE FIX IS MERGED; INSTALLED RUNTIME STILL PREDATES IT; NO NEW G1.2 KFM TRIGGER
FEEDBACK = EXISTING HUMAN A0 FB-0058 REMAINS AUTHORITATIVE; NO NEW HUMAN DECISION ORIGINATED
SCOPE_BOUNDARIES = G1 ALLOWLIST ONLY; NO FULL SUITE BY BUILDER; NO G2/G3/BUILD/RELEASE/PUBLISH/OPERATIONAL UPDATE/LAUNCH/SHORTCUT/MIGRATION/RESTORE/CRAWL/IMPORT/B09/REAL ARCHIVE/CLEANUP/ACL/MERGE
HISTORICAL_G1_0_PLUGIN_CODEGRAPH = USED_WITH_FALLBACK; structural impact only; no live path/process/DB/mutation proof
HISTORICAL_G1_PLUGIN_CODEBASE_MEMORY = USED_WITH_FALLBACK for Builder read-only readiness; zero projects; no Builder index; Planner's three aborted calls are a procedural deviation only, not operational readiness
HISTORICAL_G1_2_PLUGIN_TEST_DRIVEN_DEVELOPMENT = USED_AND_SUCCEEDED; publisher/clean-dev/version/locator contracts; no gate reduction
HISTORICAL_G1_2_PLUGIN_SYSTEMATIC_DEBUGGING = USED_AND_SUCCEEDED; exact archive path/enumeration/stat/open diagnosis on synthetic root
HISTORICAL_G1_2_PLUGIN_VERIFICATION_BEFORE_COMPLETION = USED_AND_SUCCEEDED; collection, scoped Ruff, registry/diff/scope/status checks
PLUGIN_CODEGRAPH = USED_WITH_FALLBACK; queried pytest fixtures/setup through CodeGraph; result did not isolate the common setup path; bounded direct source/test fallback will follow
PLUGIN_SYSTEMATIC_DEBUGGING = USED_AND_SUCCEEDED; required skill read before diagnosis; root cause remains pending one diagnostic
PLUGIN_CODEBASE_MEMORY = NOT_APPLICABLE; indexing is unauthorized; no index call made in G1-C01
PLUGIN_TEST_DRIVEN_DEVELOPMENT = NOT_APPLICABLE_PENDING_ROOT_CAUSE; no behavior edit authorized unless cause and exact allowlist are established
PLUGIN_VERIFICATION_BEFORE_COMPLETION = REQUIRED_BEFORE_RETURN; final evidence/checks not yet completed
PROVEN_COMPLETE = G1.0 REUSE/CONTRACT DECISIONS; G1.1 LOCAL UPDATE/RECOVERY CANDIDATE; G1.2 PUBLISHER/CLEAN-DEV/METADATA/GOVERNANCE CANDIDATE; TARGETED EVIDENCE; FINAL COLLECTION; SCOPED PYTHON RUFF
OPEN_BLOCKERS = COMMON SETUP TRACEBACK LOST; ROOT CAUSE UNKNOWN; ONE SINGLE-NODE DIAGNOSTIC AUTHORIZED; REMOTE origin/main UNVERIFIED; NO REPLACEMENT FULL SUITE AUTHORITY
SPINE_IMPACT = MULTIPLE
SPINE_TARGET_FILES = docs/superpowers/plans/WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01.md; docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent_handoff/CURRENT.md
SPINE_SYNC_STATE = PASS
HANDOFF_READY = YES_FOR_BOUNDED_BUILDER_DIAGNOSTIC
STOP_STATE = ACTIVE_G1-C01; NO REMOTE/OPERATIONAL EFFECTS
EXACTLY_ONE_NEXT_ACTION = BUILDER RUNS AT MOST ONE SIMPLE COLLECTED TEST NODE WITH -X -VV --TB=LONG UNDER A FRESH COMPACT REGISTERED SCRATCH ROOT; TRACE THE SETUP FAILURE BEFORE ANY FIX
NEXT_AUTHORITY = BUILDER_SINGLE_WRITER
REMOTE_EFFECTS = NONE
~~~
