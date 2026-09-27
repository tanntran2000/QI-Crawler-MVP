# WP-ENG-QI-CRAWLER-STORAGE-CONSOLIDATION-01

## Status, authority, and baseline

~~~text
STATUS = ACTIVE; M0_ENTRY_RECONCILED; M1_PENDING; M2_CONDITIONAL
ROLE = BUILDER_SINGLE_WRITER
AUTHORITY = Human A0 exact approval recorded in Planner task 01a0d14b-4e41-7480-9179-d1b230295f77 on 2026-09-27
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
live main. M0 uses one semantic local commit. No remote write is authorized
in this Work Order.

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
MUST_NOT_DO = start or stop the application; migrate, mutate, copy, or open an operational DB; change ACLs or take ownership; elevate to improve observation; clean unknown artifacts; use wildcard deletion; push; create PR; merge; release
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

M0, M1, and any eligible M2 evidence may receive semantic local commits under
this lease. PUSH=NO; PR=NO; MERGE=NO; RELEASE=NO; unrelated CLEANUP=NO.
Return exact identity/branch/commits, entry gates, per-target dispositions,
process/reparse/receipt evidence, bytes/free-space, protected post-check,
changed paths, validations, plugins, limitations, and Spine state.

~~~text
SPINE_IMPACT = CURRENT | ROADMAP_DELTA | FEEDBACK | PATH_REGISTRY
SPINE_TARGET_FILES = docs/agent_handoff/CURRENT.md; docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent/FEEDBACK_LEDGER.md; docs/agent/PATH_REGISTRY.yaml
SPINE_SYNC_STATE = PASS only when exact facts reconcile
EXACTLY_ONE_NEXT_ACTION = BUILDER_PERFORMS_M1_READ_ONLY_INVENTORY_AND_DISPOSITION
NEXT_AUTHORITY = BUILDER_SINGLE_WRITER under the active Human-approved lease
~~~
