# QI-Crawler Agent Handoff

## G1-C03 — Governance sync for the changelog dual-contract correction

The Human A0-authorized post-C02 full sequential Tester run at exact HEAD a1096bb2f80bc89adb52883765df498acceb1309 returned native process exit 1: 1,781 collected; 1,775 passed; 5 governed skips; 1 failed; 2 warnings; 1,112.01s. The failing release-governance node requires exact heading ## Unreleased, which the C02 heading replacement had removed while preserving the internal/unreleased 0.10.1 section. The CLI node independently requires the 0.10.1 changelog and Vietnamese guide headings. This G1-C03 correction restores ## Unreleased above the existing 0.10.1 section in CHANGELOG only. The full-run RED and .tmp/w3/78fe92/t evidence remain retained; the full-run authority is consumed. No runtime/release defect, second full run, Ruff, source/test edit or cleanup is authorized. C02 detailed history remains in the G1_C02 fields below.

~~~text
HANDOFF_ID = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-G1-C03-GOVERNANCE-SYNC-20260929
WORK_ORDER_ID = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01 rev2-corr1
ROLE = BUILDER_SINGLE_WRITER
HANDOFF_TO = BUILDER_SINGLE_WRITER CONTINUATION UNDER PLANNER-OPENED G1-C03; GOVERNANCE EVIDENCE SYNC BEFORE TARGETED CHECK
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
HANDOFF_CAPTURE_BASE = a1096bb2f80bc89adb52883765df498acceb1309; VERIFIED PRE-SYNC HEAD FOR THIS G1-C03 GOVERNANCE SYNC
LOCAL_PRE_SYNC_HEAD = a1096bb2f80bc89adb52883765df498acceb1309; PRE-SYNC ONLY; DO NOT PREDICT THIS COMMIT
LIVE_GIT_HEAD = a1096bb2f80bc89adb52883765df498acceb1309; VERIFIED LOCAL PRE-SYNC HEAD; RE-RESOLVE AT READ-IN
AUDIT_TARGET_CODE_HEAD = 795c554246c13b838e4cb9a6d434159ab09efbfe; exact G1.2 source/test commit; awaits Tester/Reviewer audit
LAST_AUDITED_CODE_HEAD = 0d9a3c41e71d368aa4c21aefdd970dc41343e6af; PR #130 source correction merged/reviewed; G1 candidate commits are not independently audited
AUDIT_TARGET_DOC_HEAD = a1096bb2f80bc89adb52883765df498acceb1309; exact full-run candidate/doc head; G1-C03 governance sync and heading correction await review
PRIOR_G1_C01_DOC_SYNC_HEAD = fce7deaf09ec105172b517b30d5720a051da0577; prior diagnostic-result sync; superseded only by this forward root-cause reconciliation
PRIOR_ROOT_CAUSE_RECONCILIATION_HEAD = 90c7a7694e7a7f3766d69134b8c77777f052ed6d; preserved pre-authority-sync document head
LAST_AUDITED_DOC_HEAD = e637e111174ada3e12a032227afb211a46eebd44; prior Workbench document audit only; not a G1 review
ACTIVE_PARENT_WP = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01 rev2-corr1
ACTIVE_MICRO_WP = G1-C03-CHANGELOG-DUAL-CONTRACT; FULL RUN RED ADMITTED; GOVERNANCE SYNC BEFORE ONE AUTHORIZED TWO-NODE TARGETED CHECK
G1_COMMITS = 795c554246c13b838e4cb9a6d434159ab09efbfe feat(release): archive app-only candidate artifacts; a7af42241619d68d9e01043aced00631ad24fc20 docs(governance): define G1.2 artifact lifecycle; a3c5d63342bec5d564ee930151c2aa7d53f54b0f docs(handoff): return G1 candidate to Planner
BRANCH_STATE = LOCAL CANDIDATE; TRACKED/INDEX CLEAN BEFORE THIS SYNC; UNKNOWN UNTRACKED NAMES PRESERVED
REMOTE_CHECKPOINT = NONE; NO PUSH
PR_STATE = NO PR FOR THIS WP
MERGE_STATE = NOT MERGED; NOT AUTHORIZED
VERIFICATION_STATE = G1-C03 TESTER FULL RUN AT a1096bb2: 1,781 COLLECTED; 1,775 PASSED / 5 GOVERNED SKIPS / 1 FAILED / 2 WARNINGS; 1,112.01s; NATIVE EXIT 1; test_changelog_has_target_release_section RED; .tmp/w3/78fe92/t RETAINED
WHOLE_WP_STATE = HOLD; C01/C02 FULL-RUN RED HISTORY PRESERVED; C03 FULL RUN RED; TARGETED DOC CHECK CANNOT PROMOTE WHOLE SUITE
HOSTED_CI_STATE = NONE FOR G1 CANDIDATE
DOC_SYNC_STATE = G1-C03 AUTHORITY/TESTER RED ROUTED TO WORK ORDER, DELTA, CURRENT, FEEDBACK FB-0060 AND FM-055; TARGETED TWO-NODE CHECK PENDING
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
D_FREE_AFTER_VERIFICATION = 18,849,902,592 bytes; greater than 10 GiB reserve at the prior C01 verification
HISTORICAL_C01_TESTER_FULL_SUITE = `.venv\Scripts\python.exe -m pytest -n 0 --basetemp=.tmp/w3/d9e71b/t`; reported exit 1; 1,781 collected; 1,780 setup errors / 1 skipped / 2 warnings; 52.63s; traceback lost; preserve as consumed RED history
TESTER_FULL_SUITE = C03 exact candidate a1096bb2; 1,781 collected; 1,775 passed / 5 governed skips / 1 failed / 2 warnings; 1,112.01s; native process exit 1; one launch/no retry; retained under .tmp/w3/78fe92/t
G1_C02_TESTER_REPORT_ID = NOT_SUPPLIED_IN_PLANNER_PACKET; SOURCE=PLANNER-ADMITTED TESTER RESULT
G1_C02_FAILED_NODE = `tests/test_cli_help.py::test_release_version_is_synchronized_across_user_documents`; line 163 expects `## 0.10.1`; next assertion requires `Co gi moi trong 0.10.1`
G1_C02_CLASSIFICATION = PLANNER WP_CODE_DEFECT; DOCUMENT-HEADING SYNCHRONIZATION; NO RUNTIME/RELEASE DEFECT; NO GITHUB ACTIONS FAILURE CLAIM
G1_C02_NATIVE_EXIT = NOT_INDEPENDENTLY_PROVEN; TESTER POWERSHELL WRAPPER REUSED RESERVED `$PID`; PREVENT WITH `$pytestProcessId` AND IMMEDIATE PROCESS OBJECT `.ExitCode` CAPTURE
G1_C02_SCRATCH = `.tmp/w3/f2a913`; 15,791 FILES / 621,117,062 BYTES; RETAINED; NO CLEANUP
G1_C02_AUTHORIZED_EDIT = CHANGELOG.md AND HUONG_DAN_SU_DUNG.md HEADINGS ONLY; BOTH MUST EXPLICITLY REMAIN INTERNAL/UNRELEASED
G1_C02_RELEASE_IMPACT = INTERNAL VERSION REMAINS 0.10.1; NO VERSION INCREMENT, BUILD, TAG, RELEASE, INSTALLATION OR CAPABILITY CHANGE
G1_C02_DOC_COMMIT = 38ab35d0362379ae64b19bba3f06ee0c9fabf732; EXACTLY CHANGELOG.md AND HUONG_DAN_SU_DUNG.md
G1_C02_TARGETED_COMMAND = `.venv\Scripts\python.exe -m pytest -n 0 --basetemp=.tmp/w3/c02f29/t tests/test_cli_help.py::test_release_version_is_synchronized_across_user_documents`
G1_C02_TARGETED_HEAD = 8d6eeac0bcacc8a443c9bc27548fb8b197be7a47; ONLY THE TWO DOC HEADING EDITS WERE IN THE WORKTREE; NOW COMMITTED ABOVE
G1_C02_TARGETED_RESULT = NATIVE PROCESS OBJECT EXIT 0; 1 PASSED; ONE NON-FAILING PytestCacheWarning WinError 5; pytest 2.47s; wall 4.43s
G1_C02_TARGETED_TIME = START 2026-09-29T06:11:25.6348784+07:00; END 2026-09-29T06:11:30.0641843+07:00; PID VALUE CAPTURED AS `$pytestProcessId`, NEVER `$PID`
G1_C02_TARGETED_EVIDENCE = stdout/stderr/metadata/parent-writable proof under `.tmp/w3/c02f29`; five files / 915,100 bytes; child `t` pytest-owned; retained; no cleanup
G1_C02_D_FREE_AFTER_TARGETED = 18,171,588,608 bytes; greater than 10 GiB reserve
G1_C03_TESTER_REPORT_ID = PLANNER-ADMITTED TESTER REPORT; ID NOT SUPPLIED
G1_C03_HUMAN_AUTHORITY = EXACT POST-C02 FULL RUN AUTHORIZED BY HUMAN A0; ROUTED AS FB-0060; AUTHORITY CONSUMED; NO SECOND FULL RUN
G1_C03_FAILED_NODE = tests/test_release_governance.py::test_changelog_has_target_release_section; requires exact ## Unreleased; C02 removed it while retaining the 0.10.1 internal/unreleased heading
G1_C03_CONTRACT_PAIR = CLI TEST REQUIRES ## 0.10.1 AND GUIDE Co gi moi trong 0.10.1; RELEASE GOVERNANCE TEST REQUIRES ## Unreleased; BOTH CHANGELOG HEADINGS MUST COEXIST
G1_C03_ROOT_CAUSE = DOCUMENTATION CONTRACT WAS ONLY PARTIALLY RESTORED BY C02; NO RUNTIME/RELEASE DEFECT; NO GITHUB ACTIONS CLAIM
G1_C03_AUTHORIZED_EDIT = CHANGELOG.md ONLY; RESTORE ## Unreleased ABOVE EXISTING ## 0.10.1 - Internal, unreleased; preserve all content/history
G1_C03_TARGETED_NODES = tests/test_cli_help.py::test_release_version_is_synchronized_across_user_documents; tests/test_release_governance.py::test_changelog_has_target_release_section
G1_C03_TARGETED_AUTHORITY = ONE INVOCATION AFTER GOVERNANCE SYNC; FRESH SHORT REGISTERED PARENT, ABSENT PYTEST-OWNED CHILD t, CAPTURE COMPLETE LOGS AND NATIVE EXIT; MAX 5 MIN / 5,000 FILES / 256 MiB / >=10 GiB FREE; NO RETRY
G1_C03_RELEASE_IMPACT = INTERNAL SOURCE METADATA REMAINS 0.10.1 UNRELEASED; NO VERSION INCREMENT, OFFICIAL RELEASE, BUILD, TAG, INSTALL, RUNTIME, CAPABILITY OR MATURITY CHANGE
G1_C03_FAILURE_MEMORY = FM-055; HUMAN AUTHORITY/TESTER RED ROUTED; CHANGELOG HEADING FIX PENDING; BOTH EXACT NODES WILL BE CHECKED TOGETHER
G1_C03_PLUGIN_CODEGRAPH = USED_AND_SUCCEEDED; queried both exact test symbols and CHANGELOG; identified three exact heading contracts; impact radius two tests and CHANGELOG; edit radius CHANGELOG; test radius both nodes
G1_C03_PLUGIN_SYSTEMATIC_DEBUGGING = USED_AND_SUCCEEDED; traced retained full-run failure to the missing exact heading after C02 while preserving the independent CLI heading requirements; edit radius CHANGELOG only
G1_C03_PLUGIN_TDD = USED_AND_SUCCEEDED; retained full-run failure is RED evidence; no RED rerun; combined two-node GREEN remains pending
HISTORICAL_C01_TESTER_REPORT_ID = NOT_SUPPLIED_IN_PLANNER_PACKET; SOURCE=PLANNER-ADMITTED TESTER SUMMARY
HISTORICAL_C01_TESTER_RUN_SCRATCH = `.tmp/w3/d9e71b` absent after run; 0 files / 0 bytes; D: free 18,849,390,592 bytes; no cleanup reported
TESTER_REMOTE_STATUS = live origin/main unverified because git ls-remote could not connect; local origin/main remains expected base
PYTEST_WARNING = PytestCacheWarning WinError 5 writing repository `.pytest_cache`; non-failing and retained as environment limitation
FULL_SEQUENTIAL_PYTEST = C03 exact candidate a1096bb2; 1,781 collected; 1,775 passed / 5 governed skips / 1 failed / 2 warnings; 1,112.01s; native exit 1; authority consumed; no further full run
RUFF = CHANGED PYTHON FILES PASS; REPO-WIDE RUFF NOT RUN; first invocation incorrectly included PowerShell and was corrected to Python-only paths
CODEBASE_MEMORY_READINESS = HOLD_WITH_DIAGNOSIS; Builder list_projects returned zero projects; Builder index calls=0; Planner accidentally issued three index_repository calls, all aborted_previous_preserved; zero projects/artifacts; no retry
PARENT_STARTUP_LIMITATIONS = ORIGINAL_DIRECT_STARTUP_FAILURE UNRESOLVED ON INSTALLED OLD BINARY; PR130 SOURCE FIX MERGED; NEW RUNTIME BINARY REQUIRED BUT NOT BUILT/DEPLOYED; SHORTCUT EDIT INELIGIBLE
PARENT_WORKBENCH_LIMITATIONS = LOCAL FULL PYTEST RED; SCRATCH CAP FAILED TWICE; REPO-WIDE RUFF LIMITATION; CBM HOLD; NO WHOLE-PARENT PASS
FAILURE_MEMORY = FM-049 SOURCE FIX IS MERGED; FM-055 RECORDS C03 SHARED CHANGELOG CONTRACT FAILURE; NO RUNTIME/RELEASE DEFECT
FEEDBACK = FB-0058 PARENT LEASE; FB-0059 C01 REPLACEMENT AUTHORITY; FB-0060 EXACT C03 POST-C02 FULL-RUN AUTHORITY; BUILDER RECORDS, DOES NOT ORIGINATE, THE DECISION
SCOPE_BOUNDARIES = G1 ALLOWLIST ONLY; NO FULL SUITE BY BUILDER; NO G2/G3/BUILD/RELEASE/PUBLISH/OPERATIONAL UPDATE/LAUNCH/SHORTCUT/MIGRATION/RESTORE/CRAWL/IMPORT/B09/REAL ARCHIVE/CLEANUP/ACL/MERGE
HISTORICAL_G1_0_PLUGIN_CODEGRAPH = USED_WITH_FALLBACK; structural impact only; no live path/process/DB/mutation proof
HISTORICAL_G1_PLUGIN_CODEBASE_MEMORY = USED_WITH_FALLBACK for Builder read-only readiness; zero projects; no Builder index; Planner's three aborted calls are a procedural deviation only, not operational readiness
HISTORICAL_G1_2_PLUGIN_TEST_DRIVEN_DEVELOPMENT = USED_AND_SUCCEEDED; publisher/clean-dev/version/locator contracts; no gate reduction
HISTORICAL_G1_2_PLUGIN_SYSTEMATIC_DEBUGGING = USED_AND_SUCCEEDED; exact archive path/enumeration/stat/open diagnosis on synthetic root
HISTORICAL_G1_2_PLUGIN_VERIFICATION_BEFORE_COMPLETION = USED_AND_SUCCEEDED; collection, scoped Ruff, registry/diff/scope/status checks
PLUGIN_CODEGRAPH = USED_WITH_FALLBACK; queries did not isolate common setup path; bounded direct read of tests/conftest.py, test_parser.py and pytest configuration completed
PLUGIN_SYSTEMATIC_DEBUGGING = USED_WITH_FALLBACK; Builder read skill and boundedly traced fixtures; one node did not reproduce; later exact pytest-runtime/fixture reconciliation is Planner-admitted evidence, not a Builder plugin execution claim
PLUGIN_CODEBASE_MEMORY = NOT_APPLICABLE; indexing is unauthorized; no index call made in G1-C01
PLUGIN_TEST_DRIVEN_DEVELOPMENT = NOT_APPLICABLE; no behavior edit made; accepted root cause is the local verification command contract
PLUGIN_VERIFICATION_BEFORE_COMPLETION = USED_AND_SUCCEEDED; verified exact command/log/inventory, one-node budget, scope, current keys and final Git state
PROVEN_COMPLETE = G1.0 REUSE/CONTRACT DECISIONS; G1.1 LOCAL UPDATE/RECOVERY CANDIDATE; G1.2 PUBLISHER/CLEAN-DEV/METADATA/GOVERNANCE CANDIDATE; TESTER FULL RUN EVIDENCE; ONE NON-REPRODUCING DIAGNOSTIC; PLANNER ROOT-CAUSE/COMMAND-CONTRACT RECONCILIATION
DIAGNOSTIC_NODE = tests/test_parser.py::test_parse_money_vnd; 1 PASSED; 1 NON-FAILING PytestCacheWarning; 1.31s; EXIT 0
DIAGNOSTIC_COMMAND = `.venv\Scripts\python.exe -m pytest -n 0 -x -vv --tb=long --basetemp=.tmp/w3/fce7de/t tests/test_parser.py::test_parse_money_vnd`
DIAGNOSTIC_LOG = `.tmp/w3/fce7de/diagnostic.log`; 1,190 BYTES; SHA256 374738A04811028D068CB02710CB14DBA6FAAE158822F4D5317779F8A21D9A49
DIAGNOSTIC_SCRATCH = 2 FILES / 914,598 BYTES; TEMPLATE DB + LOG; RETAINED; D: FREE 18,848,382,976 BYTES; NO CLEANUP
DIAGNOSTIC_BUDGET = 1/1 CONSUMED; NO RETRY OR SECOND NODE AUTHORIZED
SCOPE_EXPANSION_REQUIRED = NO PRODUCT/CODE SCOPE EXPANSION IDENTIFIED; ROOT CAUSE IS RUNNER COMMAND CONTRACT; NO SOURCE/TEST CHANGE
ROOT_CAUSE = Fresh parent `.tmp/w3/d9e71b` was absent while pytest received child `t`; pytest 8.4.2 creates only the explicit basetemp; this verified local command defect is sufficient for widespread setup failure, but lost tracebacks do not prove sole cause of all 1,780
PREVENTION = Create/verify bounded registered `<run-root>` first; retain log outside absent child `t`; verify freshness/containment/budgets; pass child `t`; never precreate it
ROOT_CAUSE_CLASSIFICATION = LOCAL VERIFICATION COMMAND-CONTRACT DEFECT; CI_INFRASTRUCTURE_DEFECT IS A LOCAL UMBRELLA ONLY; NO GITHUB ACTIONS FAILURE CLAIM; NO G1 PRODUCT DEFECT ESTABLISHED
HUMAN_AUTHORITY = EXACTLY ONE REPLACEMENT FULL SEQUENTIAL PYTEST (`-n 0`); NO CODE/TEST CHANGE; SOURCE FB-0059
TESTER_EXACT_HEAD = RESOLVE AND RECORD THE ACTUAL LOCAL GIT HEAD AT TESTER PREFLIGHT AFTER PLANNER REVIEW; DO NOT ASSUME THIS PRE-SYNC HEAD IS THE TEST TARGET
REPLACEMENT_RUN_PARENT = FRESH ABSENT REGISTERED `.tmp/w3/<new-six-hex>/`; VERIFY CONTAINMENT/REPARSE/FRESHNESS/OWNERSHIP; CREATE PARENT AND RETAIN WRITABILITY PROOF; CHILD `t` MUST REMAIN ABSENT FOR PYTEST
REPLACEMENT_RUN_EVIDENCE = COMPLETE STDOUT/STDERR/TRACEBACK/TRUE PYTEST EXIT/START/END/SUMMARY/EXACT COMMAND/WORKING DIRECTORY OUTSIDE `t`; PIPELINE MUST PRESERVE PYTEST EXIT
REPLACEMENT_RUN_BUDGET = 30 MINUTES; 20,000 FILES; 1 GiB; >=10 GiB D: FREE; ONE RUN; NO RETRY; NO CLEANUP
POST_PYTEST_GATES = ONLY IF FULL PYTEST PASSES, ONE FULL `python -m ruff check .` AND PRESCRIBED READ-ONLY STATIC GATES; ANY REQUIRED FAILURE RETURNS TO PLANNER; NO TESTER FIX/SCOPE EXPANSION
OPEN_BLOCKERS = WHOLE-SEQUENTIAL GATE RED AFTER C03 DOCUMENT CONTRACT FAILURE; ONE AUTHORIZED TWO-NODE TARGETED GREEN PENDING; FULL-RUN AUTHORITY CONSUMED; NO RUFF/RETRY; LIVE origin/main UNVERIFIED
SPINE_IMPACT = MULTIPLE
SPINE_TARGET_FILES = docs/superpowers/plans/WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01.md; docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent_handoff/CURRENT.md; docs/agent/KNOWN_FAILURE_MODES.md; docs/agent/FEEDBACK_LEDGER.md
SPINE_SYNC_STATE = PASS
HANDOFF_READY = NO; G1-C03 GOVERNANCE SYNC IN PROGRESS; TARGETED CHECK HAS NOT RUN
STOP_STATE = GOVERNANCE SYNC FOR C03 TESTER RED AND EXACT HUMAN AUTHORITY; NO C03 HEADING EDIT/TEST YET; NO REMOTE/OPERATIONAL EFFECTS
EXACTLY_ONE_NEXT_ACTION = BUILDER COMMITS THIS GOVERNANCE SYNC, RESTORES THE MISSING UNRELEASED HEADING ABOVE THE EXISTING 0.10.1 SECTION, THEN RUNS ONE TARGETED INVOCATION WITH BOTH EXACT HEADING TESTS
NEXT_AUTHORITY = BUILDER_SINGLE_WRITER
REMOTE_EFFECTS = NONE
~~~
