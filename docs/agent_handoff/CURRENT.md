# QI-Crawler Agent Handoff

## Active handoff — Agent Loop Correction 05 entry transition

Human A0 approved the bounded Correction 05 lease. This two-file transition
rebinds the active handoff and records the new decision; Stage 1/2 remain
blocked until the post-commit Role Entry Gate passes. Correction 04's red
verification and independent Reviewer HOLD remain historical evidence. B09
stays parked at Bridge A HOLD.

~~~text
HANDOFF_ID = WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01-CORRECTION-05-ENTRY
ROLE = BUILDER_SINGLE_WRITER
ROLE_SOURCE_EVIDENCE = HUMAN_A0_CORRECTION_05_LEASE; WORK_ORDER_07F2BDAF; CURRENT
CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
ACTIVE_PARENT_WP = GOVERNANCE_AGENT_LOOP_CONSOLIDATION
ACTIVE_MICRO_WP = CORRECTION_05_ENTRY_RECONCILIATION
ACTIVE_BRANCH = codex/agent-loop-consolidation-01
BASE_SHA = e9b6f62c30ee46054c0d617b639831baa8e9fba5
HANDOFF_CAPTURE_BASE = 07f2bdaf81561cc21db4de6b6e3dec8758858f2e
LIVE_GIT_HEAD_AT_CAPTURE = 07f2bdaf81561cc21db4de6b6e3dec8758858f2e
ROADMAP_REVISION = MASTER_ROADMAP_BLOB_8bd4e40dbe8c9e392166d55e3641119dca3f8d3a
ROADMAP_BASELINE_SHA = 179c0712a14161ea25096e66a127f6022bf696fd
WORK_ORDER = docs/superpowers/plans/WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01.md
WORK_ORDER_COMMIT = 07f2bdaf81561cc21db4de6b6e3dec8758858f2e
WORK_ORDER_SHA256 = 97C5DA8203A61D3F2C12505D7037E53ED21E7D5E4318685837A21374FF43EE23
CURRENT_AUTHORITY = BUILDER_SINGLE_WRITER; ENTRY_RECONCILIATION_ONLY
APPROVAL_LEASE = CORRECTION_05; LOCAL_ONLY; EXACT_FOURTEEN_PATH_ALLOWLIST
WRITE_SCOPE_PATHS =
  docs/superpowers/plans/WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01.md
  docs/agent/OPERATING_MODEL.md
  docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md
  docs/agent/LOCAL_STAGED_INTEGRATION.md
  docs/agent/FEEDBACK_LEDGER.md
  docs/agent/PATH_REGISTRY.yaml
  docs/agent_handoff/CURRENT.md
  plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md
  plugins/qi-agent-workbench/skills-lock.json
  tests/agent_workbench/test_skills_lock.py
  AGENTS.md
  docs/agent/MASTER_ROADMAP.md
  docs/agent/HUMAN_COLLABORATION.md
  docs/agent/QI_AGENT_WORKBENCH.md
ROLE_ENTRY_GATE_AFTER_ENTRY = PENDING; RUN_AFTER_TWO_FILE_TRANSITION
HUMAN_A0 = MATERIAL_AUTHORITY_ABOVE_THE_LOOP
OPERATIONAL_ROLES = PLANNER_ARCHITECT; BUILDER_SINGLE_WRITER; TESTER_MACHINE_VERIFIER; REVIEWER_AUDITOR
TESTER_AUTHORITY = EVIDENCE_ONLY
AUDIT_TARGET_CODE_HEAD = c674f77b65cc38987f201229e0efe9e79d98acf5; PRIOR_REVIEW_HOLD_TARGET
REVIEW_REPORT_ID = QI-AGENT-LOOP-C04-REVIEW-C674-01; HOLD; PRESERVED
CORRECTION_04_FINAL_HOLD = e9b6f62c30ee46054c0d617b639831baa8e9fba5; FULL_SUITE_FAIL; RUFF_UNTRACKED_KEEP; TEMP_FILE_DIR_CEILING_EXCEEDED
CORRECTION_05_CONTENT_COMMITS = ONE; EXACT_FOURTEEN_PATHS
CORRECTION_05_TERMINAL_CURRENT_SYNC = ONE_IF_REQUIRED; CURRENT_ONLY
TARGETED_RUNS = ONE; .tmp/al05/t/p
FULL_RUNS = ONE_ONLY_IF_TARGETED_PASS; .tmp/al05/f/p
RUFF_RUNS = ONE_TRACKED_PYTHON_ONLY
RETRY = NONE
CORRECTION_05_FULL_RUN_MAX_FILES = 20000
CORRECTION_05_FULL_RUN_MAX_DIRS = 15000
CORRECTION_05_FULL_RUN_MAX_BYTES = 1073741824
CORRECTION_05_CUMULATIVE_RETAINED_MAX_FILES = 32000
CORRECTION_05_CUMULATIVE_RETAINED_MAX_DIRS = 26000
CORRECTION_05_CUMULATIVE_RETAINED_MAX_BYTES = 2147483648
MIN_D_FREE_BYTES = 10737418240
CORRECTION_05_TEMP_ALIAS = .tmp/al05; REGISTER_IN_PATH_REGISTRY_BEFORE_CREATE; NOT_CREATED
B09_PRESERVATION_COMMIT = 9bc64942f35c41d002ef80a74c7a02851422b0e8
B09_STATE = PARKED_PRESERVED_LOCAL; BRIDGE_A_HOLD; NOT_PUSHED
B09_EXECUTION_IN_THIS_WP = NO
HOSTED_CI_STATE = NOT_REQUESTED; NO_PR
REMOTE_CHECKPOINT = NOT_PUSHED; PUSH_NOT_AUTHORIZED
PR_STATE = NOT_CREATED; NOT_AUTHORIZED
MERGE_STATE = NOT_AUTHORIZED
RELEASE = NOT_AUTHORIZED
UNTRACKED_KEEP = $RECYCLE.BIN/; .codex/; WP_GOV_BLUEPRINT_KVS_HANDOFF_01_AUDIT.patch; WP_GOV_BLUEPRINT_KVS_HANDOFF_01_CORRECTION.patch; case-repro.ini; case-repro2.ini; output/; prep_data/; tmp/; uv.lock
UNTRACKED_DISPOSITION = KEEP; NOT_CLEANED; NO_UNTRACKED_STAGING
SPINE_IMPACT = GOVERNANCE; CURRENT; FEEDBACK
SPINE_TARGET_FILES = docs/agent_handoff/CURRENT.md; docs/agent/FEEDBACK_LEDGER.md; docs/agent/OPERATING_MODEL.md; docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md; docs/agent/PATH_REGISTRY.yaml; plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md
SPINE_SYNC_STATE = HOLD_UNTIL_CORRECTION_05_REVIEW_AND_RECONCILIATION
PROJECT_MEMORY_PROMOTION = NOT_BEFORE_MERGE
OPEN_BLOCKERS = POST_TRANSITION_ROLE_ENTRY_GATE; CORRECTION_05_EXECUTION_NOT_STARTED
BUILDER_EXECUTION = ENTRY_RECONCILIATION_ONLY
HANDOFF_READY = NO; POST_TRANSITION_ROLE_ENTRY_GATE_REQUIRED
SCOPE_BOUNDARIES = NO_B09; NO_PRODUCT_RUNTIME; NO_WORKFLOW_CI; NO_OTHER_UNTRACKED_STAGING; NO_CLEANUP; NO_PUSH; NO_PR; NO_MERGE; NO_RELEASE
EXACTLY_ONE_NEXT_ACTION = RERUN_ROLE_ENTRY_GATE_AFTER_TWO_FILE_ENTRY_TRANSITION_COMMIT
NEXT_AUTHORITY = BUILDER_SINGLE_WRITER; ROLE_ENTRY_GATE
~~~

## Historical retention locators

The six pre-Agent-Loop historical bodies below were compared with their retained
source sections; each body matched exactly after newline normalization. The
shared immutable source identity is:

~~~text
SOURCE_GIT_SHA = 179c0712a14161ea25096e66a127f6022bf696fd
SOURCE_PATH = docs/agent_handoff/CURRENT.md
SOURCE_BLOB = 32e8bd9241666f5ed64ce1a59a9d9ef88042bb67
~~~

Each locator preserves the complete original section in Git. The active
snapshot keeps the B09 parked/HOLD state, preservation commit and exact code/test
identities above, so the longer historical narratives can leave the active
handoff without losing evidence or granting B09 execution authority. The prior
Correction 04 full-verification HOLD is retained at the exact terminal commit
below; Correction 05 supersedes only its active handoff state.

| Compacted CURRENT section | Retained source anchor | Information preserved | Why safe to compact from active CURRENT |
| --- | --- | --- | --- |
| Agent Loop Correction 04 full-verification HOLD (superseded active state) | e9b6f62c30ee46054c0d617b639831baa8e9fba5:docs/agent_handoff/CURRENT.md | Targeted retry, full-suite red result, Ruff findings, scratch accounting, open blockers and next authority | Correction 05 is now the active handoff; the exact prior report is retrievable from the immutable terminal commit, and B09 remains parked. |
| Historical v0.10 B09 post-promotion runtime contract correction (displaced at Agent Loop Stage 0) | 179c0712a14161ea25096e66a127f6022bf696fd:docs/agent_handoff/CURRENT.md#v010-b09-post-promotion-runtime-contract-correction-active-local-handoff | Runtime-contract finding, live-installation hold, verification and artifact ownership | B09 remains parked; active B09 disposition and exact source/test preservation are retained above; original full body is retrievable from the immutable source object. |
| Historical v0.10 B09 process-census compatibility correction | 179c0712a14161ea25096e66a127f6022bf696fd:docs/agent_handoff/CURRENT.md#historical-v010-b09-process-census-compatibility-correction | Process-census compatibility evidence and its disposition | B09 remains parked; active B09 disposition and exact source/test preservation are retained above; original full body is retrievable from the immutable source object. |
| Historical v0.10 B09 post-merge source identity correction | 179c0712a14161ea25096e66a127f6022bf696fd:docs/agent_handoff/CURRENT.md#historical-v010-b09-post-merge-source-identity-correction | Post-merge source-identity evidence and its disposition | B09 remains parked; active B09 disposition and exact source/test preservation are retained above; original full body is retrievable from the immutable source object. |
| Historical v0.10 B09 live promotion gate | 179c0712a14161ea25096e66a127f6022bf696fd:docs/agent_handoff/CURRENT.md#historical-v010-b09-live-promotion-gate | Live-promotion gate decision and acceptance evidence | B09 remains parked; active B09 disposition and exact source/test preservation are retained above; original full body is retrievable from the immutable source object. |
| Historical v0.10 B09 operational rebind (retained evidence) | 179c0712a14161ea25096e66a127f6022bf696fd:docs/agent_handoff/CURRENT.md#historical-v010-b09-operational-rebind-retained-evidence | Operational-rebind decision, bounded evidence and unresolved disposition | B09 remains parked; active B09 disposition and exact source/test preservation are retained above; original full body is retrievable from the immutable source object. |
| Historical v0.10 OA06 final governance closeout (retained evidence) | 179c0712a14161ea25096e66a127f6022bf696fd:docs/agent_handoff/CURRENT.md#historical-v010-oa06-final-governance-closeout-retained-evidence | OA06 governance closeout evidence and historical disposition | B09 remains parked; active B09 disposition and exact source/test preservation are retained above; original full body is retrievable from the immutable source object. |
