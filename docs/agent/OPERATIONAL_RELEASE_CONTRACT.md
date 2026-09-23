# Operational release contract

This contract defines the separate `INTERNAL_PILOT` runtime lane introduced by
B09. It does not convert a candidate into an installed release or grant live
execution authority. The live entrypoint is fail-closed unless the caller
passes the explicit `--execute-live-promotion` guard.

## Stable layout

An operational root is a stable root such as `D:\QI-Crawler` with these
boundaries:

```text
Current\QI-Crawler\QI-Crawler.exe
Current\QI-Crawler\runtime\
Current\QI-Crawler\BUILD_INFO.txt
Current\QI-Crawler\release_manifest.json
Data\config.yaml
Data\data\database\egp.db
Data\data\documents\
Data\data\downloads\
Data\data\discovery\
Data\data\raw\
Data\data\rejects\
Data\data\reports\
Data\data\sessions\
Data\data\backups\
Data\logs\
control\operational_acceptance.json
control\operational_migration_receipt.json
```

`Current\QI-Crawler` is immutable application content for the accepted bundle;
`Data` is the mutable operational root. Both must remain inside the one stable
root and must not overlap. The candidate layout and its
`pre_start_acceptance.json` remain a separate contract.

## Direct-start binding

Before configuration or database construction, a frozen executable whose
manifest declares `release_channel=INTERNAL_PILOT` must pass the operational
acceptance receipt and bind:

```text
QI_CRAWLER_DATA_DIR=D:\QI-Crawler\Data
QI_CRAWLER_CONFIG_PATH=D:\QI-Crawler\Data\config.yaml
QI_CRAWLER_DATABASE_URL=sqlite:///D:/QI-Crawler/Data/data/database/egp.db
```

The validator fails closed for a missing or substituted candidate receipt,
unexpected layout, root/path escape, metadata/hash mismatch, unsupported
schema, missing migration provenance or a database outside `Data`.

Before setting these environment variables, operational acceptance also reads
the persisted `Data\config.yaml` without calling `load_config()` or creating
directories. All seven explicit storage bindings (database URL, documents,
downloads, discovery, raw, rejects and reports) must resolve to their exact
paths under this operational `Data` root. Missing/malformed fields, non-SQLite
or ambiguous database URLs, and resolvable symlink/junction escapes fail closed
as `OPERATIONAL_CONFIG_BINDING_INVALID`. Environment overrides cannot mask a
bad persisted config.

## Acceptance receipt

The canonical schema is `qi-crawler-operational-acceptance-v1` at
`control\operational_acceptance.json`. It binds the operational root,
application bundle, executable, data/config/database paths, product/version,
source SHA, build timestamp, `INTERNAL_PILOT` channel, executable/manifest/
BUILD_INFO hashes, target schema, migration receipt SHA and migration source
provenance. The companion
`qi-crawler-operational-migration-v1` receipt records the source SHA,
`0020_add_tender_operational_revision_events` input and
`0022_add_tender_recovery_events` output.

`acceptance.database_sha256` is the **historical promotion-baseline DB SHA**;
it must equal `migration_receipt.output_db_sha256`. Runtime writes may change
the current DB bytes without invalidating startup. Every startup still requires
the exact operational DB path, a readable SQLite database, the current schema,
matching release/build identity and unchanged receipt/migration provenance.
The startup check reads the schema; it is not a full-file integrity scan.

The v1 acceptance receipt also requires bundle source SHA to equal acceptance
source SHA and migration source SHA. Therefore replacing only the application
bundle with a newly built SHA while preserving the existing migrated DB and
truthful old migration receipt is **not supported by the current v1 update
contract**. A later bounded operational-update contract must separate current
application-build provenance from historical migration provenance before any
such live update. No update or repair is authorized by this document.

## Promotion model

Synthetic promotion remains task-owned and is the default test path. The
guarded live entrypoint accepts only the fixed production roots
`D:\QI-Crawler` and `C:\Users\Admin\AppData\Local\QI-Crawler`, a fresh
`main` bundle whose source SHA equals the exact HEAD of the canonical checkout,
version `0.10.0`, and source schema
`0020_add_tender_operational_revision_events`. The checkout root must resolve
to its Git top level, remain on `main`, have no tracked changes, and keep the
same HEAD throughout source-identity verification. Before any write the gate
checks that identity, the bundle hashes, source schema, active process census,
rollback-root collision, volume/free-space requirements and the untouched 4
GiB reserve.

On Windows the process census first uses CIM for exact executable-path
authority. If CIM is unavailable, the gate invokes the trusted
`%SystemRoot%\System32\tasklist.exe` directly with a fixed argument list and
accepts only an exact `QI-Crawler.exe` image-name census. A fallback match has
unknown path authority and blocks promotion. Command failure, malformed or
ambiguous output, or inability to resolve the System32 executable fails closed
as `LIVE_PROCESS_CENSUS_FAILED`. A successful no-execute preflight reports the
census method, process count and path-authority level.

Both entrypoints use the same staged-copy/migration/receipt/rotation core;
only the root and authorization policy differs.

When separately authorized, live promotion follows:

```text
read-only source
→ consistent SQLite copy
→ migration on the copy
→ staged operational receipt
→ staged validation
→ bind staged config to future final root and validate it without writes
→ same-volume atomic root rotation
→ post-cutover validation
→ deterministic rollback on failure
```

The active AppData database is copied with SQLite's read-only backup API and
migrated only in the unique staging root. The original `D:\QI-Crawler` is
rotated intact to `D:\QI-Crawler-Rollback\v0.9-<UTC_TIMESTAMP>` before the
staged root becomes live; rollback is attempted only against those exact
roots. A preflight or an omitted execute flag performs no mutation. This
phase never executes the live entrypoint, and the B02 Inno Setup installer
remains deferred and is not required for B09.
