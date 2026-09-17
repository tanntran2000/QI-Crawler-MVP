# C3 Verification Contract — A3/F5 Cumulative Acceptance

Status: FROZEN BEFORE C3 EXECUTION

This document is the pre-execution contract for the cumulative C3 verification
of the already-merged A3/F5 corrections. It is a durable governance artifact,
not a run report and not an execution grant.

~~~text
PATH_REGISTRY_GATE = PASS
PATH_REGISTRY_BASELINE = revision 1.0.8; SHA256:4782AB372AAE6C09BC1DE1EE87BD4E38E138046483D8799A818308882B402A9A
PATH_REGISTRY_IMPACT = USE_EXISTING
PATH_ID = PATH.GOV.DOCUMENT
ARTIFACT_ID = ART.A3_F5.C3_VERIFICATION_CONTRACT
ROADMAP_REF = docs/agent/MASTER_ROADMAP.md#cross-cutting--quality--ci--release-governance
WP_ID_AND_AUTHORITY = WO-GOV-QI-A3-F5-C3-ENTRY-RECON-01 / HUMAN_A0_APPROVED_DIRECTION
WRITE_SCOPE = docs/agent_handoff/CURRENT.md; docs/agent/LESSONS.md; docs/agent/C3_VERIFICATION_CONTRACT.md
UNREGISTERED_WRITE_PATHS = NONE
WORK_ORDER = WO-GOV-QI-A3-F5-C3-ENTRY-RECON-01
OWNER = BUILDER_SINGLE_WRITER / later C3 evidence owner
LIFECYCLE = DURABLE_GOVERNANCE_CONTRACT
STORAGE_BUDGET = ONE_TRACKED_CONTRACT_FILE; C3 RUN EVIDENCE USES THE REGISTERED EVIDENCE ROOT
~~~

This contract is created by the entry-reconciliation Work Order. That Work
Order does not authorize C3 execution. A later explicit C3 execution Work
Order must preserve this contract or obtain a governed revision.

## 1. Identity model

~~~text
CODE_BASELINE_SHA = f50a27e7c96385d1770676a68b7371b15fb7daeb
CODE_BASELINE_TREE = 3e51c60bb41bd5b554946777e1a8d7fbced9004d
C3_ENTRY_MAIN = RE_RESOLVE_AFTER_HANDOFF_SYNC
HANDOFF_DOC_SHA = RE_RESOLVE_AFTER_HANDOFF_SYNC
~~~

The C3 code baseline is the merged main object above. The handoff/document
identity is resolved separately after this docs-only sync is merged. A later
C3 run may use a later docs-only main head only when:

~~~text
git diff f50a27e7c96385d1770676a68b7371b15fb7daeb -- src tests tools .github
~~~

is empty. Any source, test, release-tool or workflow difference is
CODE_BASELINE_DRIFT and requires STOP_FOR_PLANNER. A handoff file must not
predict its own future document SHA.

## 2. C3 purpose and non-claims

C3 proves the relationships among the already-merged Finding A, Finding B and
Finding C corrections. It can establish only whether the specified contracts
are sufficiently evidenced for a later Human rearm decision.

C3 does not prove that every possible Windows race is eliminated, that
historical run 350633 has a unique known cause, that Real F5 is safe, or that
no process exists anywhere on the machine. It does not authorize A3 rearm,
Real F5, production access, sandbox reset, release, installer publication or
merge.

## 3. Coverage matrix

C3 must report each finding separately and map every claim to an exact test node,
receipt or source-contract assertion. The evidence level and the required
interpretation are fixed below.

| Finding | Required evidence levels | Required mapping and boundary |
| --- | --- | --- |
| A — process lifetime / containment | UNIT / CONTRACT, NATIVE_WINDOWS, SYNTHETIC_P4_RECEIPT | ProcessHandle-backed creation identity; handle retained through evidence persistence; Job Object remains containment authority; PARTIAL or UNRESOLVED remains HOLD. |
| B — shared canonical role identity | UNIT, CLI, PROBE CONTRACT, native-runtime status | Unit shared-canonical identity tests; observer JSON/config boundary tests; LAUNCH_RECEIPT transport and positive control; WINDOWS_NATIVE_LIVE_SHARED_CANONICAL is not currently proven. If no native-live test exists, record B_NATIVE_LIVE_COVERAGE = GAP_DECLARED; this contract does not authorize a new test. |
| C — scope-complete zero proof | UNIT, CLI observer boundary, P1/P2 Job receipts, P3 Job-drained receipt, P4 route receipts, P5 composite receipt | Scope proof must include bounded observed scope, completeness and a recognized authority. Empty or scopeless observations do not prove zero. |

At execution, the coverage matrix must name the exact test node IDs, evidence
level, expected result, actual result and retained receipt path for every row.
A source statement or copied audit report is not a substitute for the exact
Git/test/receipt object.

## 4. Recovery coverage

C3 records pre-barrier and post-barrier recovery separately. Post-barrier
evidence cannot substitute for pre-barrier coverage.

### 4.1 Pre-barrier requirements

| Input condition | Required result |
| --- | --- |
| Missing scope | RECOVERY_REQUIRED / mutated=false |
| Malformed or unrecognized scope | RECOVERY_REQUIRED / mutated=false |
| Valid scope with schema mismatch | RECOVERY_REQUIRED / mutated=false |
| Valid modern scope, valid schema and valid legacy identity | Expected LEGACY_READY behavior |

Each row must cite its exact test node ID and actual result. No row may be
satisfied by a post-barrier refusal.

### 4.2 Post-barrier requirement

The post-barrier refusal must be recorded as:

~~~text
MAINTENANCE_RECOVERY_REQUIRED
mutated=false
exit=2
~~~

The refusal occurs before ScopeProof evaluation. C3 must show that ordering
explicitly and retain the bounded diagnostic receipt.

## 5. R0–R3 fixture scope provenance

The current recovery failpoint fixture constructs:

~~~text
COMPLETE_PID_TREE
process_tree_complete=true
root_absent=true
tree_dead=true
~~~

before launching the recovery process. C3 must classify this claim as exactly
one of:

~~~text
R0_R3_SCOPE_PROVENANCE = PROVEN_BY_LIFECYCLE
R0_R3_SCOPE_PROVENANCE = FIXTURE_ONLY_NON_MEASURED
R0_R3_SCOPE_PROVENANCE = HOLD
~~~

PROVEN_BY_LIFECYCLE requires evidence of a fresh isolated New-Trial lifecycle,
no process launched in that trial scope before the proof, and no reused sandbox
or process identity. These fixture fields must not be called measured
process-tree evidence unless the lifecycle and identity were actually observed.
There is no auto-fix in C3; a gap routes to the Planner or to a separate
test-only Work Order.

## 6. Bounded execution and positive evidence

C3 does not run the whole repository merely to accumulate another green count.
When a separate C3 execution Work Order authorizes execution, run the relevant
A3/F5 targeted suite once while excluding the canonical rehearsal test from
that suite. Then run exactly these five rehearsal instances:

~~~text
C3_REHEARSAL_1 = test_synthetic_canonical_route_rehearsal
C3_REHEARSAL_2 = test_synthetic_canonical_route_rehearsal
C3_REHEARSAL_3 = test_synthetic_canonical_route_rehearsal
C3_REHEARSAL_4 = test_synthetic_canonical_route_rehearsal
C3_REHEARSAL_5 = test_synthetic_canonical_route_rehearsal
~~~

There is no sixth run and no retry-until-green behavior. A failure is retained
as bounded evidence and reported; it is not hidden by a timeout increase,
skip, xfail, blanket retry or environment-specific pass.

## 7. Required negative coverage

The C3 evidence matrix must include existing tests proving these invariants.
Every entry records its test node ID, evidence level, expected result and actual
result.

| Invariant family | Required negative behavior |
| --- | --- |
| Process identity | Missing or wrong process identity → UNRESOLVED/HOLD; PID lifetime mismatch → UNRESOLVED/HOLD; shared path without binding → UNRESOLVED/HOLD. |
| Scope proof | Missing scope → zero=false; malformed scope → zero=false; incomplete P4 → zero=false; incomplete P5 → zero=false. |
| Recovery | Old scopeless recovery → RECOVERY_REQUIRED; schema mismatch → RECOVERY_REQUIRED; negative aggregate/control fault → HOLD; process or receipt failure → HOLD. |

Unit/CLI/synthetic evidence must stay labelled at its own evidence level. It may
not be promoted to native Windows live-runtime evidence.

## 8. Evidence retention

C3 runtime evidence belongs under the registered path:

~~~text
PATH_ID = PATH.EVIDENCE.WP_RUN
EVIDENCE_ROOT = release_staging/evidence/C3-A3-F5-CUMULATIVE-<RUN_ID>
~~~

This is runtime evidence, not a source-code change. The run must retain exactly
the bounded artifacts required by the C3 execution Work Order:

~~~text
c3_manifest.json
c3_coverage_matrix.json
c3_test_results.json
c3_rehearsal_summary.json
c3_limitations.json
~~~

The manifest must contain:

~~~text
code_baseline_sha
code_baseline_tree
handoff_doc_sha
execution_main_sha
OS / Python identity
trial IDs
test node IDs
receipt paths
SHA256 of retained evidence
storage/budget accounting
~~~

For five passing rehearsals, retain a hash or summary for all five and one
complete representative PASS receipt bundle. For any HOLD, retain the bounded
failure diagnostics and relevant route/gate receipts. Do not copy arbitrary
temporary trees. The finite storage budget and reserve must be resolved from
the applicable path/CI contract before execution; an unknown budget is a
verification hold.

## 9. Verdict and transition

The only C3 verdict values are:

~~~text
PASS_WITH_DECLARED_LIMITATIONS
HOLD_COVERAGE_GAP
HOLD_INVARIANT_FAILURE
~~~

Plain PASS is not a valid C3 verdict. A successful C3 means only:

~~~text
CUMULATIVE_ACCEPTANCE = EVIDENCE_SUFFICIENT_FOR_HUMAN_REARM_DECISION
~~~

It never sets A3_REARM = YES or REAL_F5 = YES. Any missing invariant,
unresolved native-live coverage or unmeasured fixture provenance remains
declared in c3_limitations.json and can force a HOLD.

At freeze time:

~~~text
C3_EXECUTED = NO
A3_REARM = NOT_AUTHORIZED
REAL_F5 = NOT_AUTHORIZED
RELEASE = NOT_AUTHORIZED
MERGE = NOT_AUTHORIZED
~~~

The next authority after this docs-only synchronization is Planner
reconciliation. A separate C3 execution Work Order is required before any
runtime test execution.
