# QI-Crawler candidate release contract

This contract governs the future v0.10.0 portable candidate assembly and its
first access to copied business data. It does not authorize a build, data copy,
migration, launch, installation, publication, promotion, tag, release, or merge.

## Canonical candidate layout

The future Build Work Order must resolve one fresh boundary with this pattern:

```text
D:\QI-Crawler-Candidates\
  v0.10.0-<FROZEN_SHORT_SHA>-<BUILD_ID>\
    app\
      QI-Crawler\
    data-root\
    output\
    control\
      portable_artifact_receipt.json
      pre_start_acceptance.json
    evidence\
```

The candidate boundary, application root, and data root must be physically and
logically disjoint from `D:\QI-Crawler` and
`%LOCALAPPDATA%\QI-Crawler`. Before first business startup, the controlled gate
must validate the exact build, frozen source SHA, clone receipt, migration
receipt, migrated database, managed-document mapping, and candidate-only
configuration. Invalid evidence means the application is not launched.

The portable candidate and a future installer have separate artifact identities.
`portable_artifact_receipt.json` uses `qi-crawler-portable-artifact-v1`, is
produced from the actual portable EXE, release manifest, and `BUILD_INFO.txt`,
and contains no installer hash. A future installer/publisher receipt remains a
separate lifecycle artifact and is not required for portable readiness.

A frozen bundle with release channel `INTERNAL_CANDIDATE` must authorize its
governed candidate root before standalone runtime preparation. Normal direct
startup requires a valid existing acceptance and binds data/config to the
candidate root. Pre-acceptance smoke is permitted only with an explicit isolated
data root that does not overlap working user data or the candidate boundary.

Candidate authorization binds all three effective storage inputs before
configuration loading: `QI_CRAWLER_DATA_DIR`, `QI_CRAWLER_CONFIG_PATH`, and
`QI_CRAWLER_DATABASE_URL`. The database URL is derived from the single
`StandalonePaths.database_path` authority and identifies exactly
`<candidate-data-root>/data/database/egp.db`. Direct startup, the controlled
launcher, and isolated smoke must overwrite inherited process values with this
candidate-specific URL so a candidate `.env` cannot redirect database access.

After `load_config()` and before constructing `Database`, candidate startup must
parse and validate the effective URL. It must use SQLite, resolve exactly to the
authorized candidate database, and remain inside the explicit candidate or
smoke data root. An external, relative escape, in-memory, non-SQLite, malformed,
or otherwise noncanonical target fails closed with
`CANDIDATE_EFFECTIVE_DATABASE_ESCAPE`; no database constructor or connection may
run first. This candidate-only rule does not remove the existing
`QI_CRAWLER_DATABASE_URL` override for ordinary non-candidate development or CLI
operation. Acceptance binds the database location, not immutable database bytes;
normal post-acceptance database writes remain allowed.

## Storage budget

All values are byte ceilings for one candidate run. The managed-document limit
is a sublimit of the cloned-data limit and is not counted twice when calculating
required free space.

| Category | Ceiling |
| --- | ---: |
| Build intermediates | 6 GiB |
| Portable bundle | 3 GiB |
| Candidate cloned data, total | 12 GiB |
| Managed documents within cloned data | 10 GiB |
| Migration backup and migration evidence | 2 GiB |
| Acceptance outputs and durable evidence | 2 GiB |
| Logs | 256 MiB |
| Temporary files | 4 GiB |
| Untouched safety reserve after the run | 4 GiB |

The future Build Work Order must calculate required headroom before any material
write. The minimum is the sum of all applicable top-level ceilings plus the
4 GiB safety reserve: 33.25 GiB when every category above is needed. A category
may receive a smaller per-run lease when PRE measurements justify it; no
category may exceed its ceiling without a new Human/Planner authorization.

The run must record:

1. **PRE:** exact resolved roots, volume identity, free bytes, source DB/WAL/SHM
   bytes, managed-document bytes, planned per-category leases, and required
   safety reserve.
2. **RUN:** bytes created per category and remaining free space. Stop before the
   next write if a lease, category ceiling, or reserve would be crossed.
3. **POST:** retained bytes, reclaimed task-owned transient bytes, remaining
   free space, and disposition of every created root.

Unknown artifacts are `KEEP`. Cleanup requires an exact task-owned allowlist and
the Path Registry lifecycle rules. No working runtime or user-data bytes may be
counted as reclaimable headroom.

## Evidence stages

Candidate data preparation preserves the v0.9 standalone source contract when
`storage.document_dir` is absent: the source managed-document root resolves to
`<source-root>/data/documents` with basis `LEGACY_STANDALONE_DEFAULT`. This is a
bounded omitted-field compatibility rule. An explicitly present empty, null, or
invalid value fails closed; an explicit relative value resolves from the source
root; every resolved root remains source-contained and reparse-free. Database
`documents.stored_path` records remain the file authority and must stay within
that root with their existing SHA checks. Candidate preparation never writes the
fallback into the source config or creates the source directory solely for a
zero-document clone. A successful clone receipt records the exact source root,
resolution basis, and whether the field was declared.

`CLONE_RECEIPT` is authoritative for the pre-migration candidate state.
`MIGRATION_RECEIPT` supersedes the clone database-byte identity after a
successful isolated migration. `PRE_FIRST_BUSINESS_STARTUP_ACCEPTANCE` binds the
approved initial operational state. The clone hash is not a permanent runtime
invariant after normal application writes begin.

Migration execution must use an exact clean Git checkout whose `HEAD` equals the
expected frozen commit. Each executed Alembic version file must match its Git
blob at that commit. Untracked build output does not invalidate a clean tracked
tree and must not be deleted by this verification. Before backup or migration,
the actually loaded `candidate_readiness`, `candidate_data`, `migrations`, and
`db` modules must resolve to their canonical paths inside that same checkout and
match their Git objects. `alembic.ini` and `alembic/env.py` must also match their
frozen Git objects. The migration receipt records this execution-code identity
and later evidence validation rechecks the durable file/Git lineage without
requiring a later candidate runtime to load modules from the build checkout.

This verification has a controlled build-time TOCTOU limitation. The frozen
checkout remains under the Single Writer contract with no concurrent source
mutation between verification and migration; this contract does not claim an
immutable filesystem or introduce a source-locking subsystem.

`PRE_FIRST_BUSINESS_STARTUP_ACCEPTANCE` means the initial candidate state was
accepted; it does not assert that a process started. A failed process launch
preserves this write-once evidence, and a later launch may reuse it after
revalidating immutable build/root/receipt lineage. Runtime authorization must
not compare the current operational DB byte hash to the historical pre-start
hash, because normal application writes are allowed after acceptance.
