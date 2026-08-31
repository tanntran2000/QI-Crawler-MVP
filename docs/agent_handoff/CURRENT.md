# QI-Crawler Agent Handoff

## Active machine-readable checkpoint

```text
HANDOFF_ID = WP-TB-BASIC-CRAWLER-02 / PARENT_PRE
HANDOFF_CAPTURE_BASE = 2826f8c6735fcf68f405a01386d6ab4e63476e57
ROADMAP_REVISION = 1.3
ROADMAP_BASELINE_SHA = 38d94877f67818a8ddbc33e7e6b0b05e1f9f59a6
AUDIT_TARGET_CODE_HEAD = N/A_DOCS_ONLY
LAST_AUDITED_CODE_HEAD = N/A_DOCS_ONLY
LAST_AUDITED_DOC_HEAD = 41b7a1056b9bb2d69922a60282bba9846e7e2128
LIVE_GIT_HEAD = REVERIFY_FROM_GIT_AT_READ_IN
LIVE_MAIN_HEAD = 2826f8c6735fcf68f405a01386d6ab4e63476e57
ACTIVE_PARENT_WP = WP-TB-BASIC-CRAWLER-02
ACTIVE_MICRO_WP = PRE_ENTRY
ACTIVE_BRANCH = tb/basic-crawler-02-operational-closure
PARENT_STATE = PRE_ENTRY_PENDING_INDEPENDENT_REVIEW
CANONICAL_CHECKOUT = D:\QI Technology\QI Crawler\egp-crawler-python
FORMER_C_CHECKOUT = PHYSICALLY_REMOVED
GOV_BOOT_D0 = PASS
GOV_BOOT_D1 = PASS
RETROSPECTIVE_RESULT = REMOTE_IMPLEMENTATION_PRESERVED_LOCAL_PROVENANCE_REVALIDATED
PARENT_BASE = 2826f8c6735fcf68f405a01386d6ab4e63476e57
PRODUCT_FRONTIER = Unified Tender Warehouse
PRIMARY_DELTA = RD-0010
NEXT_PRODUCT_RETURN_DIRECTION = WP-TB-BASIC-CRAWLER-02
GOVERNANCE_CANONICAL_FILE = docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md
PRODUCT_CODE_CHANGED = NO
GOV_PARENT_81 = MERGED_VERIFIED
GOV_PARENT_81_MERGE = 2826f8c6735fcf68f405a01386d6ab4e63476e57
POST_MERGE_CODEQL = PASS
POST_MERGE_PYTHON_CI = PASS
MICRO_A = NOT_STARTED
FB_0028_IMPLEMENTATION = MERGED_DURABLE_GOVERNANCE
FB_0029_PROMOTION = MERGED_DURABLE_GOVERNANCE
FB_0024_CORRECTION = FORWARD_CORRECTED_MERGED
FM_010_RECLASSIFICATION = MERGED_RESOLVED
RD_0008 = PARKED
RD_0009 = PARKED
DEEP_HSMT = NO
API_EVOLUTION = HOLD
DELTA_WRITE = NO
MASTER_ROADMAP_WRITE = NO
PROJECT_MEMORY_WRITE = NO_PRE_MERGE
FEEDBACK_WRITE = NO_PRE_MERGE
FAILURE_MEMORY_WRITE = NO
LESSONS_WRITE = NO
RELEASE = NO
TEAM_BID_PILOT_ALLOWED = NO
PUSH = NO
PR = NO
MERGE = NO
HOSTED_CI_STATE = PASS_EXACT_MAIN
CI_PASS_CLAIMED = YES
PENDING_RETRO_CI = YES
ROLE_BOOT_SOURCE = CANONICAL_ROLE_BOOT_AND_PROMPT_PROFILES
ROLE_CONTRACT_SOURCE = docs/agent/OPERATING_MODEL.md
MASTER_ROADMAP_ALIGNMENT = ALIGNED_BY_GOVERNANCE_REFINEMENT
ROADMAP_CONFLICT = NO
RELEVANT_DELTA_IDS = RD-0010; RD-0004; RD-0001; RD-0008; RD-0009
SPINE_IMPACT = POST_MERGE_SPINE + PARENT_PRE
SPINE_TARGET_FILES = docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent/PROJECT_MEMORY.md; docs/agent/FEEDBACK_LEDGER.md; docs/agent/KNOWN_FAILURE_MODES.md; docs/agent_handoff/CURRENT.md; docs/agent_handoff/history/CURRENT_parent_pre_wp_tb_basic_crawler_02.md
SPINE_SYNC_STATE = PASS
EXACTLY_ONE_NEXT_ACTION = INDEPENDENT_PARENT_PRE_AUDIT
NEXT_AUTHORITY = REVIEWER_AUDITOR
HANDOFF_READY = YES_FOR_INDEPENDENT_PARENT_PRE_AUDIT
```

## Implementation state

The Role-Boot / Prompt-Continuity Parent is merged and verified in PR #81.
`docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md` is the single detailed source
for universal role boot, Planner/Builder/Reviewer profiles, three-pole mutual
challenge, Action-First prompts, Delta cadence, Roadmap comparison, prompt
quality and hold/escalation packets. `ROLE_CONTRACT` remains canonical in the
Operating Model; Human A0 remains the top material authority and the Machine
Verifier remains evidence-only.

The supporting governance documents contain bounded references rather than a
second copy of the contract. The Roadmap and Delta were read and remain
aligned; RD-0010 now routes to the approved WP-TB-BASIC-CRAWLER-02 Parent PRE.
MEM-023 records the merged governance truth. The canonical checkout is the D:
path above; the former C checkout was physically removed. FB-0024's generic
identity gate remains valid while its checkout-location interpretation was
forward-corrected by FB-0029, and FM-010 is merged/resolved by that correction.
No product code, tests, database, release or Team Bid pilot was changed or
authorized.

This handoff is the Parent PRE snapshot for WP-TB-BASIC-CRAWLER-02. It does
not authorize product implementation and does not claim the Parent PRE audit
has passed. The next governed action is exactly
`INDEPENDENT_PARENT_PRE_AUDIT` under `REVIEWER_AUDITOR` authority.
