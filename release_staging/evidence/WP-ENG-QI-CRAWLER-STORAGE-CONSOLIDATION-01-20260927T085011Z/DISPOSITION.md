# M1 candidate inventory and disposition

WP: `WP-ENG-QI-CRAWLER-STORAGE-CONSOLIDATION-01`
Run: `20260927T085011Z`
Branch/code head at inventory: `codex/crawler-storage-consolidation-01` / `faf8e968c9dd41bdd74cab1923c72df38201f131`
Raw local-only manifest: `RAW_INVENTORY.json` (never stage or publish)

## Decision

M1 read-only inventory is complete. All four exact deletion targets are
`KEEP_PENDING_REVIEW`. M2 did not start. The pre-inventory CIM path-aware
process census returned Access denied and the trusted System32 `tasklist.exe`
fallback also returned Access denied. The supplemental `Get-Process` query
was empty but cannot authorize deletion. The batch-wide process rule therefore
holds every candidate; no per-target census, retry, elevation, or delete was
attempted. Exact-binary recovery/reproduction need is also not proven absent.

The inventory covered the named operational, candidate, Acceptance, Rollback,
and AppData roots at metadata level. `D:\QI-Crawler` still exposes only its
protected `Current`, `Data`, and `control` roots. Candidate roots and their
`control`, `data-root`, `evidence`, and `output` siblings are retained. Their
contents, operational databases, HSMT material, configuration contents, logs,
Acceptance, Rollback, and AppData were not opened or changed. The two protected
candidate app siblings `v0.10.0-f6782d7e` and `v0.10.0-b4f016d7` remain KEEP.
The `fb8edac` target also has a matching Acceptance root with recovery-copy
folders, so an exact-binary recovery role remains unresolved.

## Exact target inventory

All paths resolved to the exact direct `app` child under
`D:\QI-Crawler-Candidates`. Each ancestor component and every app descendant
was enumerated without following reparse points; each census completed with
zero reparse entries. Parent identity remained stable between the inventory
and receipt checks. Portable receipt identity/hash fields matched the current
`QI-Crawler.exe`, `BUILD_INFO.txt`, and `release_manifest.json`; each recorded
source Git commit object is available. Source availability does not prove a
byte-identical rebuild.

| Candidate / exact app | Source Git SHA | Files / dirs | Logical bytes | EXE SHA-256 | Portable receipt SHA-256 | Disposition |
|---|---|---:|---:|---|---|---|
| `v0.10.0-376efdad-20260918T092709Z` | `376efdad62907938a2af1596ed75bef2dd0616cf` | 1,775 / 137 | 1,755,258,576 | `2A846325725AE75B70C306DB52F993E7E68CAB76BC998DBCA512E316F61F69C9` | `53388C4EEA151A9A8B43174514E78904C004BD6013F53FDD1A2407ABE27DEF71` | KEEP_PENDING_REVIEW |
| `v0.10.0-f3856385-20260918T152214Z` | `f3856385f06445a30c6d677960625b0575060fc4` | 1,775 / 137 | 1,755,259,162 | `B1507C9A3B4B5393D9B2734B7B3D4DBC4630C6366EF583D88671DAC4657F17E3` | `9DDCA4A2BB29988E96DC62881C88E8451E44A9891EC8301B26B2D10297236269` | KEEP_PENDING_REVIEW |
| `v0.10.0-55c0bddf-20260921T093954Z` | `55c0bddfebf7ef13e2e06e93e7460544a757b3de` | 2,445 / 204 | 1,810,610,828 | `8F0C430F47FBB5316B7FD7F1F0F9C7D4E904B9185A0C973E620BDCA88568589C` | `5A02093CEE553D3DD583B358448AF1A03C1328B6D61701105AE6CFBEB69EF558` | KEEP_PENDING_REVIEW |
| `v0.10.0-fb8edac-20260921T010751Z` | `fb8edac793ab37cd7289b1d1cc684d958118ab4d` | 2,445 / 204 | 1,810,607,486 | `B89D09223510C7ED30E7D2321B6088B4A149E0E9965298B530C609DC1BC55497` | `515A0231D9821B9F017D9398636A5C222E15B545B3448BBFD22F29F3109FB696` | KEEP_PENDING_REVIEW |

Receipt and named protected sibling receipt hashes, full three-artifact hash
sets, path-component metadata, and field-match results are in the raw local
manifest. Candidate data/control/evidence/output siblings and their receipts
remain KEEP; receipt content was not read except the portable artifact receipt
needed to verify its identity and artifact hash fields. No configuration,
database, HSMT, or raw log content was read.

## Reference and process evidence

The tracked governance search found the four IDs only in this approved Work
Order allowlist and its locator registration; no other tracked governance,
handoff, or plan reference matched. The two prior storage-relief Builder
reports were reviewed and did not reference these candidate IDs/source SHAs.
The rollback root’s observed direct child is `v0.9-20260923T014400Z`; this
does not prove exact-candidate binaries are unnecessary for recovery or
reproduction. The current operational installation is kept intact.

Process census elapsed about 0.3 seconds, within the two-minute bound. Both
required routes were unavailable due to Access denied; errors were not a
clearly transient read failure, so no retry was used. There is no verified
zero-process result. Deletion authority is not satisfied.

## Byte and evidence accounting

- Candidate app logical bytes inventoried: 7,131,736,052.
- Logical bytes removed: `0`.
- Observed volume free-space delta from deletion: `NOT_MEASURED`; no deletion occurred.
- D: free space was 15,444,156,416 bytes before the registered evidence run and
  15,417,384,960 bytes at disposition capture, above the 10,737,418,240-byte
  reserve. These observations are not attributed to candidate cleanup.
- No candidate, operational, Acceptance, Rollback, AppData, repository, or
  unknown artifact was deleted or otherwise mutated.
- Retained evidence root currently contains only this sanitized record and the
  local-only raw manifest, within the one-run / one-directory / eight-file /
  67,108,864-byte cap. Evidence is KEEP; cleanup is unauthorized.

**M1 status:** inventory/disposition complete and returned for Planner review.
**M2 status:** not started; batch held by process-census Access denied and
unresolved exact-binary need.
**Spine:** `CURRENT` records this exact blocker; `SPINE_SYNC_STATE=PASS` for
this M1 return.
**Next authority:** `PLANNER_ARCHITECT` to review the M1 evidence and decide the
next authorized action.

## M2 conditional sequential deletion result

This section records the later M2 checkpoint; the M1 disposition above is a
historical snapshot and remains accurate for that earlier state. The Planner's
bounded review cleared targets 1–3 for fresh point-of-use gates. Target 4
remains held because the matching Acceptance recovery-copy references are not
proven independent of its exact app binary.

| Candidate app subtree | Result | Pre-delete inventory | Logical bytes removed | Receipt SHA-256 |
|---|---|---:|---:|---|
| `D:\QI-Crawler-Candidates\v0.10.0-376efdad-20260918T092709Z\app` | DELETED; target complete | 1,775 files / 137 descendant dirs; zero reparse | 1,755,258,576 | `BCD17AC7F6479A7AA27A875FF98976B0CD4E227860CBDCDF968EA5D2E3F89AB3` |
| `D:\QI-Crawler-Candidates\v0.10.0-f3856385-20260918T152214Z\app` | DELETED; target complete | 1,775 files / 137 descendant dirs; zero reparse | 1,755,259,162 | `325B1145EAC67EC6C5D0121AE700568E6572CCDE1CF168A06C85D22DC691195C` |
| `D:\QI-Crawler-Candidates\v0.10.0-55c0bddf-20260921T093954Z\app` | DELETED; target complete | 2,445 files / 204 descendant dirs; zero reparse | 1,810,610,828 | `300F28BA477F72D889D263C96743B31A87FD653CAC068B9F0620ADF21BCF57A0` |
| `D:\QI-Crawler-Candidates\v0.10.0-fb8edac-20260921T010751Z\app` | KEEP_PENDING_REVIEW; no census or deletion | Matching Acceptance recovery-copy-01/02 remains; independence from exact binary is unproven | 0 | Not applicable |

Each deletion had a fresh, immediate same-user process census with
`ADMIN_ROLE=False`: CIM found zero `QI-Crawler.exe` processes, trusted
`C:\Windows\System32\tasklist.exe` exited 0 and reported no matching tasks,
and supplemental `Get-Process` found zero. The exact allowlisted direct app
path, containment, ancestor components, recursive reparse census, portable
receipt, `QI-Crawler.exe` / `BUILD_INFO.txt` / release-manifest hashes and
source Git object were revalidated before each deletion. No Windows elevation,
ACL change or process control was used.

All per-target protected post-checks passed (25, 24 and 23 protected roots,
respectively, after excluding the exact app being deleted). The live database
remained 2,043,904 bytes with SHA-256
`33A3A5ADACA15514A18714DBD9281C224C174B8471341EEB8C333C11748818EE`; the
current install's executable/build/manifest/receipts, operational root,
AppData, Acceptance, Rollback, protected candidate app siblings, and all
candidate `control`, `data-root`, `evidence` and `output` siblings were
unchanged. Target 3's `control\pre_start_acceptance.json` and all other
named sibling receipts were retained and hash-checked.

Total logical bytes removed were **5,321,128,566**. Immediate observed free
space deltas were 1,757,388,800 bytes, 1,757,388,800 bytes and 1,813,471,232
bytes. The net observation from the first pre-delete reading through the third
post-delete reading was 5,324,681,216 bytes. These are volume observations,
not exact cleanup attribution; unrelated activity and allocation, compression,
sparse-file or hardlink behavior may affect them. Per-target counts, before /
remaining bytes, census results and protected comparisons are in the three
`DELETE_0N_RECEIPT.json` files.

No application data, database, current installation, candidate root, sibling,
Acceptance, Rollback, AppData, repository source or test was changed. No
remote operation, cleanup or unrelated deletion occurred. The raw inventory
manifest remains local-only and must not be staged or published. The sanitized
receipts and final summary are retained within the registered evidence budget.

**M2 status:** conditional sequential deletion complete for the three targets
whose gates passed; `fb8edac` remains KEEP_PENDING_REVIEW. The Work Order has
not been Planner-closed. `CURRENT.md` records the handoff state; next authority
is `PLANNER_ARCHITECT` for M2 result review and closeout/continuation decision.
