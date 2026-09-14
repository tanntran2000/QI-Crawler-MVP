# Canonical Path & Artifact Registry

Version: 1.0. Authority: direct Human request dated 2026-09-14 to establish
path, naming and artifact-lifecycle rules for future agents. This is a local
governance change awaiting independent review and normal integration; it is
not an independent audit verdict or a claim of deployment to other checkouts.

## 1. One map, explicit addresses

`PATH_REGISTRY.yaml` is the machine-readable address catalog. This contract
defines its meaning. Master Roadmap/Delta retain strategic authority;
Work Orders retain execution authority; CURRENT retains active handoff state.
The catalog does not duplicate those states or become another roadmap.

Every new governed write must resolve this chain before creation:

```text
ROADMAP heading or existing RD-ID
→ approved WP_ID and Work Order reference
→ ARTIFACT_ID (purpose, not business identity)
→ PATH_ID + template parameters
→ absolute resolved path + owner + lifecycle + storage budget
```

A PATH_ID registers a directory or file family, not every individual file.
Every produced file must still appear in the run inventory or a bounded
family inventory. Registering `src/` or `docs/` is not permission to create
arbitrary subtrees: the Work Order names exact modules/files and their purpose.
Do not create one source tree, clone or worktree per WP. Reuse capability-owned
modules; WP identity belongs in work/evidence metadata, not product filenames.

Before adding a file, identify its consumer and inspect the existing owner of
the behavior. Explain why extension/reuse is insufficient. No speculative
frameworks, duplicate helpers or placeholder modules solely for roadmap ideas.
Legitimate test doubles, fixtures and synthetic evidence are allowed only
when explicitly labeled, scoped and never represented as real acceptance.

## 2. Stable identities and honest existence

- PATH_ID: `PATH.<SPACE>.<PURPOSE>[.<SUBPURPOSE>]`, uppercase ASCII.
- ARTIFACT_ID: `ART.<CAPABILITY>.<PURPOSE>`; instances additionally use WP_ID,
  RunId and, where applicable, SHA256. This is not Document/Tender identity.
- Preserve approved WP IDs. Planner proposes new IDs inside an existing
  design/Delta record; only authorized WPs enter `wp_bindings`. A proposed
  name is not an active WP. Do not mint follow-on WPs to bypass a blocker.
- New run IDs: UTC `YYYYMMDDTHHMMSSZ`; append a six-digit fractional suffix
  only when the Work Order requires collision avoidance. Reject collisions and
  never overwrite an existing immutable run. Keep frozen historical names
  unchanged.
- Python filenames remain purpose-based `snake_case.py`; preserve existing
  tool/framework naming conventions and stable public entry points.
- For new owned generated runs, use the registered template, not `tmp2`,
  `final_final`, `backup_old`, personal names or unexplained numeric folders.
- A registry record uses `OBSERVED`, `RESERVED` or `LEGACY`; a planned path
  must not be claimed to exist. Never mkdir empty future roadmap scaffolding.
- Generated inventory states: `PLANNED`, `PRESENT_VERIFIED`, `MISSING`,
  `DELETED_VERIFIED`. A path string alone is never proof of output or success.

IDs are never recycled or silently renamed. Preserve history/aliases when a
purpose is retired. Bump registry revision for any entry change; incompatible
schema changes increment schema_version. Physical relocation is separately
designed, authorized, verified and reversible before old data is retired.

## 3. Roots and resolution

Fix logical IDs and relative templates. Record actual absolute paths per host
and run. Never treat the Windows drive letter as product architecture.
Runtime resolution comes from verified application configuration; the registry
does not change that code. Standalone defaults and source-run defaults differ.
An override must record its source and resolved value, with secrets excluded.

Resolve paths before use: normalize separators and Windows case, reject `..`,
absolute/template injection, reserved device names, alternate data streams,
trailing dots/spaces, and escapes through symlinks/junctions/reparse points.
Template `filename`, `wp_id` and `run_id` parameters are single path components;
`relative_path` and `module_path` are scoped relative paths, never unrestricted
write grants. `selected_path` is the explicit external-selection exception and
must equal the Human-authorized target. Validate containment on the resolved
target and all existing ancestors.
Reject ambiguous overlapping entries unless an explicit child entry owns the
path; use the most specific registered entry. External import/export may share
the selected-path template only with explicit `operation=READ` or `WRITE`;
the actual operation must match, and export may not overwrite an input without
separate explicit authority. Ancestor registration cannot
weaken child protection. Fail closed on unknown roots or unresolved templates.

Never manually clean `.git` object/history storage under a cache policy;
ordinary authorized Git operations retain their separate governance.
External inputs/exports are user-selected locations, not repo-owned scratch.
Record exact selection and authority; never recursively sweep an external
root. OS/tool-managed roots are inventory boundaries, not deletion grants.
New top-level roots, production locations, data ownership changes, migrations
and destructive retention changes require explicit Human material authority.

## 4. Catalog schema and reverse lookup

The YAML catalog uses JSON-compatible YAML (no executable tags or aliases).
Required top-level fields: schema_version, revision, enforcement, roots,
profiles, paths, roadmap_bindings, wp_bindings, legacy_locations.

Each path declares id, root_id, relative_template, purpose, profile, status,
producer and naming. A path may also declare `allowed_values` for a finite
filename set; a templated entry without that list still requires exact file
scope in the Work Order and is not a blanket write grant. The named profile
supplies owner, consumers, git_policy,
persistence, retention, cleanup_policy, sensitivity, backup/recovery and
creation/mutation/deletion authority. Profile fields apply to every entry;
they cannot be weakened implicitly. Entry-specific restrictions are additive.
`UNKNOWN` is a hold/keep condition, never a permission default.

Root records declare resolver and allowed_overrides. Snapshot examples are
informational and never replace fresh resolution. No credentials in the map.

`roadmap_bindings` references actual Master Roadmap headings and related RD IDs
plus PATH_IDs. `wp_bindings` is a locator-only index, with:

```text
wp_id, authority_ref, roadmap_ref, path_ids,
artifact_inventory_ref, scope_paths, relation
```

The index must not duplicate progress, audit verdicts or approval status from
CURRENT/Work Orders. The Work Order/run inventory supplies concrete resolved
paths. Shared modules may serve multiple WPs; do not copy them to make the
mapping one-to-one. When a path is unknown, report UNMAPPED; never invent a
location. Historical backfill is incremental and evidence-backed.

## 5. PRE / RUN / POST gates

Before the first write, every new Work Order or authorized governance edit
records the following in its existing packet (do not create a report per file):

```text
PATH_REGISTRY_BASELINE = revision + SHA256
PATH_REGISTRY_IMPACT = NONE | USE_EXISTING | ADD_ENTRY | CHANGE_ENTRY | MIGRATION
ROADMAP_REF = canonical heading / RD-ID
WP_ID_AND_AUTHORITY = exact reference / DIRECT_HUMAN_GOVERNANCE_REQUEST
PATH_IDS_USED = ...
ARTIFACTS = id, purpose, path_id, resolved_path, consumer, keep/delete condition
WRITE_SCOPE = exact files or bounded generated families
STORAGE_BUDGET = max_files, max_bytes, peak_bytes, reserve_bytes, max_runs
UNREGISTERED_WRITE_PATHS = NONE
PATH_REGISTRY_GATE = PASS | HOLD
```

No extra Human approval is needed to instantiate an approved template within
an existing lease. A new family requires Planner design and an approved scope;
a new material root or destructive lifecycle requires Human authority.
Unexpected new writes or unexplained duplicates stop the affected operation.
Do not silently redirect work to C:, D:, system TEMP or another checkout.

RUN: constrain test TEMP/TMP/basetemp, coverage, logs, build output and tool
caches where supported. Child processes inherit or explicitly receive the
same destinations. Tools with fixed caches get a distinct registered managed
entry. Never claim interception of every filesystem write from static checks.
Measure free space and peak growth on each affected volume. Estimate and
enforce finite budgets before heavy tests/builds; do not increase budgets just
to hide unbounded creation. Until a launcher enforces this, report MANUAL,
not MACHINE_ENFORCED. Shared tool caches require owner-aware cleanup.

POST: inventory created/modified outputs, keep an exact source/test evidence
binding when reusing a test result, and classify every artifact:

| Disposition | Required basis |
| --- | --- |
| KEEP_PRODUCT | Source, tests, migrations, templates or a reusable approved tool with a named consumer. |
| KEEP_EVIDENCE | Audit/reproduction, failure, release, rollback or required provenance dependencies. |
| DELETE_CANDIDATE | Task-owned, reproducible transient data with no remaining dependency. |
| KEEP_PENDING_REVIEW | Unknown ownership, active process, open finding or unresolved retention. |

Record bytes created, bytes kept by reason, bytes actually reclaimed, remaining
bytes, duplicate payloads and peak volume usage. Logical byte totals and actual
disk/free-space changes are different measurements. No zero-byte claim for
unmeasured data. A closed WP needs artifact disposition, not a false claim that
all its bytes vanished. Every deferred cleanup has an owner, reason and next
review condition; KEEP must not become an unowned permanent dumping ground.

## 6. Cleanup is an audited operation

An audit recommends deletion; it does not itself delete or grant permission.
Builder may execute bounded cleanup already expressly included in a lease
after its gate passes, without requesting approval per command. Otherwise
return the concrete manifest to the proper authority. This policy itself
authorizes no deletion of existing files on C: or D:.

For every deletion target verify git status AND tracked descendants via
`git ls-files`, owner marker/run identity, reproducibility, inbound references
(including frozen manifests and open audits), active writers/handles, real path
containment and explicit allowlist. Age, extension, ignored status or a WP
number alone is insufficient. Any error/unknown means KEEP and report.

Use `scripts/clean_dev.ps1 -WhatIf` first under the existing safety rule, but
its broad targets (`release_staging`, `.tmp`, `build`, `dist`) are not a safe
WP-specific deletion manifest. Do not run its broad deletion mode for this
policy. A future exact-target executor must validate each descendant, reject
links/escapes, recheck identity at deletion time, warn/skip ACL failures and
never elevate or take ownership. Never delete a repository or volume root.

Keep the minimal durable verification packet outside the disposable temp tree:
contract/input hashes, source/test binding, command/environment, result,
required logs/JUnit, review reference and cleanup receipt. Hashes alone cannot
replace unique source bytes, recovery artifacts or historical execution logs.
No automatic disposal of business data, HSMT, Ground Truth, databases,
sessions, release/rollback material or cited failure evidence. Tracked source
deletion still requires the exact Human request specified in AGENTS.

Do not promote the earlier 3–4-Parent retention direction into a global deletion
rule. Dedup/compaction must preserve references and recovery; immutable evidence
gets a successor manifest, never an in-place rewrite. Temporary success runs
may be deleted after evidence capture and authorized audit; failed runs remain
bounded and retained while investigation requires them.

## 7. Enforcement and closeout contract

Today: agent/manual gates apply prospectively in this checkout. Automated path
validation, filesystem attribution and automatic cleanup are NOT_IMPLEMENTED.
Independent Reviewer checks registry/WP coherence, path containment, lifecycle,
budgets, unexpected files and false existence/verification claims. The writer
does not certify its own independent audit.

```text
PATH_AUDIT = PASS | HOLD
ARTIFACT_DISPOSITION_COMPLETE = YES | NO
UNOWNED_NEW_ARTIFACTS = 0 | count
CLEANUP = NOT_NEEDED | EXECUTED_VERIFIED | DEFERRED_WITH_OWNER | HOLD
STORAGE_ACCOUNTING = measured totals / explicit gaps
SPINE_IMPACT = applicable canonical targets
```

No completion claim for unregistered writes, fabricated WPs/files, missing
required evidence, unexplained growth or unowned leftovers. A bounded documented
retention hold does not demand deletion to achieve a green gate.

Existing active/frozen WPs keep their exact approved paths. Reconcile this
policy at their next governed transition; do not retroactively alter their
audit objects. Rollout and remaining coverage are in PATH_REGISTRY_ROLLOUT.md.
