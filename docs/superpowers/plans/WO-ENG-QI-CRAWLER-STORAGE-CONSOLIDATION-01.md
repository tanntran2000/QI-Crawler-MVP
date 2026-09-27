# WP-ENG-QI-CRAWLER-STORAGE-CONSOLIDATION-01

## Status, authority, and baseline

~~~text
STATUS = LOCAL_EXECUTION_COMPLETE_PASS_WITH_LIMITATIONS; M0_COMPLETE; M1_COMPLETE; M2_TARGETS_01_03_COMPLETE; TARGET04_FB8EDAC_KEEP_PENDING_REVIEW; TESTER_PASS; REVIEWER_PASS; PR135_OPEN; INITIAL_HEAD_6FBCD_REQUIRED_CI_GREEN; TERMINAL_SYNC_HEAD_CI_PENDING; HUMAN_MANUAL_MERGE_PENDING
ROLE = BUILDER_SINGLE_WRITER_FOR_REMOTE_INTEGRATION_ONLY
AUTHORITY = Human A0 exact approval recorded in Planner task 01a0d14b-4e41-7480-9179-d1b230295f77 on 2026-09-27
PLANNER_BUILDER_RESULT_REVIEW = PASS_WITH_ONE_TARGET_RETAINED; PARENT_NOT_CLOSED
TESTER_STATE = PASS_MACHINE_EVIDENCE_FOR_M2_CANDIDATE_ONLY
TESTER_REPORT_ID = STORAGE_M2_TESTER_PASS_20260927_01; SOURCE_TASK=/root/agent_loop_contract_tester
TESTER_OBJECT_ID = M2_a610ea07d434d6677e6f5749dc970a375e81d67c__DOC_2377888c35a86edd478b2e7a1011f32c9ab53eee
PLANNER_TESTER_RECONCILIATION = ACCEPTED; PARENT_NOT_CLOSED
REVIEWER_STATE = PASS; REPORT_ID=STORAGE_M2_REVIEWER_PASS_20260927_01; TARGET_CODE=a610ea07d434d6677e6f5749dc970a375e81d67c; TARGET_DOC=2c0c62c2609018a784e704b3e02b1b1520a503fd
REVIEWER_REPORT_ID = STORAGE_M2_REVIEWER_PASS_20260927_01; SOURCE_TASK_ID=/root/agent_loop_contract_reviewer
REVIEWER_OBJECT_ID = M2_a610ea07d434d6677e6f5749dc970a375e81d67c__LIVE_DOC_2c0c62c2609018a784e704b3e02b1b1520a503fd
REVIEWER_AUDIT_VERDICT = PASS; CI_FITNESS=FIT_FOR_LOCAL_STORAGE_AND_EVIDENCE_CAPABILITY; HOSTED_GATES_LATER_REMOTE_PR_TRANSITION
REVIEWER_LIMITATIONS = UNRELATED_ACCEPTANCE_EXPORT_WORKSPACE_NAMES_ONLY_ACCESS_DENIED; DELETE_01_SUMMARY_POSTCHECK_PASS_EMPTY_MISMATCHES_CRITICAL_HASHES_MATCH_BUT_FULL_ARRAYS_OMITTED; SAFETY_GUARD_MANUAL_ONLY; FREE_SPACE_DELTAS_OBSERVATIONAL
PLANNER_POST_REVIEW_RECONCILIATION = LOCAL_OUTCOME_PASS_WITH_LIMITATIONS; LOCAL_PARENT_TESTER_REVIEWER_COMPLETE; PR135_OPEN; INITIAL_HEAD_REQUIRED_CI_GREEN; TERMINAL_SYNC_HEAD_CI_PENDING
REVIEWER_FINDING_STORAGE_M2_R01 = FINDING_ID=STORAGE-M2-R01; IMPORTANT; NONBLOCKING; NEW_AUTHORITY_REQUIRED; DELETE_01_FULL_PROTECTED_PRE_POST_ARRAYS_NOT_PERSISTED; NO_RETROSPECTIVE_FABRICATION; FUTURE_DESTRUCTIVE_LIFECYCLE_REQUIRES_COMPLETE_PER_TARGET_ARRAYS
REMOTE_INTEGRATION_AUTHORITY = HUMAN_A0_AUTHORIZED_NORMAL_BRANCH_PUSH_AND_ONE_PR_TO_MAIN_AFTER_REVIEW_GATES; ONE_TERMINAL_DOCS_SYNC_COMMIT_AND_NORMAL_PUSH_TO_SAME_PR; MONITOR_EXACT_HEAD_REQUIRED_CI; NO_SECOND_PR; NO_MERGE
LOCAL_M2_OUTCOME = PASS_WITH_LIMITATIONS; TARGETS_01_03_DELETED; TARGET04_FB8EDAC_KEEP_PENDING_REVIEW; LOGICAL_BYTES_REMOVED=5321128566; NO_FURTHER_DELETION_AUTHORITY
CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
M0_BASE = cc9bd53be871059689be4f91f0584efbec04405e
BRANCH = codex/crawler-storage-consolidation-01
ROADMAP_NODE = Cross-cutting — Windows / Team Bid delivery; Engineering Toolbox / Plugins; RD-0014
ROADMAP_IMPACT = SPINE_ONLY; NO_PRODUCT_CAPABILITY_OR_MATURITY_CHANGE
ARCHITECTURE_LAYERS = INFRASTRUCTURE_OPERATIONAL_ARTIFACT_LIFECYCLE; WINDOWS_PACKAGING_RELEASE_LIFECYCLE; PERSISTENCE_OBSERVED_ONLY
RELEASE_IMPACT = NONE_FOR_THIS_CLEANUP_WP
~~~text

Human intent: keep D:\QI-Crawler as the only operational Crawler installation,
reclaim only the four exact obsolete candidate application subtrees below
when every evidence gate passes, and preserve operational data, AppData,
acceptance, rollback, candidate data, evidence, repository files, and unknowns.

PR #134 was read from authenticated GitHub before the branch transition:
MERGED at 2026-09-27T05:57:54Z; head
89596cbf3609e931ecd59ed1f007981e35adf26d; base eb1e2931c0c353f8cd6517f7d94ef80804f76e26;
merge/live origin/main cc9bd53be871059689be4f91f0584efbec04405e. The exact-head
required checks were SUCCESS: Code Quality, Tests Ubuntu 3.12, Tests Windows
3.12, Compatibility Ubuntu 3.11, Required CI Gate, CodeQL Analyze (actions),
CodeQL Analyze (python), and CodeQL.

M0 verified the canonical checkout and origin, fast-forwarded local main to
the verified origin/main, proved the merged local branch tip reachable and
deleted only that local branch, then created this local branch at the exact
live main. M0 made no remote write. After local Tester and Reviewer gates, the
authorized branch push and single PR were completed. PR #135 is open at exact
head `6fbcd24814cf1974b74741b1bbbb4d728d5c19d5`, base main
`cc9bd53be871059689be4f91f0584efbec04405e`; all exact-head checks are SUCCESS:
Code Quality (11:49:37Z), Tests Ubuntu 3.12 (11:53:46Z), Tests Windows 3.12
(11:58:08Z), Compatibility Ubuntu 3.11 (11:57:42Z), Required CI Gate
(11:58:16Z), CodeQL Analyze actions (11:49:46Z), CodeQL Analyze python
(11:50:02Z), and CodeQL aggregate (11:49:38Z), all on 2026-09-27. One
terminal docs-only commit and normal push to this same PR are authorized;
required checks must be monitored on its exact new head. Merge remains
Human-only.

## Objective and boundaries

Perform a read-only inventory of the named Crawler roots, produce a local raw
manifest and a sanitized disposition record, and sequentially delete only
allowlisted candidate app subtrees whose complete gate is proven. This is
artifact lifecycle work. It changes no product capability, persistence
behavior, packaged release, or roadmap maturity.

B09 remains incomplete, Bridge A remains HOLD, and this Work Order grants no
B09, A3, sandbox rearm, RealF5, live application start, release, or operational
database mutation authority.

~~~text
MUST_NOT_CHANGE = repository source/tests/migrations/packaging/scripts/templates; workflow CI; AGENTS.md; Master Roadmap; operational configuration; shortcuts; database; AppData; Acceptance; Rollback; protected candidate content
MUST_NOT_DO = start or stop the application; migrate, mutate, copy, or open an operational DB; change ACLs or take ownership; elevate to improve observation; clean unknown artifacts; use wildcard deletion; perform further deletion; force push; rebase; amend; rewrite history; create more than one PR; merge; release
UNKNOWN_OR_ACCESS_DENIED = KEEP
~~~text

## M0 — entry and terminal reconciliation

M0 has verified the canonical path, git top-level, git-dir/common-dir,
origin, branch, and live main. Authenticated PR #134 is merged at the exact
identity recorded above. The tracked tree was clean before the transition.
Unknown untracked artifact names were retained without content inspection.
Local main was fast-forwarded to cc9bd53; the merged local branch was deleted
only after reachability proof and after switching away; the new branch was
created from that exact origin/main commit.

M0 writes only this Work Order, CURRENT, FEEDBACK_LEDGER, MASTER_ROADMAP_DELTA,
and PATH_REGISTRY. It does not modify MASTER_ROADMAP. M0 commit is local only.

## M1 — read-only inventory and disposition

Inventory these exact root boundaries without following reparse points:

- D:\QI-Crawler
- D:\QI-Crawler-Candidates
- D:\QI-Crawler-Acceptance
- D:\QI-Crawler-Rollback
- C:\Users\Admin\AppData\Local\QI-Crawler

The only possible deletion targets are these exact direct app children:

1. D:\QI-Crawler-Candidates\v0.10.0-376efdad-20260918T092709Z\app
2. D:\QI-Crawler-Candidates\v0.10.0-f3856385-20260918T152214Z\app
3. D:\QI-Crawler-Candidates\v0.10.0-55c0bddf-20260921T093954Z\app
4. D:\QI-Crawler-Candidates\v0.10.0-fb8edac-20260921T010751Z\app

For each exact target, record the resolved target and parent identity, source
Git SHA and object availability, portable QI-Crawler.exe / BUILD_INFO /
release_manifest hashes, external receipt hash and identity-field match,
logical bytes and file count, ancestor/root/descendant reparse census,
active/current/historical WP references, operational/rollback/reproduction
role, exact-binary need, protected sibling identity, process evidence,
disposition, and the authority/gate for that disposition. Source availability
does not prove a byte-identical rebuild. An unresolved or mismatched field is
KEEP_PENDING_REVIEW.

M1 must not record database rows, HSMT content, configuration secrets, or raw
sensitive logs. Database evidence is limited to authorized path, size,
timestamp, and SHA-256 metadata required for protected before/after comparison.

~~~text
EVIDENCE_PATH_ID = PATH.EVIDENCE.WP_RUN
EVIDENCE_ROOT = release_staging/evidence/WP-ENG-QI-CRAWLER-STORAGE-CONSOLIDATION-01-{UTC_RUN_ID}/
RAW_MANIFEST = RAW_INVENTORY.json; LOCAL_ONLY; NEVER_STAGE_OR_PUBLISH
SANITIZED_RECORD = DISPOSITION.md; Git-safe content only; local commit permitted
PER_TARGET_RECEIPTS = DELETE_01_RECEIPT.json through DELETE_04_RECEIPT.json only when M2 gates pass
FINAL_RECORD = FINAL_SUMMARY.md
EVIDENCE_BUDGET = MAX_FILES=8; MAX_DIRS=1; MAX_BYTES=67,108,864; MAX_RUNS=1
MIN_D_FREE_BYTES = 10,737,418,240 before creating M1/M2 retained evidence
TASK_TEMP_OR_TREE_COPY = NONE
BUDGET_EXCEEDED_OR_RESERVE_BREACHED = HOLD; NO_PRUNE_OR_DELETE
~~~text

The evidence root is created only after checking the registered path and run-id
collision. Keep all evidence after the WP; cleanup is not authorized. Stage or
commit only the exact sanitized record/receipts after verifying they contain
no sensitive content. Never stage the raw manifest or unknown artifacts.

## Conditional deletion gates

A target may be deleted only when every item below is proven for that target:

1. It has no current operational or rollback role.
2. No active WP requires the exact binary for recovery, reproduction, or comparison.
3. A portable artifact receipt outside app exists and matches the current
   executable, BUILD_INFO and release_manifest hashes and identity.
4. The source Git object is available; this is not treated as a byte-identical
   rebuild guarantee.
5. Human A0 accepted loss of the exact bytes for this allowlisted app subtree.
6. Data-root, control, evidence and output siblings and their required receipts
   are identified as KEEP.
7. The resolved absolute path is the exact allowlisted direct app child inside
   D:\QI-Crawler-Candidates.
8. Every existing path component and every app descendant is free of symlink,
   junction, or other reparse points; identity is stable through point of use.
9. Process census permits the operation under the rule below.

Always KEEP:

- D:\QI-Crawler\Current, D:\QI-Crawler\Data, and D:\QI-Crawler\control.
- Every candidate root and every candidate data-root, control, evidence, and
  output subtree.
- Candidate apps f6782d7e and b4f016d7.
- All Acceptance and Rollback content and all AppData.
- Repository source, tests, migrations, packaging, scripts, docs, templates,
  and tracked root helpers.
- Every unknown, unclassified, denied, reparse-containing, mismatched, or
  otherwise unproven path.

## Process census and M2 execution

Primary census is a path-aware CIM process census. Fallback is the exact
trusted C:\Windows\System32\tasklist.exe image-name census for
QI-Crawler.exe. Get-Process Path is supplemental only.

- Run the inventory census within two minutes before inventory.
- Run one immediate target-specific census within two minutes before each
  deletion. At most one retry is allowed only for a clearly transient read
  error.
- An exact target path match holds that target.
- A tasklist image match without executable-path authority holds every app
  deletion in the batch.
- If both primary and fallback routes are unavailable or malformed, hold all
  deletion and finish inventory only.
- A valid zero-match fallback may proceed with its limitation recorded.
  Get-Process no-match alone is insufficient.
- Never change ACLs, take ownership, or elevate to improve observation.

Use one native PowerShell flow end-to-end and process targets sequentially.
Immediately before each deletion, resolve and prove the exact absolute target
is still the allowlisted direct app child inside D:\QI-Crawler-Candidates,
recheck identity and all reparse components/descendants, then use
-LiteralPath without wildcard expansion. After each target, enumerate safely,
verify protected siblings and emit its receipt before considering another.

If deletion errors, enumeration is incomplete, or any target remains, record
PARTIAL_DELETE and TARGET_COMPLETE=NO; stop the entire deletion batch
immediately, do not retry or continue, do not change ACLs, and safely record
the remaining state, exact exception, pre/post counts and logical bytes, target
identity, and protected sibling checks. Update CURRENT at this blocker and
return to Planner.

For every target keep these values separate:
PRE_DELETE_LOGICAL_BYTES; POST_DELETE_REMAINING_LOGICAL_BYTES;
LOGICAL_BYTES_REMOVED; OBSERVED_VOLUME_FREE_SPACE_DELTA. The free-space delta
may include concurrent activity, allocation-unit effects, compression, sparse
or hardlink behavior, and other volume changes. Do not call it exact cleanup
contribution.

## Verification and protection contract

Before and after M2 prove the live install and its Current/Data/control,
database path/size/timestamp/hash, current EXE/manifest/BUILD_INFO/receipts,
AppData, Acceptance, Rollback, protected candidate f6782d7e/b4f016d7 and all
retained candidate subtrees are unchanged, except ordinary unrelated
concurrent timestamps explicitly classified. Prove repository source/test
bytes unchanged.

Run governance/path-registry validation, exact scope accounting,
git diff --check and git diff --name-status. Run only narrow Agent Workbench
or governance tests applicable to changed docs/registry. No full product
pytest or Ruff is required because source/test edits are prohibited; any
source/test change is STOP_SCOPE_VIOLATION. Hosted CI is not part of this
local-only assignment.

## Plugin applicability and evidence

- ecc:git-workflow = REQUIRED for entry and branch handling.
- ecc:github-ops = REQUIRED for authenticated PR #134 read-only verification.
- ecc:living-docs-governance = REQUIRED before Spine writes.
- ecc:safety-guard = REQUIRED before external candidate deletion.
- qi-context-boot = REQUIRED before declaring readiness; read-only.
- CodeGraph = NOT_APPLICABLE unless a new product-code question arises.

Record plugin, purpose, invocation, result, fallback, impact radius, edit
radius, test radius, and limitations. Installed/configured is not proof of use.

## Stop conditions and handoff

Stop on wrong checkout/origin/branch/head, tracked dirty entry, conflicting
writer, unresolved roadmap/role authority, unregistered destination, scope
expansion, source/test change, exact-binary role unresolved, receipt mismatch,
path escape, any reparse component/descendant, unresolved process evidence,
protected artifact drift, access denied on a target census, or any partial
delete. Unknown remains KEEP.

M0, M1, eligible M2 evidence, and governed post-review metadata may receive
semantic local commits under this lease. The normal branch push and single PR
were completed; one terminal docs-only commit and normal push to the same PR
are authorized, followed by exact-head required-CI monitoring. MERGE=HUMAN_ONLY;
RELEASE=NO; further deletion and unrelated CLEANUP=NO.
Return exact identity/branch/commits, entry gates, per-target dispositions,
process/reparse/receipt evidence, bytes/free-space, protected post-check,
changed paths, validations, plugins, limitations, and Spine state.

~~~text
SPINE_IMPACT = CURRENT | ROADMAP_DELTA | WORK_ORDER
SPINE_TARGET_FILES = docs/agent_handoff/CURRENT.md; docs/agent/MASTER_ROADMAP_DELTA.md; docs/superpowers/plans/WO-ENG-QI-CRAWLER-STORAGE-CONSOLIDATION-01.md
SPINE_SYNC_STATE = PASS_FOR_TERMINAL_REMOTE_CHECKPOINT_SYNC
EXACTLY_ONE_NEXT_ACTION = BUILDER_COMMITS_AND_PUSHES_ONE_TERMINAL_DOCS_SYNC_TO_PR135_THEN_MONITORS_REQUIRED_CI_ON_EXACT_NEW_HEAD; AFTER_GREEN_HAND_TO_HUMAN_A0_FOR_MANUAL_MERGE
NEXT_AUTHORITY = BUILDER_SINGLE_WRITER_FOR_REMOTE_INTEGRATION_ONLY_UNTIL_TERMINAL_HEAD_REQUIRED_CI_GREEN; THEN_HUMAN_A0
~~~
