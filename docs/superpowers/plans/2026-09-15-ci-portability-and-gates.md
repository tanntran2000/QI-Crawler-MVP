# QI-PR103-CI-PORTABILITY-GATES-01

## Authority and intent

Parent: QI-PR103-CI-HARDENING-01. Human request on 2026-09-15 authorizes
design, implementation, durable CI law, verification and normal branch push
to make PR 103 merge-ready. Merge/release remain for Human review after the
result. This bounded successor reconciles the previous A2 handoff: run
34935783050 on 6069980 failed with 23 Windows tests depending on absent local
release artifacts. No previous independent PASS is inferred.

PLANNER_ARCHITECT: root task (design, evidence reconciliation, integration).
BUILDER_SINGLE_WRITER: delegated ci_builder (sole code/test/workflow writer).
REVIEWER_AUDITOR: separate agent assigned only after Builder return.
Machine evidence: Builder/local commands and GitHub Actions; no audit authority.

CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
BASE_SHA = 6069980d343c46e1a3022859dcf67dc3bcadd170
BRANCH = release/v0.10-recon-01
PR = 103; base main observed 27d72a6f9ba7bce0a133aa06b97585812792f390.
Verify live state at each integration boundary. No worktree, clone, reset,
amend, rebase, force push, deletion of existing artifacts, or release execution.
Leave pre-existing untracked output/prep_data/tmp/patches/uv.lock untouched.

## Blueprint and entry

READ_MODE = FULL for role takeover; same-WP continuations reuse valid context.
Roadmap revision 1.3, SHA256
E097156C9C5F18D4DB28A23D957A3C49750D69948AE1F4A309D5DBD2573D4D2D.
Frontier remains Unified Tender Warehouse / PARTIAL.
Node: Cross-cutting — Quality / CI / release governance.
Relevant Delta: RD-0007 integrity/evidence discipline; RD-0008 protected source
and recovery boundaries. No product maturity promotion. This is the explicitly
Human-authorized bounded CI work; it does not activate every future CI program.
Architecture layers: engineering tools/test infrastructure IN_SCOPE;
Domain, backend, persistence schema, source adapters, GUI/API/AI OUT_OF_SCOPE.
Legacy real release validation must remain strict at its compatibility seam.

Mandatory reads: AGENTS, MEMORY_INDEX, OPERATING_MODEL role/coordination,
ROLE_BOOT profile, HUMAN_COLLABORATION, LOCAL_STAGED_INTEGRATION, full Roadmap,
relevant Delta, PROJECT_MEMORY, FM-009 and relevant A3 failures/lessons,
CURRENT, this order, CI workflow, exact affected source/tests.

## Design and authorized write scope

1. Make A3 synthetic/dispatch tests reproducible without historical EXEs or
   controller files from release_staging. Exercise the real guard/route logic;
   do not skip/xfail failing Windows tests or simulate release acceptance.
   Keep normal release artifact/hash/lock/lifecycle validation strict.
2. Preserve the existing four CI jobs and supported Python/OS coverage while
   adding PR concurrency cancellation, bounded diagnostic artifacts, collection
   accounting and a final fail-closed Required CI Gate. No path-based test
   omission in this first implementation; routing optimizations require proof.
   Evidence must identify actual checkout SHA (PR merge preview vs source head).
   Collect JUnit/timings/dependency identity on failure as well as success.
3. Establish durable CI laws in AGENTS and one supporting CI contract. Laws:
   clean-checkout reproducibility; explicit product/engineering/release test
   ownership; no silent skips/coverage erosion; finite evidence-based budgets;
   strict gate success; exact evidence; controlled dependency updates; bounded
   artifacts; production/release authority separate; risk-based evolution for
   future capabilities. Distinguish implemented controls from future criteria.
4. Route Human request/failure lesson to narrow canonical Spine authorities,
   update CURRENT at handoff with exact known facts, and register this WP.

Exact existing scope: .github/workflows/ci.yml; tools/release/a3_probe_windows.ps1;
tools/release/a3_f5_guard.ps1 if present; tests/a3_f5_synthetic_route.ps1;
tests/test_a3_f5_guard.py; tests/test_a3_f5_final_integrity.py;
tests/conftest.py only if collection/evidence isolation requires it;
scripts/ci_windows_runtime_attribution.py; pyproject.toml only for pytest config;
AGENTS.md; docs/agent/PATH_REGISTRY.yaml; docs/agent/FEEDBACK_LEDGER.md;
docs/agent/KNOWN_FAILURE_MODES.md; docs/agent/LESSONS.md;
docs/agent_handoff/CURRENT.md. Additional existing guard filename may be resolved
from imports before writing and recorded in the Builder packet.
New bounded files: docs/agent/CI_CONTRACT.md; scripts/ci_gate.py;
scripts/ci_test_evidence.py if needed; tests/test_ci_contract.py;
tests/test_ci_gate.py; tests/test_ci_test_evidence.py if needed;
tests/a3_ci_fixture.ps1 if needed; tests/a3_ci_controller.py for the explicit
synthetic handshake controller fixture (not an actual release controller).
No speculative scaffolding.
Planner owns this Work Order; Builder does not edit its authority.
Unmerged implementation facts do not enter PROJECT_MEMORY.

## Acceptance and CI fitness

Classification: FIT_WITH_ADDITION; preserve baseline four required jobs.
Critical risks: bypassed release guard; tests passing because dev artifacts
exist; fake CI success after skipped/cancelled jobs; lost collection; process
leaks; uncontrolled disk growth; false merge/release claim.
TDD RED: existing failing paths plus focused regression reproducing absent
staging/invalid gate results. GREEN must retain fault-specific assertions.
Gate tests must cover failed/cancelled/skipped/missing/unknown job results.
Collection evidence must account for collected/executed/skipped tests and
report decreases; do not enshrine a historical integer as a universal baseline.
CI does not certify arbitrary future functionality; future WPs own risk gates.

Verification order: baseline collection; focused pytest; full pytest;
Ruff; git diff --check; git diff --name-status; independent exact-range review;
push; fresh hosted CI on the resulting PR object; reconcile final live state.
Local targeted budget 15 min, full suite 45 min; shell commands return sessions
for ongoing work. Windows CI retains 45 min, Linux jobs 20 min, quality 10 min;
new final gate max 3 min. No increases solely to mask defects. One transient
infra retry maximum; assertion defects require correction. Full pytest once
per material implementation, broaden/repeat only for new findings/changes.
No real A3 rearm/RealF5 trial, installer deployment, or business data access.
Release impact: CI/test/governance and release-tool boundary correction only;
no delivered application capability/version change or release authorization.

## Paths, budget and evidence

PATH_REGISTRY_BASELINE = 1.0.6 / SHA256
C07E58B63AF999230EFCDF14C55EF9777D6963CC2E5F210E16310114D66FB103.
Use existing PATH.GOV.PLAN, PATH.GOV.DOCUMENT, PATH.GOV.HANDOFF and the registered
CI/scripts/tests/tools/root-helper families; resolve their exact IDs before
writing. Registry update is locator-only. Work Order artifact: this file,
Planner-owned, durable governance; consumer Builder/Reviewer/Human; <=16 KiB.
New durable implementation/docs budget: <=9 files, <=128 KiB combined.
Temporary output: .tmp/QI-PR103-CI-PORTABILITY-GATES-01/{run_id}/ under registered
test-temp family. Approved compact execution alias `.tmp/CI103/{run_id}/`
maps exclusively to this same WP (not a new WP); use it for Windows PowerShell
5.1 path-length constraints and record it in the WP locator scope. The long
first-run directory is retained as failure evidence, not deleted.
<=4 local test runs initially, <=4 GiB total, retain >=10 GiB
free on C and D. Manual preflight/accounting, not claimed filesystem enforcement.
Evidence: release_staging/evidence/QI-PR103-CI-PORTABILITY-GATES-01-{run_id}/,
<=12 files and <=16 MiB total. Retain logs/results and one Builder report;
Reviewer report <=32 KiB. No duplicate runtime trees or whole-repo copies.
Dispositions: code/law KEEP_PRODUCT; reports KEEP_EVIDENCE; test temp
KEEP_PENDING_REVIEW owned by Builder until authorized exact cleanup.

PLUGIN_APPLICABILITY: CodeGraph REQUIRED for impact discovery (test guard,
synthetic route, probe seed queries), fallback raw inspection for unindexed PS1
or failed symbol resolution. Superpowers debugging/TDD/verification REQUIRED;
record invocation/result, impact vs edit vs test radius. No plugin changes.

SPINE_IMPACT = GOVERNANCE; FEEDBACK; FAILURE_MEMORY; CURRENT (LESSONS if useful).
SPINE_TARGET_FILES = authorized files above. Resolve SPINE_SYNC_STATE before
handoff. Recheck Delta at entry, material finding and return; no routine diary.

## Return and stop

Return actual changed paths, collection delta, test commands/results, artifact
bytes/disposition, release impact, plugin evidence, limitations and exact head.
Stop for Planner on material scope expansion, missing reusable source needed
to preserve behavior, authority conflict, failed bounded triage, or unexplained
concurrent tracked changes. Routine fixes within this contract are leased.
Builder returns to Planner for result review then independent Reviewer.
Planner pushes audited commits to existing branch and reports hosted result.
Final state: merge-ready evidence for Human review; no automatic merge/release.

## Remote enforcement and report clarification

Within the Human request to make CI a lasting protective law, Planner may
activate existing ruleset 21023970 (QI-Crawler Main Safety Fence) after fresh
hosted success, adding the exact final CI gate check bound to GitHub Actions.
Preserve its existing PR, deletion, force-push, review and bypass settings.
Capture before/after JSON in the bounded evidence directory and verify readback;
do not create a duplicate protection system. No bypass will be exercised.
Planner may update the existing PR title/body with scope and verification
evidence; no fabricated GitHub review approval. These actions do not authorize
merge, tags or Team Bid release. Existing PR history before BASE_SHA is not
automatically independently certified by this correction review.

## Bounded follow-up: process identifier reuse

Planner scope reconciliation after full local run: 1252 passed, one synthetic
fault test failed before its intended checkpoint with F5_P1_JOB_LINEAGE_UNPROVEN.
Its Toolhelp ancestry included a live SmartAudio process created hours before
the test controller. Bare parent process IDs can refer to reused identities.
The same Human CI-reliability intent authorizes the same single Builder to
correct chronology validation in the already scoped a3_probe_windows.ps1 and
add regression coverage in existing tests/test_a3_native_lineage.py. Register
that exact test path in this WP locator. No product-source or native-helper
expansion is authorized. Reject proven impossible older-child edges; unavailable
or ambiguous identity metadata must remain fail-closed. Never intersect away
unknown descendants merely because they are outside the Job object.
Require deterministic RED/GREEN cases for PID reuse, unknown metadata and valid
ancestry, then relevant native tests and a fresh full suite before completion.
This is a diagnosed correction, not an infrastructure rerun or timeout increase.
Extend local execution allowance to at most 7 run directories within the same
4 GiB total and 10 GiB free-space reserves; retain failed evidence separately.

### Snapshot/ancestry contract reconciliation

The next full suite returned 1256 passed / one containment-characterization
failure. A bounded diagnostic proved the launcher had exited before observation:
Toolhelp enumeration succeeded, but creation identity for the absent parent was
unavailable. Job membership, live survivor, false-zero rejection and termination
checks all held. Authorize the same Builder to expose raw snapshot_status apart
from existing PARTIAL/UNRESOLVED ancestry, and update existing
tests/a3_p4_characterize.ps1 and tests/test_a3_p4_containment.py to assert these
separate contracts. Register both paths. Preserve all Job containment assertions
and production fail-closed ancestry gates; missing parent identity is not COMPLETE.
Add deterministic absent-parent evidence coverage in the scoped native tests.
Allow at most 10 local run directories and 14 evidence files, retaining the same
4 GiB local / 16 MiB evidence limits and free-space reserves. Retain both failed
full results; subsequent results use distinct names. No blanket retries.

## Forward correction from independent cumulative review

Correction commit d713f0525ca0546995c3c956b45309d0d49b1ce5 independently passed;
cumulative PR review found C1/C2 in the preexisting maintenance primitive.
To satisfy the Human request for a merge-reviewable branch, Planner authorizes
the same single Builder to correct only src/qi_crawler/update_transaction.py
and tests/test_update_transaction.py, plus the already scoped registry, failure
memory, feedback/lesson and transition handoff if triggered. This explicit
follow-up supersedes the earlier product-source exclusion for this one module;
no other product source, migration, installer or API expansion is authorized.

C1: journal I/O failure after resource acquisition must release SQLite and owner
lock independently, even when cleanup itself fails, without falsely recording
COMPLETE or losing the original error. C2: recovery journal selection/content
must be revalidated under ownership so concurrent completion cannot be reopened
from a stale pre-lock snapshot. Preserve exactly-one-incomplete and hard-crash
recovery semantics. Use existing module, no parallel implementation.

Baseline is exact d713f05; record fresh collection. Required TDD RED/GREEN:
start/resume/complete journal failure, resource reacquisition, cleanup failure
independence, and deterministic completion-between-read-and-lock interleaving.
Run targeted transaction regressions, then full default pytest, Ruff/diff; retain
all previous CI evidence. Independent Reviewer rechecks the forward Git range
and reconciles cumulative verdict before merge recommendation. No merge/release.

RELEASE_IMPACT_ASSESSMENT: current references are module/tests only, no observed
product caller. This is failure-safety correction of an unintegrated primitive;
no user-visible feature/schema/package behavior or version bump is claimed.
If new runtime exposure is discovered, return to Planner before broader edits.
Register the two exact paths; route C1/C2 prevention without promoting unmerged
facts to PROJECT_MEMORY. Allow at most 12 local run directories / 16 evidence
files with unchanged 4 GiB temp,16 MiB evidence and10 GiB free-space limits.
Update existing Builder/Reviewer reports with distinct follow-up evidence; never
overwrite earlier full results. Final hosted CI must correspond to final code.
