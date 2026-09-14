# Path registry rollout and local address guide

## Decision and scope

Human intent (2026-09-14): make each WP traceable to its folders, constrain
new code/artifacts to purposeful fixed addresses, prohibit fictional WPs and
outputs, audit leftovers and prevent recurring storage growth.

Adopt Planner's contract + registry + gate design, with four additions:
reverse WP lookup; explicit existence states; per-run capacity accounting;
dependency-aware post-WP disposition. Keep stable logical names while resolving
actual physical roots. Do not create a second idea/roadmap registry.

This change authors governance only, under the direct Human request. It is
not a continuation of the earlier R2 independent audit or a self-issued
independent PASS. The live AO-04-C3 handoff and its writer are not reassigned.
No source/test changes, runtime migration, deletion, commit, push or release.
Release impact: governance/docs only; no application version bump.

## Immediate navigation on this host

`ROOT.REPO` was verified as
`D:\QI Technology\QI Crawler\egp-crawler-python` on branch
`release/v0.10-recon-01`, HEAD
`e7dea5c6e07662e963401f795da0cff623be832c` during read-in. These are snapshot
facts, not persistent baseline authority for later tasks.

| Purpose | Address on this host / resolution |
| --- | --- |
| Product code | `D:\QI Technology\QI Crawler\egp-crawler-python\src\qi_crawler\` |
| Reusable tests | `D:\QI Technology\QI Crawler\egp-crawler-python\tests\` |
| Governance/map | `D:\QI Technology\QI Crawler\egp-crawler-python\docs\agent\` |
| New test scratch | `D:\QI Technology\QI Crawler\egp-crawler-python\.tmp\{wp_id}\{run_id}\` |
| Retained run evidence | `D:\QI Technology\QI Crawler\egp-crawler-python\release_staging\evidence\{wp_id}-{run_id}\` |
| Approved sandbox | `D:\QI Technology\QI Crawler\egp-crawler-python\release_staging\sandbox\{wp_id}-{run_id}\` |
| Build intermediate / distributable | Repo `build\` / `dist\`; serialize use and name exact outputs in WP. |
| Standalone user data | `QI_CRAWLER_DATA_DIR` override, otherwise `%LOCALAPPDATA%\QI-Crawler`; read resolver/config first. |
| Standalone database | `{standalone_user_root}\data\database\egp.db` |
| Source-run database default | `{verified_cwd}\data\egp.db`, subject to explicit config; never confuse with standalone. |
| External imports/exports | Exact user-selected path; ownership remains external. |

Run IDs use the existing evidence convention `YYYYMMDDTHHMMSSZ`; a fractional
suffix is allowed only for a collision requirement recorded in the Work Order.
Names with braces are templates, not existing directories. This is an initial
address map, not a full byte census of C: and D: or a promise that all legacy
WPs have been indexed. Unmapped historical paths are KEEP until attributed.

## Rollout sequence and exit criteria

| Stage | Work | Evidence required to exit |
| --- | --- | --- |
| A — Foundation (this change) | Contract, initial registry, LAW 16, boot/roadmap entry links and captured Human intent. | Parse/unique IDs/reference/containment checks; scoped diff; independent review remains separate. |
| B — Read-only inventory | Census repo plus explicitly selected crawler-owned C:/D: locations; map each existing WP to outputs, ownership and references; backfill legacy rows. | Coverage denominator, inaccessible paths, bytes/files, protected dependencies, top consumers; no inferred deletion. |
| C — Agent/machine enforcement | Extend existing Workbench/Task Envelope and launchers; validate schema, WP bindings, actual write destinations, finite storage budgets; keep one registry. | Negative cases for unknown/duplicate IDs, case aliases, traversal/junction escape, missing owner, unregistered writes and stale lineage; exercise real Windows producer paths. |
| D — Bounded storage relief | Delete only audited, authorized exact transient targets; dedup only proven reconstructible payloads with preserved dependencies. | Before/after manifest, actual reclaimed bytes, protected SHA stability, recovery/reference checks and cleanup receipt. |
| E — Recurrence prevention | Require PRE/RUN/POST accounting on every new WP; use existing governed transitions to review deferred leftovers. | No unowned new artifacts; every retained artifact has purpose, owner and next review condition; measured growth stays within WP budget. |

These stages are a design sequence, not five new authorized WPs. The proposed
`WP-GOV-PATH-REGISTRY-01` name from Planner is not activated by this document.
Planner should first reconcile the live A3/Storage Relief boundary, then place
the remaining work in one bounded existing/new authorized unit as appropriate.
No recurring automation or CI program is installed by this plan.

## Inventory and enforcement design constraints

- Start from the highest byte consumers; do not rename folders for cosmetic
  uniformity. Identify references before classifying duplicate runtimes.
- Attribute `.tmp*`, `tmp`, `output`, `prep_data`, pytest and tool caches,
  `.venv`, `.git`, release artifacts and external tooling separately.
- Include `C:\t\b2migration` and `D:\QI Technology\Temp` as Human-reported
  leads, not verified disposable targets. Never sweep entire C:/D: roots.
- Do not copy large trees just to inventory/audit them. Stream metadata/hashes
  where needed, bound report size, and reuse an existing evidence packet.
- Small permanent registry entries describe families; a run inventory describes
  instances. Avoid millions of registry rows or duplicate report files.
- Source/test freeze evidence must cover the execution object whose test result
  is being reused; a stable Git status cannot fingerprint untracked test bytes.
- Static source scanning cannot prove absence of dynamic writes. Pair targeted
  static checks with representative producer tests; report actual coverage.
- Policy stability comes from stable IDs, roots and lifecycle profiles. Expand
  the map additively; avoid recurring whole-repo relocation/refactoring.

## Authoring scope and artifact inventory

```text
AUTHORITY = DIRECT_HUMAN_GOVERNANCE_REQUEST_2026_09_14
ROLE_FOR_THIS_DELIVERABLE = GOVERNANCE_AUTHOR; NOT_INDEPENDENT_REVIEWER
PATH_REGISTRY_IMPACT = ADD_ENTRY / INITIAL_CATALOG
PATH_IDS_USED = PATH.GOV.DOCUMENT; PATH.REPO.ROOT_HELPERS
NEW_ARTIFACTS =
  ART.GOV.PATH_POLICY → docs/agent/PATH_REGISTRY_CONTRACT.md
  ART.GOV.PATH_MAP → docs/agent/PATH_REGISTRY.yaml
  ART.GOV.PATH_ROLLOUT → docs/agent/PATH_REGISTRY_ROLLOUT.md
EXISTING_DOCUMENT_EDITS =
  AGENTS.md; docs/agent/MEMORY_INDEX.md;
  docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md;
  docs/agent/MASTER_ROADMAP.md; docs/agent/FEEDBACK_LEDGER.md
DISPOSITION = KEEP_PRODUCT for the catalog; KEEP_EVIDENCE/GOVERNANCE for docs
CONSUMERS = Planner, authorized Builder and independent Reviewer
NEW_FILE_BUDGET = 3 files / 65536 bytes total
HEAVY_EXECUTION = NONE; no temp tree or runtime copy
CLEANUP = NOT_NEEDED; no transient file created by this authoring task
INDEPENDENT_REVIEW = PENDING; no self-issued PASS
SPINE_IMPACT = GOVERNANCE; FEEDBACK; ROADMAP_NAVIGATION
PROJECT_MEMORY_PROMOTION = NONE; not a merged product fact
CURRENT_WRITE = NONE; active A3 handoff remains its owner's responsibility
```

The initial registration is part of the same directly authorized governance
creation, not a requirement for a pre-existing catalog before bootstrapping it.
Subsequent tasks must capture its fresh revision/SHA before writing. The three
new files are intended durable deliverables, not disposable authoring scratch.

## Verification boundary

CodeGraph was invoked for runtime-root discovery; its responses did not locate
the resolver precisely, so source fallback inspected `standalone.py` and
`config.py`. Impact radius: runtime/config paths and governance entry points.
Edit radius: governance Markdown and the catalog only. Validation radius:
catalog structure/references, documented paths and scoped diffs. No claim of
runtime enforcement, full filesystem inventory or storage reclaimed.

Next authority: Planner reconciles this local governance change and arranges
independent review before normal integration and implementation of stages B–D.

Local author verification (2026-09-14): catalog parses; duplicate keys/IDs and
ambiguous exact templates are rejected (external READ/WRITE is explicit);
all root/profile/PATH_ID references, Roadmap anchors, selected historical
locators and observed legacy locations resolve. There are 43 path families
and 15 legacy/inventory leads. Three new durable files total less than the
65,536-byte authoring cap. These checks are structural validation, not a
runtime security test or independent governance audit. No pytest/build run.
