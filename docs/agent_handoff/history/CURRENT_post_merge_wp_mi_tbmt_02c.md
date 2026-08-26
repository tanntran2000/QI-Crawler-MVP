# HISTORICAL / NON-NORMATIVE / MAY CONTAIN SUPERSEDED RULES

# WP-MI-TBMT-02C — POST-MERGE MAIN-TRUTH SNAPSHOT

This snapshot records the governed state captured after PR #60 merged the
Opportunity Intelligence delivery-closure Parent. It is historical evidence,
not live Git/GitHub authority.

```text
PARENT_WP = WP-MI-TBMT-02C
PR = 60
MERGE_COMMIT = 82013b0bc1a4b3a62a12567d3d4cc02974f93ec9
MERGED_FEATURE_HEAD = d5fecd3cc95e55f825e83e75321a3182da633384
LAST_AUDITED_CODE_HEAD = 513becf3fc9a24d9ff8d26df37fee320486fd0de
LAST_AUDITED_DOC_HEAD = 38d481f95ea9d2c9aa871d12def63b07d27e5aee
ACTIVE_PARENT_WP = NONE
ACTIVE_MICRO_WP = NONE
ACTIVE_BRANCH = main
PARENT_STATE = MERGED_MAIN_TRUTH
02C = MERGED
PARENT_INTEGRATION_BLOCKERS = NONE
PRODUCT_FRONTIER = Unified Tender Warehouse
ALEMBIC_HEAD = 0015_add_opportunity_review_events
P0_BACKUP_MECHANISM = SQLITE_CONNECTION_BACKUP
P0_WAL_BACKUP = RESOLVED_LOCAL_AUDITED
FC2_DOMAIN_APPLICATION_BOUNDARY = RESOLVED_LOCAL_AUDITED
FC2_ARCHITECTURE_GUARD = RESOLVED_LOCAL_AUDITED
FULL_REPO_AUDIT_DIRECT_02B_BLOCKERS = NONE
LOCAL_FULL = 628 passed
LOCAL_TARGETED = 63 passed
COLLECTION = 628 / 0 errors
RUFF = PASS
PARENT_INDEPENDENT_AUDIT = PASS
SPINE_AUDIT = PASS
FM_007 = MERGED_RESOLVED_PENDING_RETRO_CI_ONLY
FULL_REPO_AUDIT = HOLD
OPEN_OUT_OF_SCOPE_FINDINGS = WINDOWS_PUBLISHER_SCHEMA_DRIFT; LEGACY_BID_AUTHORITY_QUARANTINE; API_LAYER_BYPASS; BID_RADAR_SOURCE_INTEGRITY_BACKEND_ENFORCEMENT; TEST_CREATE_ALL_SHIM
PR_CI_RUN = 32869607389
PR_CI_EXECUTION = PRE_EXECUTION_FAILURE
MAIN_POST_MERGE_CI_RUN = 32870547007
MAIN_POST_MERGE_CI_EXECUTION = PRE_EXECUTION_FAILURE
CI_WAIVER = ACTIVE
HOSTED_CI_STATE = INFRASTRUCTURE_UNAVAILABLE
CI_PASS_CLAIMED = NO
PENDING_RETRO_CI = YES
PRODUCT_CI_FAILURE = NOT_ESTABLISHED
OFFICIAL_TEAM_BID_RELEASE = BLOCKED_PENDING_RETRO_CI
PUSH = NO
PR_STATE = MERGED_60
MERGE_STATE = MERGED_MAIN
NEXT_PARENT_OR_MICRO_WP = FULL_LOCAL_BUG_AUDIT
NEXT_STATE = FULL_LOCAL_BUG_AUDIT
NEXT_AUTHORITY = PLANNER_ARCHITECT
```

The merged capability is the bounded KHMT/TBMT source-neutral workflow:
intake, PL/IB preservation, tri-state filtering/search, explicit Human Review,
review persistence and revision isolation, confirmed XLSX, backend SHA
fail-closed export integrity, thin existing Bid Radar GUI wiring and vertical
KHMT/TBMT acceptance. KHMT Legal DOCX compatibility remains supported; TBMT
Legal DOCX remains explicitly unsupported; API integration remains on HOLD.

The P0 WAL-safe pre-migration backup uses `sqlite3.Connection.backup()` to
create a coherent snapshot; partial output is removed and errors propagate
fail-closed. FM-007 is merged/resolved, while the full-repository audit remains
HOLD for the listed out-of-scope findings.

Hosted CI runs `32865755230` (attempts 1/2/3), `32869607389` and
`32870547007` had no runner allocation and no workflow steps executed. No CI
PASS is claimed; the waiver and retro-CI debt remain active.

This snapshot records no production-data access, release publication, CI
rerun, push, or PR creation. The next governed action is a fresh full local
bug audit/test sweep that finds evidence and root cause before any correction.
