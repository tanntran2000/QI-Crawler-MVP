# QI-Crawler Agent Handoff

## HANDOFF_ID

POST — WP-GOV-BLUEPRINT-KVS-HANDOFF-01 / QI-KVS BLUEPRINT + HANDOFF GOVERNANCE

## Status

WP-GOV-BLUEPRINT-KVS-HANDOFF-01 IMPLEMENTED / PENDING INDEPENDENT DOC AUDIT /
GOVERNANCE DOCS ONLY / NO PRODUCT BEHAVIOR CHANGE / NOT MERGED

## Active machine-readable checkpoint

```text
ACTIVE_PARENT_WP = WP-GOV-BLUEPRINT-KVS-HANDOFF-01
ACTIVE_MICRO_WP = NONE
ACTIVE_BRANCH = gov/blueprint-kvs-handoff-01
PARENT_STATE = IMPLEMENTED_PENDING_INDEPENDENT_DOC_AUDIT
MAIN_BASE = c2439e545d56ec4d65c166e5df6e9430cd824311
PRE_HEAD = 341aa917081f20864096e67f3c6c1d8cfb736906
IMPLEMENTATION_HEAD = 44f0a12ac150764d36f33f6f76dac17ed53bf33e
LAST_MERGED_PARENT_WP = WP-GOV-FAILURE-MEMORY-01
LAST_MERGED_PR = 57
LAST_MERGE_COMMIT = c2439e545d56ec4d65c166e5df6e9430cd824311
PRODUCT_FRONTIER = Opportunity Intelligence
PARENT_OBJECTIVE = align QI-KVS blueprint, roadmap-read governance, documentation freshness and handoff integrity
ROADMAP_REVISION = 1.2
QI_KVS_BLUEPRINT = ADDED_TARGET_ARCHITECTURE
QI_KVS_IMPLEMENTATION = NOT_ACTIVE
ROADMAP_ENTRY_GATE = STRENGTHENED
POST_MERGE_HANDOFF_GATE = ADDED
HANDOFF_FRESHNESS = STRENGTHENED
OPPORTUNITY_ROADMAP_RECONCILIATION = 02B_MERGED_CAPABILITIES_RECORDED
ROADMAP_IMPACT = MATERIAL_BLUEPRINT_UPDATE
PRODUCTION_CODE_CHANGE = NO
CI_WORKFLOW_CHANGE = NO
RELEASE_IMPACT = NO
DOC_SYNC_STATE = IMPLEMENTATION_DOCS_UPDATED
PROVEN_COMPLETE = QI_KVS_BLUEPRINT_AND_HANDOFF_GOVERNANCE_DOCS
OPEN_BLOCKERS = NONE_WITHIN_SCOPE
SCOPE_BOUNDARIES = NO_KNOWLEDGE_RUNTIME_OR_PRODUCT_CODE
FULL_REPO_AUDIT = HOLD
PENDING_RETRO_CI = YES
HOSTED_CI_STATE = UNAVAILABLE_QUOTA
CI_PASS_CLAIMED = NO
OFFICIAL_TEAM_BID_RELEASE = BLOCKED
NEXT_PARENT_OR_MICRO_WP = WP-MI-TBMT-02C
NEXT_STATE = NOT_STARTED
NEXT_AUTHORITY = PLANNER_ARCHITECT
PUSH = NO
PR = NO
MERGE = NO
ACTIVE_DUPLICATE_KEYS = NONE
PROJECT_CONTEXT_MAP = docs/agent/MASTER_ROADMAP.md
ROADMAP_CONTEXT_REQUIRED = YES
EXACTLY_ONE_NEXT_ACTION = INDEPENDENT DOC AUDIT OF THIS GOVERNANCE WP
```

## Main truth after merge

- WP-MI-TBMT-02B / PR #55 was merged at
  `cbda73692dfe6b99c6a2045b2306b57e1e4136fb`.
- The merged feature head was
  `6513acfe7397467d1588fb3d404938ac04c8c00c`; the audited code head was
  `b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a`.
- Live `main` HEAD must be verified from Git/GitHub at handoff entry; this
  document records the verified merge ancestry but does not replace live Git
  authority.
- Runtime/package version remains `0.8.0`.
- Hosted CI remains unavailable because the recorded run failed before job
  execution; this is infrastructure evidence, not a product-test failure.
- `PENDING_RETRO_CI = YES`; no official Team Bid release is authorized while
  this debt remains open.

## Completed Parent WP — WP-MI-TBMT-02A

### 02A-1 — Source-neutral Opportunity identity/candidate contract

Introduced `OpportunitySourceType` (`KHMT`/`TBMT`), separate `PL`/`IB`
identity namespaces, source-backed identity/import-batch/candidate contracts,
raw/base/revision consistency, positive source-row and SHA checks, and
authoritative provenance consistency. `PL != IB`; no PL↔IB conversion.

### 02A-2 — TBMT schema + conservative IB parser/normalization

Implemented the observed TBMT schema and fail-closed revisioned IB parsing,
including the distinction between an identity revision delimiter and a title
delimiter. Ambiguous or extended identity-like tokens remain rejected.

### 02A-3 — TBMT workbook importer → OpportunityCandidate

Added bounded read-only `.xlsx` import with header scanning, SHA-256/sheet/time/
schema provenance, IB-only identity construction, complete raw-field retention,
conservative price parsing, issue reporting, and no silent source-row
deduplication. TBMT does not enter the KHMT `PlanPackage` path.

### 02A-4 — Real-file/read-only acceptance + Parent Integration Gate

The protected real workbook was read only. Acceptance recorded:

```text
source rows = 72
candidates = 72
issues = 0
SHA-256 = E4B8FF62D8FF979BD646287EB7C894B9F03D089691B9122A6A96847457A1CDB4
size = 120194 bytes
source bytes/size unchanged = YES
```

The final local regression evidence was 532 passed; latest collection after
the revision-domain contract was 534; Ruff and diff-check passed. This is
real-file/read-only acceptance, not a `Golden` label.

## CodeGraph evidence

Queries executed in the merged checkout:

```text
codegraph explore "Merged TBMT facts for OpportunityIdentity, OpportunityCandidate, import_tbmt_workbook, and parse_tbmt_notice_identity; confirm source-neutral TBMT importer, IB namespace, PL != IB, and provenance fields"
codegraph explore "import_tbmt_workbook"
codegraph explore "parse_tbmt_notice_identity"
codegraph explore "OpportunityIdentity"
```

The graph returned the relevant source/caller graph and confirmed the merged
source-neutral contract boundary: TBMT importer/normalization produces IB
opportunity identities with source provenance; it is distinct from KHMT
`PlanPackage` and does not authorize review/export/GUI behavior.

## Merged Parent — WP-MI-TBMT-02B

02B-1, 02B-2, and 02B-3 are merged. 02B-2 provides the source-neutral
filter/search projection and preserves legacy KHMT exclude-keyword compatibility
at its adapter boundary. 02B-3 provides the source-neutral review backend,
repository port, persistence adapter, and migration; export, GUI, and API
integration remain future work.

Hard invariant:

```text
IB...-00 Human Review does NOT automatically confirm IB...-01.
same base_id = same lineage, not same exact reviewed identity.
```

No automatic review inheritance is designed or authorized in this handoff.

## Data / release safety

- Do not access or mutate protected business data or `%LOCALAPPDATA%\QI-Crawler`.
- No production DB migration/downgrade/stamp/repair is authorized here.
- Version remains `0.8.0`; known-good release artifacts remain immutable.
- Retro-CI debt remains open.

## Delivery authority

This file is the active handoff snapshot, not an alternative source of live Git
or GitHub truth. Before designing or executing the next Work Package:

- fetch live Git/GitHub;
- resolve the live `main` HEAD;
- reconcile it with the recorded historical merge ancestry;
- do not treat `CURRENT.md` as live Git authority;
- reconcile the live state with this historical merge evidence;
- define the design scope and obtain explicit Human implementation approval.

## Next governed action

The only next candidate is `WP-MI-TBMT-02C — Opportunity Intelligence Delivery
Closure`, not started and awaiting Planner/Architect design. This governance
WP remains pending independent document audit; no implementation authorization
is implied.
