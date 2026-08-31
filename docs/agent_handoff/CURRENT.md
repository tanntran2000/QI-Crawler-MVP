# QI-Crawler Agent Handoff

## Active machine-readable checkpoint

```text
HANDOFF_ID = WP-TB-BASIC-CRAWLER-03 / PARENT-PRE
HANDOFF_CAPTURE_BASE = 54a0c53fdb5d38e208c4fd66d126b20e971f00f5
ROADMAP_REVISION = 1.3
ROADMAP_BASELINE_SHA = 38d94877f67818a8ddbc33e7e6b0b05e1f9f59a6
AUDIT_TARGET_CODE_HEAD = N/A_DOCS_ONLY
LAST_AUDITED_CODE_HEAD = N/A_DOCS_ONLY
LAST_AUDITED_DOC_HEAD = 54a0c53fdb5d38e208c4fd66d126b20e971f00f5
LIVE_GIT_HEAD = REVERIFY_FROM_GIT_AT_READ_IN
LIVE_MAIN_HEAD = 54a0c53fdb5d38e208c4fd66d126b20e971f00f5
CANONICAL_CHECKOUT = D:\QI Technology\QI Crawler\egp-crawler-python
ACTIVE_PARENT_WP = WP-TB-BASIC-CRAWLER-03
ACTIVE_MICRO_WP = NONE_PARENT_PRE
ACTIVE_BRANCH = tb/basic-crawler-03-revision-intake
PARENT_BASE = 54a0c53fdb5d38e208c4fd66d126b20e971f00f5
PRODUCT_FRONTIER = Unified Tender Warehouse
PRIMARY_DELTA = RD-0010
SUPPORTING_DELTA = RD-0001
SEQUENCING_DELTA = RD-0004
PARENT_STATE = PREPARED_PENDING_INDEPENDENT_AUDIT
DESIGN_APPROVAL = HUMAN_A0_APPROVED
CURRENT_VERIFIED_PRODUCT_GAP = REAL_REVISION_TRANSITION_AND_HUMAN_CONTROLLED_FOLDER_INTAKE
MICRO_A = NOT_STARTED_PENDING_PRE_AUDIT
MICRO_B = CONDITIONAL_NOT_AUTHORIZED
MICRO_C = NOT_STARTED
START_PRODUCT_IMPLEMENTATION = NO_PENDING_PRE_AUDIT
RD_0008 = PARKED_NOT_AUTHORIZED
RD_0009 = PARKED_NOT_AUTHORIZED
DEEP_HSMT = NOT_AUTHORIZED
API_EVOLUTION = HOLD
MEM_024 = FORWARD_RECONCILED
FB_0030 = ACCEPTED_ROUTED_TO_RD_0010_AND_PARENT_03_DESIGN
FM_009 = FORWARD_RECONCILED
MASTER_ROADMAP_ALIGNMENT = ALIGNED
PRODUCT_HOUSE_ALIGNMENT = PASS
ROADMAP_CONFLICT = NO
SPINE_SYNC_STATE = PENDING_INDEPENDENT_PRE_AUDIT
PROJECT_MEMORY_WRITE = YES_MEM_024_FORWARD_RECONCILIATION
FEEDBACK_WRITE = YES_FB_0030
FAILURE_MEMORY_WRITE = YES_FM_009_RECONCILIATION
MASTER_ROADMAP_WRITE = NO
LESSONS_WRITE = NO
HOSTED_CI_STATE = PASS_EXACT_MAIN_BASELINE
CI_PASS_CLAIMED = YES_FOR_MAIN_BASELINE_ONLY
PENDING_RETRO_CI = YES
RELEASE = NO
TEAM_BID_PILOT_ALLOWED = NO
PUSH = NO
PR = NO
MERGE = NO
SPINE_TARGET_FILES = docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent/PROJECT_MEMORY.md; docs/agent/FEEDBACK_LEDGER.md; docs/agent/KNOWN_FAILURE_MODES.md; docs/agent_handoff/CURRENT.md; docs/agent_handoff/history/CURRENT_parent_pre_wp_tb_basic_crawler_03.md; docs/superpowers/specs/2026-08-31-basic-crawler-03-design.md
EXACTLY_ONE_NEXT_ACTION = INDEPENDENT_PARENT_PRE_AUDIT
NEXT_STATE = INDEPENDENT_PARENT_PRE_AUDIT
NEXT_AUTHORITY = REVIEWER_AUDITOR
HANDOFF_READY = YES_FOR_INDEPENDENT_PARENT_PRE_AUDIT
```

## Parent PRE state

WP-TB-BASIC-CRAWLER-03 is a Human-approved design and parent-PRE entry for
real revision transition and controlled folder intake. No Parent-03 product
implementation has started. The exact main baseline is
`54a0c53fdb5d38e208c4fd66d126b20e971f00f5`; this branch contains only the
bounded Spine reconciliation, feedback/failure-memory updates, handoff and
design specification.

The durable Parent-02 facts remain in MEM-024: PR #82 merged from audited head
`03056fe147c3263cf8fb2ea39e63dc239e35fffe` at
`54a0c53fdb5d38e208c4fd66d126b20e971f00f5`, with post-merge Python CI
`33384009634` and CodeQL `33384009691` passing. FM-009 records the historical
25→35-minute evidence and the bounded 35→45 correction; another 45-minute
breach requires renewed attribution and HOLD.

Parent-03 design authority is explicit: source revision is the CĐT/e-GP
published package revision, the crawler never invents it, newer accepted
revisions advance without downgrade, and mismatches hold for Team Bid
confirmation. Folder scanning is read-only and one-shot with manual rescan;
discovered files require Human confirmation before Warehouse membership.
Package identity, membership and business authority remain in the governed
domain/backend/persistence layers, not filenames or folders.

RD-0008 and RD-0009 remain parked and no implementation, release or Team Bid
pilot is authorized. The exactly-one next action is
`INDEPENDENT_PARENT_PRE_AUDIT` under `REVIEWER_AUDITOR` authority.
`CURRENT.md` is an actionable handoff, not a diary, roadmap, review report or
chat transcript.
