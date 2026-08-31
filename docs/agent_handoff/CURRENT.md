# QI-Crawler Agent Handoff

## Active machine-readable checkpoint

```text
HANDOFF_ID = WP-TB-BASIC-CRAWLER-03 / MICRO-A POST-SPINE
HANDOFF_CAPTURE_BASE = 818945f2d7f4dce6b3791c94ca6dfe8c5ebd96d2
ROADMAP_REVISION = 1.3
ROADMAP_BASELINE_SHA = 38d94877f67818a8ddbc33e7e6b0b05e1f9f59a6
AUDIT_TARGET_CODE_HEAD = 3c3b277a5828175f0a43148fb48aabcc0ac9d310
LAST_AUDITED_CODE_HEAD = 3c3b277a5828175f0a43148fb48aabcc0ac9d310
LAST_AUDITED_DOC_HEAD = 818945f2d7f4dce6b3791c94ca6dfe8c5ebd96d2
LIVE_GIT_HEAD = REVERIFY_FROM_GIT_AT_READ_IN
LIVE_MAIN_HEAD = 54a0c53fdb5d38e208c4fd66d126b20e971f00f5
CANONICAL_CHECKOUT = D:\QI Technology\QI Crawler\egp-crawler-python
ACTIVE_PARENT_WP = WP-TB-BASIC-CRAWLER-03
ACTIVE_MICRO_WP = MICRO-A_REAL_REVISION_ACCEPTANCE_AND_BLOCKER_DISCOVERY
ACTIVE_BRANCH = tb/basic-crawler-03-revision-intake
PARENT_BASE = 54a0c53fdb5d38e208c4fd66d126b20e971f00f5
PRODUCT_FRONTIER = Unified Tender Warehouse
PRIMARY_DELTA = RD-0010
SUPPORTING_DELTA = RD-0001
SEQUENCING_DELTA = RD-0004
PARENT_STATE = ACTIVE_MICRO_A_INDEPENDENT_AUDIT_PASS_PENDING_MICRO_B_AUTHORIZATION
DESIGN_APPROVAL = HUMAN_A0_APPROVED
MICRO_A = INDEPENDENT_AUDIT_PASS
MICRO_A_AUDITED_HEAD = 818945f2d7f4dce6b3791c94ca6dfe8c5ebd96d2
START_PRODUCT_IMPLEMENTATION = NO_MICRO_A_EVIDENCE_FIRST
MICRO_B = CONDITIONAL_NOT_AUTHORIZED
MICRO_B1 = CONTROLLED_FOLDER_INTAKE_AND_PACKAGE_SCOPED_NAMING
MICRO_B2 = OPERATIONAL_REVISION_TRANSITION_AND_ADJACENT_DIFF
MICRO_C = NOT_STARTED
RD_0008 = PARKED_NOT_AUTHORIZED
RD_0009 = PARKED_NOT_AUTHORIZED
DEEP_HSMT = NOT_AUTHORIZED
API_EVOLUTION = HOLD
REAL_LINEAGE = IB2600462391 / SINGLE_REVISION_ONLY
REAL_REVISIONS = IB2600462391-00 ONLY; NO SECOND REVISION FOUND
REAL_SOURCE_PROVENANCE = D:\QI Technology\QI Crawler\business-data\TBMT_19_8_2026.xlsx; sheet Bản tin điện tử; row 38; source-backed metadata only
FOLDER_DISCOVERY_BEHAVIOR = READ_ENUMERATION_THEN_AUTO_INTAKE_AND_MEMBERSHIP
FOLDER_DISCOVERY_REPRODUCTION = PASS_ISOLATED_TEMP_DB; 2 MEMBERSHIPS AND 2 WORKSPACE_ENTRIES BEFORE CONFIRMATION
HUMAN_CONFIRMATION_BOUNDARY = ABSENT
LATEST_OPERATIONAL_REVISION = ABSENT
NO_DOWNGRADE = ABSENT
REVISION_MISMATCH_HOLD = PARTIAL_SOURCE_REPLACEMENT_GUARD_ONLY
PREVIOUS_LATEST_COMPARE = ABSENT
OLD_REVISION_PRESERVATION = PROVEN_STRUCTURALLY_APPEND_ONLY_EXACT_RELEASES
DOCX_ROLE_AUTHORITY = PARTIAL
REFERENCE_AUTHORITY_SEPARATION = PARTIAL_EXPLICIT_REFERENCE_ONLY_GUARD
MANAGED_SHORT_NAMING = ABSENT
MATERIAL_BLOCKERS = BC03-B01; BC03-B02; BC03-B03; BC03-B04; BC03-B05
EVIDENCE_GAPS = REAL_MULTI_REVISION_EVIDENCE; LATEST_OPERATIONAL_REVISION; PREVIOUS_LATEST_COMPARE; DOCX_ROLE_AUTHORITY_REAL_EVIDENCE; MANAGED_SHORT_NAMING
ALREADY_PROVEN = EXACT_RELEASE_IDENTITY; OLD_REVISION_APPEND_ONLY_PRESERVATION; EXPLICIT_REFERENCE_ONLY_GUARD
PRODUCT_CODE_CHANGED = NO
TEST_CODE_CHANGED = NO
SCHEMA_CHANGED = NO
LIVE_DB_WRITE = NO
LIVE_TEAM_BID_DATA_MUTATION = NO
TARGETED_TESTS = tests/test_tender_workspace.py -q: 6 passed; workspace/case/persistence/bundle/intake suite: 55 passed
ISOLATED_RUNTIME_REPRODUCTION = PASS
RUFF = PASS
DIFF_CHECK = PASS
MASTER_ROADMAP_WRITE = NO
PROJECT_MEMORY_WRITE = NO_MICRO_A_NOT_MERGED
FEEDBACK_WRITE = NO
FAILURE_MEMORY_WRITE = NO
HOSTED_CI_STATE = NOT_RUN_MICRO_A_READ_ONLY
CI_PASS_CLAIMED = NO
PENDING_RETRO_CI = YES
RELEASE = NO
TEAM_BID_PILOT_ALLOWED = NO
PUSH = NO
PR = NO
MERGE = NO
SPINE_SYNC_STATE = PASS
EXACTLY_ONE_NEXT_ACTION = PLANNER_MICRO_B1_ENTRY_REVIEW
NEXT_STATE = PLANNER_MICRO_B1_ENTRY_REVIEW
NEXT_AUTHORITY = PLANNER_ARCHITECT
HANDOFF_READY = YES_FOR_PLANNER_MICRO_B1_ENTRY_REVIEW
```

## Micro-A evidence state

Micro-A has passed independent evidence review and is pending Planner
authorization for the bounded Micro-B1/Micro-B2 corrections. No Parent-03 product
implementation was started. The bounded local source search found one real
source-backed lineage, `IB2600462391-00`, in the existing workbook
`D:\QI Technology\QI Crawler\business-data\TBMT_19_8_2026.xlsx` (sheet
`Bản tin điện tử`, row 38); no second published revision for that base was
found in the approved local/project roots. This is an evidence gap, not a
fabricated revision or a product failure.

CodeGraph and source inspection show exact `(base_id, revision)` release
identity and append-only release records, with explicit `REFERENCE_ONLY`
classification guards. They do not establish a latest-operational revision,
no-downgrade gate, previous/latest comparison, or a package-scoped short
naming contract. DOCX role authority remains only partial without genuine
package evidence.

The material blockers are BC03-B01 through BC03-B05. BC03-B01 is
`AUTO_FOLDER_INTAKE_BYPASSES_HUMAN_CONFIRMATION`:
`TenderWorkspaceService.add_path_to_zone()` recursively enumerates supported
files and immediately calls intake, membership persistence and zone assignment.
An isolated temporary SQLite reproduction produced two memberships and two
workspace entries before any Human confirmation. Micro-A records this fact and
does not repair it; any fix requires a separately authorized Micro-B scope.

Existing targeted evidence is green: `tests/test_tender_workspace.py` passed
6 tests and the bounded workspace/case/persistence/bundle/intake suite passed
55 tests. Ruff and the documentation diff check pass. The exactly-one next
action is `PLANNER_MICRO_B1_ENTRY_REVIEW` under `PLANNER_ARCHITECT` authority.
This file is an actionable handoff, not a diary, roadmap, review report or chat
transcript.
