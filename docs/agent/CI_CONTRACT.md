# Crawler CI protection and evolution contract

Authority: Human request of 2026-09-15, implemented through
`docs/superpowers/plans/2026-09-15-ci-portability-and-gates.md`.
This contract supports AGENTS; it does not grant merge, release or A3 trial
authority. It applies to future Crawler work through each WP's CI Fitness
Contract. Product frontier remains Unified Tender Warehouse / PARTIAL.

## Required baseline and final gate

| Job | Contract | Maximum runtime |
| --- | --- | --- |
| Code Quality | Ruff across the checkout | 10 minutes |
| Tests Ubuntu 3.12 | Full default pytest, including GUI offscreen | 20 minutes |
| Tests Windows 3.12 | Full default pytest, including native engineering tests | 45 minutes |
| Compatibility Ubuntu 3.11 | Full default pytest on supported older Python | 20 minutes |
| Required CI Gate | All four baseline job results equal success | 3 minutes |

Budgets preserve the verified baseline; Windows history and escalation are in
FM-009. They are ceilings, not performance targets. Exceeding one triggers
bounded triage; never raise it merely to turn a red run green. Assertion failures
require corrections; transient infrastructure allows at most one retry.

The final gate executes with `always()` and rejects missing, failure, cancelled,
skipped or unknown baseline results. Never use it only as a reporting/comment
job. PR commit concurrency cancels superseded runs; cancelled runs are not
evidence for the current commit. Main runs retain verification.

Required-check names in GitHub must agree with workflow job names. Repository
ruleset activation, bypass permissions and branch coverage must be read back
from GitHub at integration. A workflow file alone does not enforce branch
protection. Existing CodeQL/default-setup checks remain a separate protection.
Before merge, verify live ruleset activation, exact required-check contexts and
bypass permissions against the final commit. Preserve the readback as integration
evidence; neither this durable contract nor an earlier run proves current enforcement.

## Test ownership and clean runner rule

1. **Product regression:** source discovery, pagination, retry/resume, dedup,
   identity/provenance, persistence/migrations, Warehouse/recovery and GUI
   behavior. Use controlled fixtures; no live business input or destructive
   installed-app execution on ordinary PRs.
2. **Engineering contracts:** PowerShell, process containment, lock/lifecycle,
   path boundaries, synthetic fault injection and evidence/gate logic. They
   run in default pytest on their applicable platform from tracked inputs and
   installed declared dependencies. They must not read an old developer
   `release_staging` tree, a prior WP output, or an installed release.
3. **Real release acceptance:** exact installer/EXE, build manifest/hash,
   upgrade/rollback, real specimen and authorized RealF5 trials. Supply and
   validate explicit immutable inputs before execution; missing inputs mean
   HOLD/FAIL. Synthetic actors are never proof of release acceptance.

These are ownership categories, not a reduction of current execution coverage.
All four existing jobs remain. Windows-only platform skips on Linux are
expected and recorded; their Windows execution remains mandatory. A new skip,
xfail, removed test or moved category requires a reviewed reason and a named
replacement gate where applicable. Never manufacture duplicate tests to meet
a count. No `continue-on-error`, blanket retries or environment-based pass.

The A3 dispatch checkpoint validates the guard/context/held-lock boundary and
reports P1-P5 NOT_RUN. Only that previously-authorized test checkpoint avoids
loading historical release payloads. Normal F5Only and Sequential execution
retain real artifact loading and strict validation. The synthetic canonical
route uses a tracked test actor and small Windows utility fixtures; the real
probe still performs observation, job containment, recovery and verdict checks.
`UseFrozenStub` retains its explicit frozen release dependencies.

Process ancestry checks must use lifetime evidence in addition to PID/PPID;
proven stale edges are recorded and unknown metadata fails closed. Windows
scratch prefixes remain compact because legacy PowerShell/.NET paths can hit
MAX_PATH even when free disk space is sufficient.

## Evidence and collection integrity

Each test job captures a pre-run collection and compares the executed suite's
ordered node IDs against it, rejecting selection drift/deselection. Evidence
includes collection/outcome counts, skipped/not-executed accounting, JUnit,
slowest-test timings, dependency freeze, Python/OS, GitHub run/attempt, source
head and actual checkout SHA (PR merge preview may differ from source head).
On failure diagnostics are retained where the runner remains available.

Cross-commit collection reductions must be reviewed against exact prior
evidence and the WP; this implementation does not automatically fetch previous
CI artifacts or treat an old integer as a universal count floor. Collection
errors, failing tests and unexplained reductions block completion. Every
planned future test partition must prove that its union preserves ownership
and coverage before replacing a baseline job.

CI run scratch uses `.tmp/CI/{UTC-run-id}/` under PATH.DEV.TEST_TEMP;
`CI` is the workflow-owned execution alias, not a new WP. Diagnostics are at
most 12 files / 16 MiB per job, uploaded for 7 days. Budget rejection fails the
job and preserves console evidence instead of uploading an unbounded payload.
Cancellation can prevent artifact publication; absence is not PASS. Ordinary
runner scratch is discarded by the runner lifecycle. Local runs use the WP's
explicit path, byte budget, free-space reserve and cleanup authority.

## Dependency discipline and future capability gates

Dependency updates are reviewed changes and must pass all supported-platform
gates. Pip cache is an optimization, never an input authority; record resolved
versions. This correction retains existing version ranges and pip caching;
it does not claim a fully locked environment. A future lock/constraints change
must prove supported-platform resolution and a bounded update procedure.

Each future WP maps its changed capability/risk to acceptance evidence:

| Capability | Minimum risk-directed evidence when changed |
| --- | --- |
| Crawler/source adapters | discovery, pagination, retry/resume, dedup, provenance |
| Warehouse/persistence | SHA, exact revision membership, migrations, recovery, no data loss |
| HSMT/extraction | boundary rows, completeness, source conflict/missing-source handling |
| Evidence/Ground Truth | locator fidelity, append-only corrections, Golden regression |
| GUI/delivery | backend authority, supported-platform startup and workflow regressions |
| AI/learning | authority boundary, deterministic fallback, confidence/routing regression |
| Packaging/release | exact artifact identity, compatibility, upgrade/rollback, Human authority |

Do not activate unbuilt future capability gates. Path-based job omission and
parallel pytest are not implemented here: introducing either requires impact
coverage and filesystem/process/lock isolation evidence. Test count, a green
summary and number of jobs do not substitute for a fit verification contract.
