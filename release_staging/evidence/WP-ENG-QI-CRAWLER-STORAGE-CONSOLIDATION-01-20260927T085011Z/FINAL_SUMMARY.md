# WP-ENG-QI-CRAWLER-STORAGE-CONSOLIDATION-01 — M2 result

```text
RUN_ID = 20260927T085011Z
CHECKOUT = D:\QI Technology\QI Crawler\egp-crawler-python
ORIGIN = https://github.com/tanntran2000/QI-Crawler-MVP.git
BRANCH = codex/crawler-storage-consolidation-01
CODE_HEAD = c0d6fbf7a5d5429effac8dc9137d73b7fee50f4b
M0_COMMIT = faf8e968c9dd41bdd74cab1923c72df38201f131
M1_COMMIT = c0d6fbf7a5d5429effac8dc9137d73b7fee50f4b
M2_STATUS = COMPLETE_WITH_THREE_DELETIONS_AND_ONE_KEEP_PENDING_REVIEW
```

## Dispositions

| Exact allowlisted app subtree | Disposition | Pre-delete files / descendant dirs | Logical bytes removed | Receipt SHA-256 |
|---|---|---:|---:|---|
| `D:\QI-Crawler-Candidates\v0.10.0-376efdad-20260918T092709Z\app` | Deleted; complete | 1,775 / 137 | 1,755,258,576 | `BCD17AC7F6479A7AA27A875FF98976B0CD4E227860CBDCDF968EA5D2E3F89AB3` |
| `D:\QI-Crawler-Candidates\v0.10.0-f3856385-20260918T152214Z\app` | Deleted; complete | 1,775 / 137 | 1,755,259,162 | `325B1145EAC67EC6C5D0121AE700568E6572CCDE1CF168A06C85D22DC691195C` |
| `D:\QI-Crawler-Candidates\v0.10.0-55c0bddf-20260921T093954Z\app` | Deleted; complete | 2,445 / 204 | 1,810,610,828 | `300F28BA477F72D889D263C96743B31A87FD653CAC068B9F0620ADF21BCF57A0` |
| `D:\QI-Crawler-Candidates\v0.10.0-fb8edac-20260921T010751Z\app` | `KEEP_PENDING_REVIEW`; no point-of-use census or deletion | Matching Acceptance recovery-copy-01/02 exists; independence from the exact app binary is unproven | 0 | Not applicable |

## Deletion gates and protected state

Before each of the three deletions, the Builder revalidated the exact resolved
direct `app` child, containment inside `D:\QI-Crawler-Candidates`, every path
component and the full subtree for reparse points, parent identity, candidate
inventory, portable receipt, EXE / build-info / release-manifest hashes, and
source Git object. Each target had zero reparse points and matched its
recorded file count and logical bytes. Candidate data, control, evidence and
output siblings remained protected; target 3's pre-start acceptance receipt
was retained.

The point-of-use process census for each deletion ran as `ADMIN-PC\Admin` with
`ADMIN_ROLE=False`, without RunAs, UAC, ACL changes or process control. CIM
returned zero `QI-Crawler.exe` processes; trusted
`C:\Windows\System32\tasklist.exe /FI "IMAGENAME eq QI-Crawler.exe"` exited
0 and reported no matching tasks; supplemental `Get-Process` returned zero.
The receipts preserve each capture time and result.

Post-delete checks passed for 25, 24 and 23 protected roots after excluding
the target being deleted. The checks included the operational installation,
all of `D:\QI-Crawler`, the live database, current EXE / build-info / manifest
and operational receipts, Acceptance, Rollback, AppData, protected candidate
apps, retained candidate app tree and protected siblings. The database stayed
at 2,043,904 bytes and SHA-256
`33A3A5ADACA15514A18714DBD9281C224C174B8471341EEB8C333C11748818EE`.
Every deletion receipt records zero protected mismatches and zero bytes/files
remaining in its target.

No operational database, application data, current installation, candidate
root or sibling, Acceptance, Rollback, AppData, repository source or test was
changed. No process was started. No remote action, cleanup or unrelated
deletion occurred.

## Byte and retained-artifact accounting

- Total logical bytes removed from the three exact `app` subtrees:
  **5,321,128,566**. Each receipt records pre-delete counts and bytes,
  post-delete remaining counts and bytes, and logical bytes removed.
- Per-target observed free-space deltas: target 1 **1,757,388,800** bytes;
  target 2 **1,757,388,800** bytes; target 3 **1,813,471,232** bytes.
- Net observed free-space change from the first immediate pre-delete read
  (**15,445,442,560** bytes free) through the third post-delete read
  (**20,770,123,776** bytes free): **5,324,681,216** bytes.
- Free-space observations are not exact cleanup attribution. Concurrent
  activity, allocation units, compression, sparse files, hardlinks or other
  volume changes may affect the delta. The D: reserve remained above
  10,737,418,240 bytes before each deletion.
- Evidence directory contains the sanitized disposition, this summary, three
  deletion receipts and `RAW_INVENTORY.json` (6 files; aggregate bytes=186231).
  The raw manifest is local-only and must never be staged or published. The
  registered one-directory, eight-file, 67,108,864-byte run cap remains
  satisfied.

## Limitations and handoff

Source Git objects remain available, but byte-identical rebuilds were not
proven. The `fb8edac` recovery-copy role is unresolved, so its app bytes stay
KEEP_PENDING_REVIEW. The initial sandbox process-census denial is superseded
only for the recorded snapshots by the same-user non-admin Planner census and
the immediate same-user point-of-use censuses; it is not a general process
observation guarantee. One parent-identity precheck aborted before any process
census or deletion because PowerShell reparsed an already-UTC timestamp; the
comparison was corrected to UTC ticks and the full gates then passed. No
external mutation occurred during that aborted precheck.

## Plugin evidence

- `ecc:safety-guard` — `REQUIRED` before external deletion. **Invocation:**
  read `C:\Users\Admin\.codex\plugins\cache\ecc\ecc\2.2.2\skills\safety-guard\SKILL.md`
  and applied its careful-mode constraints before M2. **Result:**
  `USED_AND_SUCCEEDED` as manual guidance; exact paths, `-LiteralPath`,
  reparse checks, same-user/non-admin census and fail-closed gates were used.
  **Fallback:** no callable safety-guard activation tool was available.
  **Impact radius:** the three authorized app subtrees and protected-root
  verification. **Edit radius:** those exact app subtrees plus registered
  evidence and CURRENT. **Test radius:** point-of-use gate / post-check
  receipts. **Limitation:** manual checks do not create machine enforcement.
- `ecc:living-docs-governance` — `REQUIRED` before Spine edits. **Invocation:**
  read and applied its guidance before the CURRENT M2 checkpoint.
  **Result:** `USED_AND_SUCCEEDED`. **Fallback:** direct current-state and
  unique-key validation. **Impact radius:** CURRENT handoff state.
  **Edit radius:** CURRENT plus its linked registered result evidence.
  **Test radius:** key uniqueness, exact scope and diff checks.
- `ecc:git-workflow` — `REQUIRED` for M0 branch handling. **Invocation:**
  applied during the M0 canonical branch/base transition.
  **Result:** `USED_AND_SUCCEEDED`; M2 remained local-only.
  **Fallback:** normal Git identity/status checks. **Impact radius:** local
  branch lifecycle. **Edit radius:** no additional files in M2.
  **Test radius:** Git identity, tracked/index and exact path checks.
- CodeGraph — `NOT_APPLICABLE`; M2 made no product-code change and no unresolved
  code-impact question arose. No CodeGraph invocation is claimed.

```text
SPINE_IMPACT = CURRENT
SPINE_TARGET_FILES = docs/agent_handoff/CURRENT.md
SPINE_SYNC_STATE = PASS_FOR_M2_FINAL_CHECKPOINT
PROVEN_COMPLETE = M0; M1; M2 conditional processing for three qualified targets; hold decision for fb8edac
PROVEN_NOT_COMPLETE = fb8edac app reclamation; Planner Parent-WP closeout; independent audit; hosted CI / remote integration
EXACTLY_ONE_NEXT_ACTION = PLANNER_REVIEWS_M2_DISPOSITION_AND_DECIDES_CONTINUATION_OR_CLOSEOUT
NEXT_AUTHORITY = PLANNER_ARCHITECT
```
