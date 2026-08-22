# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-REL-01

## HANDOFF_REVISION

1

## WP

WP-REL-01 — Team Bid Verified Reference Release, Stage A

## Status

LOCAL WORK IN PROGRESS / NO MERGE

## Snapshot

- Approved base: `ea7b376250c1115fab344f9bd5c981d233b3b7bb`
- Branch: `wp/rel-team-bid-reference`
- Target version: `0.8.0` (approved minor release candidate)
- Release impact: YES
- Version impact: MINOR

## Mission

Prepare a verifiable local Windows release candidate with one canonical application version and auditable metadata. This Stage A does not publish the candidate or create an official Team Bid Reference release.

## Current verified state

- Canonical checkout is on the approved feature branch from the verified main base.
- Canonical runtime version source is `src/qi_crawler/__init__.py`; package metadata is dynamic from that source.
- GUI already displays the package version through `qi_crawler.__version__`.
- Alembic has exactly one head: `0013_add_candidate_review_events`.
- Build and publish plumbing now injects the canonical version, validates the Alembic head, and produces `BUILD_INFO.txt` plus `release_manifest.json` in the isolated candidate staging area.
- No production database has been migrated or modified, and `Crawler tool\Current` has not been touched.

## Completed in this Stage

- Bumped the approved application/package version from `0.7.1` to `0.8.0`.
- Removed active release-script/Inno Setup version hardcodes in favor of canonical version injection.
- Added release governance regression tests and the `0.8.0` changelog entry.
- Added candidate metadata and manifest validation for commit, version, hashes, and Alembic head.
- Archived the prior handoff as `history/CURRENT_pre_wp_rel_01.md` with a historical/non-normative banner.

## Files changed

- `src/qi_crawler/__init__.py`
- `pyproject.toml`
- `packaging/QI-Crawler.iss`
- `build_installer.ps1`
- `scripts/publish_windows_release.ps1`
- `CHANGELOG.md`
- `tests/test_windows_installer.py`
- `tests/test_release_governance.py`
- `docs/agent_handoff/CURRENT.md`
- `docs/agent_handoff/history/CURRENT_pre_wp_rel_01.md`

## Pending / unverified

- Run the fresh local Windows candidate build and verify packaged migration/manifest metadata.
- Make a read-only inventory and copy backup of `%LOCALAPPDATA%\QI-Crawler`, then run clean-data and Team Bid-copy smoke tests only against isolated copies.
- Run the final targeted/full verification gates and record their exact results.
- Commit and push this bounded branch and create one Draft PR; PR/CI state remains live GitHub state and is not asserted here.

## Risks / blockers

- Build or smoke failure, multiple Alembic heads, missing packaged migration, unsafe data copy/isolation, unexpected deletion, or any need to touch production data is a STOP_FOR_REVIEW condition.
- Official publication, tag/release creation, and user-visible `Crawler tool\Current` replacement are explicitly outside Stage A.

## Explicitly NOT done

- No `Crawler tool\Current` publish.
- No Team Bid Reference official creation.
- No Git tag, GitHub Release, or installer release publication.
- No production DB mutation, downgrade, or stamp.
- No business-data, crawler, storage, MI, AI, or schema redesign.

## Verification evidence

- Pytest collection baseline before implementation: `452 tests collected`.
- Targeted release/installer tests after implementation: `11 passed` (full suite pending).
- CodeGraph status/sync/explore succeeded; `.codegraph/` remains local-only.
- Final Ruff, full pytest, diff-check, build, and isolated-copy smoke evidence are pending at this handoff point.

## Next objective

Complete Stage A verification only. After independent audit, human merge decision, and a clean merged main, a later approved stage may consider official release actions. Do not start Stage B from this handoff.

## Locked decisions

- Keep application version `0.8.0` for this approved Stage A.
- Preserve existing GUI version display and Alembic history.
- Do not publish or mutate production/user data during candidate verification.

## Tool state

- CodeGraph: available, up to date, and used for release/build/GUI/migration impact exploration.
- Commit/push: not yet performed for this Stage A working tree.
