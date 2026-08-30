# QI-Crawler Agent Handoff

## Active machine-readable checkpoint

```text
HANDOFF_ID = WP-GOV-ROLE-BOOT-PROMPT-CONTINUITY-01 / PRE
HANDOFF_CAPTURE_BASE = 0482af7b48291f488aee5820b29a10ce8dde883b
ROADMAP_REVISION = 1.3
ROADMAP_BASELINE_SHA = 38d94877f67818a8ddbc33e7e6b0b05e1f9f59a6
ACTIVE_PARENT_WP = WP-GOV-ROLE-BOOT-PROMPT-CONTINUITY-01
ACTIVE_MICRO_WP = NONE
ACTIVE_BRANCH = gov/role-boot-prompt-continuity-01
PARENT_STATE = AUTHORIZED_ACTIVE
PARENT_BASE = 0482af7b48291f488aee5820b29a10ce8dde883b
PRODUCT_FRONTIER = Unified Tender Warehouse
NEXT_PRODUCT_RETURN_DIRECTION = TEAM_BID_BASIC_CRAWLER
OBJECTIVE = ROLE_BOOT_PROMPT_CONTINUITY_AND_THREE_POLE_MUTUAL_CHALLENGE
LATEST_GOVERNED_UNIT = WP-TB-BASIC-CRAWLER-01 / TERMINAL_CLOSED
LATEST_MERGED_HEAD = 0482af7b48291f488aee5820b29a10ce8dde883b
LIVE_MAIN_HEAD = REVERIFY_FROM_GIT_AT_READ_IN
RELEVANT_DELTA_IDS = RD-0010; RD-0004; RD-0001; RD-0008; RD-0009
DELTA_STATE = PASS
SPINE_FRESHNESS = PASS
CURRENT_FRESHNESS = PASS_SELF_REFERENTIAL_RECONCILIATION
ROLE_AUTHORITY_DRIFT = NO
NEXT_ALIGNMENT = PASS
LATEST_WP_SPINE_SYNC_AUDIT = PASS
RELEASE = NO
TEAM_BID_PILOT_ALLOWED = NO_PENDING_HUMAN_DECISION
HOSTED_CI_STATE = PASS_EXACT_MERGE_HEAD
CI_PASS_CLAIMED = YES_FOR_MERGED_HEAD_ONLY
PENDING_RETRO_CI = YES
NEXT_STATE = BUILDER_EXECUTION
EXACTLY_ONE_NEXT_ACTION = BUILDER_EXECUTE_AUTHORIZED_GOVERNANCE_PARENT
NEXT_AUTHORITY = BUILDER_SINGLE_WRITER
HANDOFF_READY = YES_FOR_BUILDER_EXECUTION
```

## Parent PRE authority

Human A0 approved Option B: promote FB-0028's role-boot, action-first prompt
and three-pole mutual-challenge design into one canonical governance contract.
This Parent changes governance orientation and continuity only; it does not
authorize product implementation, a new crawler WP, release, Team Bid pilot,
or premature promotion of FB-0028 into merged Project Memory.

The latest governed product unit is WP-TB-BASIC-CRAWLER-01, now terminally
closed at live main `0482af7b48291f488aee5820b29a10ce8dde883b`. Existing
release safety, retro-CI debt, and historical PR evidence remain in the
canonical history; volatile Git/GitHub state must be re-resolved at read-in.

The Master Roadmap remains authoritative and unchanged. Its high-level
Planning & Audit Pole is interpreted as a family containing independent
Planner and Reviewer poles. The Delta remains aligned, with RD-0010 and the
related Warehouse dependency nodes as the relevant context. `CHECK DELTA OFTEN
!= WRITE DELTA OFTEN` remains in force.

## Entry rule

Before the next governed transition, resolve the canonical checkout, live Git
and GitHub state, applicable Roadmap/Delta and Context Spine authorities, then
the role and prompt gates. Material conflict is a hold and escalation, not a
guess.
