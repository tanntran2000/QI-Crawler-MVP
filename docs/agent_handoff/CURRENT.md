# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-GOV-03

## HANDOFF_REVISION

1

## WP

WP-GOV-03 — Release & Version Governance Contract

## Status

LOCAL WORK IN PROGRESS / NO MERGE

## SNAPSHOT_HEAD

`6a5766fbdf2625b3470ed2abe5847ad976d931ba` (approved base)

## UPDATED_BY_ROLE

BUILDER_SINGLE_WRITER

## Mission

Create durable governance for QI-Crawler application versioning, release
impact awareness, and Team Bid release identity.

## RELEASE IMPACT

NO — this Work Package changes governance/docs only and does not change
user-visible application behavior.

## VERSION IMPACT

NONE — observed application version remains `0.7.1`; no version bump is
authorized in this Work Package.

## Current verified state

- Canonical checkout: `egp-crawler-python`.
- Branch: `wp/gov-release-version-contract`.
- `HEAD == origin/main ==
  6a5766fbdf2625b3470ed2abe5847ad976d931ba` at entry.
- PR #41 (WP-GOV-02) is merged into this exact main commit; live GitHub is
  authoritative for volatile PR/CI/merge state.
- `pyproject.toml` and `src/qi_crawler/__init__.py` both report `0.7.1`.
- `CHANGELOG.md` contains `0.7.1` and an `Unreleased` section.
- Main contains the approved Memory v3 and Human Collaboration governance.

## Completed in this Work Package

- Added normative release-impact and one-release/one-version/one-SHA/build
  identity rules to `AGENTS.md`.
- Added release-aware prompt requirements to
  `docs/agent/HUMAN_COLLABORATION.md`.
- Added the implementation-to-release lifecycle to
  `docs/agent/OPERATING_MODEL.md`.
- Archived the completed WP-GOV-02 snapshot at
  `docs/agent_handoff/history/CURRENT_pre_wp_gov_03.md`.
- Replaced this file with the single active WP-GOV-03 snapshot.

## Locked decisions

- Semantic versioning: PATCH for stability without capability, MINOR for new
  capability or significant GUI/workflow change, MAJOR for breaking contracts.
- Docs-only, test-only, CI-only, and internal refactor commits without
  user-visible effect do not automatically require a version bump.
- Human approves the official Team Bid release/publish.
- `CHANGELOG.md`, a Git commit, or `main` alone is not an official release.
- Historical tags/releases are immutable identities.
- Next release implementation/build work belongs to WP-REL-01.

## Scope / files

Documentation/governance only:

- `AGENTS.md`
- `docs/agent/HUMAN_COLLABORATION.md`
- `docs/agent/OPERATING_MODEL.md`
- `docs/agent_handoff/CURRENT.md`
- `docs/agent_handoff/history/CURRENT_pre_wp_gov_03.md`

`MEMORY_INDEX.md` was not changed because discoverability already includes the
Human Collaboration Contract. No production, tests, schema, migrations, CI
workflow, dependencies, version files, build/publish scripts, business data,
runtime data, installer, tag, release, or `.codegraph/` state is in scope.

## Verification

- Collection baseline: `452` tests collected.
- Targeted tests: NOT REQUIRED; governance/docs-only Work Package.
- Full pytest: `452 passed` in `358.24s` (one known cache-permission warning).
- Ruff: PASS (`ruff check .`).
- `git diff --check`: PASS.
- Changed-file check: limited to the five governance files listed above.

## Pending / unverified

- Commit, push, one Draft PR, and natural CI are delivery steps; live GitHub
  remains the authority for their volatile state.
- Commit, push, one Draft PR, and natural CI are delivery steps; live GitHub
  remains the authority for their volatile state.
- No version bump, tag, GitHub Release, build, publish, or Team Bid Reference
  has been performed or authorized by this Work Package.

## Risks / blockers

- A later user-visible change must complete a release-impact assessment before
  implementation and must not silently omit version/build compatibility work.
- Version mismatch across app, runtime, GUI, installer, `BUILD_INFO`, and
  manifest is a release-gate failure.

## Explicitly NOT done

No application version bump, production code, tests, schema, migrations, GUI,
crawler, extraction, CI workflow, dependency change, EXE/installer build,
publish, Git tag, GitHub Release, Team Bid Reference, AI, Legal, scoring, or
business-data change was made.

## Next objective

### NEXT

WP-REL-01 — Team Bid Verified Reference Release.

### WHY

WP-REL-01 owns canonical version implementation, GUI version display, release
manifest, safe Windows build/recovery, compatibility smoke, and the human
release decision.

### ENTRY CONDITION

WP-GOV-03 is merged and the release Work Order has a verified baseline and
explicit Human authority for version/build actions.

### STOP CONDITION

HOLD on version mismatch, missing release evidence, scope/baseline/writer
conflict, or any request to publish without explicit Human authority.

### EXPECTED OUTPUT

A verified governance contract ready for WP-REL-01; no release artifact is
created by this Work Package.

## Relevant files

- `AGENTS.md`
- `docs/agent/MEMORY_INDEX.md`
- `docs/agent/OPERATING_MODEL.md`
- `docs/agent/HUMAN_COLLABORATION.md`
- `docs/agent_handoff/history/CURRENT_pre_wp_gov_02.md`
- `docs/agent_handoff/history/CURRENT_pre_wp_gov_03.md`
- `pyproject.toml`
- `src/qi_crawler/__init__.py`
- `CHANGELOG.md`

## Tool state

CodeGraph is not required for this docs-only Work Package and remains
uninitialized/local-only. Superpowers process was followed through Entry
Review and one Approval Lease. No external plugin state was added.

## Handoff instructions

Read `AGENTS.md`, then the Memory Index order including the Human Collaboration
Contract, then this snapshot and live Git/GitHub state. Treat live evidence as
newer than tracked prose. Do not bump version, build, tag, publish, or start
WP-REL-01 without the next approved Work Order.
