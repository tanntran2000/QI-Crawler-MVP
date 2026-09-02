# QI-Crawler Agent Handoff

## Active machine-readable checkpoint

```text
HANDOFF_ID = WP-CI-FM009-RUNTIME-ATTRIBUTION-01 / PRE-MERGE CLOSEOUT
HANDOFF_CAPTURE_BASE = 5732684ec5959093854bd29ae8ce1c52024b8a5b
ROADMAP_REVISION = 1.3
LIVE_GIT_HEAD = REVERIFY_FROM_GIT_AT_READ_IN
LIVE_MAIN_HEAD = 73727897a9c60c21aa8874ca21057ed6992b3390
CANONICAL_CHECKOUT = D:\QI Technology\QI Crawler\egp-crawler-python
ACTIVE_PRODUCT_WP = NONE
ACTIVE_ENGINEERING_WP = WP-CI-FM009-RUNTIME-ATTRIBUTION-01
PR = 85 / OPEN_DRAFT
BASE_MAIN = 73727897a9c60c21aa8874ca21057ed6992b3390
AUDITED_CODE_HEAD = 5732684ec5959093854bd29ae8ce1c52024b8a5b
MICRO_A = AUDITED_PASS
MICRO_B = AUDITED_PASS
WINDOWS_ROBUSTNESS = 3_OF_3_PASS
WINDOWS_RUNTIME_RANGE = 6m30s_TO_8m07s_JOB
WINDOWS_TEST_COUNT = 787_EACH
FM_009 = AUDITED_RESOLVED_PENDING_MERGE
FM_008 = OPEN_TEST_DEBT
PRODUCT_REGRESSION = NONE_OBSERVED
TIMEOUT_CHANGE = NO
CURRENT_WINDOWS_CEILING = 45_MINUTES
RELEASE = NO
TEAM_BID_PILOT = NO
RELEASE_PREP = PARKED_UNTIL_THIS_WP_MERGED_AND_POSTMERGE_VERIFIED
PENDING_RETRO_CI = YES_UNTIL_POST_MERGE_VERIFICATION
NEXT_WP_AUTHORIZED = NO
EXACTLY_ONE_NEXT_ACTION = STOP_FOR_INDEPENDENT_CLOSEOUT_AUDIT
NEXT_AUTHORITY = PLANNER_ARCHITECT
FAILURE_MEMORY_WRITE = FM008_FM009_RECONCILED
MASTER_ROADMAP_DELTA_WRITE = RD0003_RECONCILED
PROJECT_MEMORY_WRITE = NO_CHANGE_REQUIRED
MASTER_ROADMAP_WRITE = NO_CHANGE_REQUIRED
CHANGELOG_WRITE = NO_CHANGE_REQUIRED_TEST_INFRA_ONLY
LESSONS_WRITE = NO_CHANGE_REQUIRED_LESSON11_SUFFICIENT
FEEDBACK_WRITE = NO_CHANGE_REQUIRED
SPINE_SYNC_STATE = PASS
HANDOFF_READY = YES_FOR_INDEPENDENT_CLOSEOUT_AUDIT
```

## Pre-merge closeout disposition

Micro-A and Micro-B are independently audited PASS at code head
`5732684ec5959093854bd29ae8ce1c52024b8a5b`. Three same-head Windows
robustness samples (run `33581232930`) each completed 787 tests below the
35-minute watch threshold: 8m07 in `northcentralus`, 6m47 in `eastus`, and
6m30 in `westcentralus`. The measured pytest runtimes were 413.62s, 336.21s,
and 322.40s respectively; no assertion or product failure was observed.

FM-009 is therefore `AUDITED_RESOLVED_PENDING_MERGE`. The primary runtime
driver was repeated full Alembic execution through the autouse
`Database.require_current_schema` test shim; hosted-runner variance remains a
secondary observed factor and is not claimed to be zero. The 45-minute hard
ceiling remains unchanged, and any future breach requires renewed attribution
before considering a budget change. FM-008 remains OPEN test-debt for the
legacy `Database.create_all` compatibility seam; it is not closed by the
FM-009 correction.

PR #85 remains OPEN and Draft against `main`. No merge, release, Team Bid
pilot, or product implementation is authorized by this handoff. The next
governed action is an independent closeout audit of this docs transition.
