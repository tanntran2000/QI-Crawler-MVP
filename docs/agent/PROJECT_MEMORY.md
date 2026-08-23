# Project Memory — `main` Truth Only

Only facts already merged to `main` belong here. Proposals and unfinished
branches must remain in their Work Package handoff.

## MEM-001 — Canonical workspace

- **State:** ACTIVE
- **Since main commit:** `311f6fb`
- **Contract:** Work in the canonical `egp-crawler-python` checkout on one
  short-lived branch. Do not create Git worktrees, sibling clones, or WP
  folders. After an approved merge, return to `main`, fast-forward from
  `origin/main`, and delete the merged local branch.
- **Evidence:** merged workspace policy and `AGENTS.md`.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## MEM-002 — Market intelligence authority

- **State:** ACTIVE
- **Since main commit:** `3f847f3`
- **Contract:** MI-0 through MI-6 are merged and accepted. KHMT import,
  targeted search, human review, confirmed XLSX, Legal DOCX, and Bid Radar
  reuse their existing authority services. Filter match is never human
  confirmation; PL and IB remain separate namespaces.
- **Evidence:** merged MI work and Real Golden acceptance on `main`.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## MEM-003 — Managed document storage boundary

- **State:** ACTIVE
- **Since main commit:** `74cab1c`
- **Contract:** The managed Document Store preserves original bytes,
  content SHA/version, tender identity, and bundle membership. Filename/path
  is metadata, not identity. Vault/Shelf/Recovery/cold-archive work is **not**
  claimed complete.
- **Evidence:** merged document-intake and bundle-guard tests.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## MEM-004 — Source of record and derived outputs

- **State:** ACTIVE
- **Since main commit:** `5592c9c`
- **Contract:** SQLite/review history is authoritative. XLSX/DOCX reports
  are derived outputs and must not mutate source packages or review history.
  `FILTER MATCH != HUMAN CONFIRMED`.
- **Evidence:** MI-3/MI-4/MI-5 regression suites and Real Golden evidence.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## MEM-005 — Windows publish boundary

- **State:** ACTIVE
- **Since main commit:** `e345256`
- **Contract:** `dist` is a generated build workspace. The user-visible
  `Crawler tool\Current` is the publish authority, updated only by an explicit
  clean-main publish after a verified candidate; failed candidates do not
  replace Current. The approved Team Bid release is `0.8.0`.
- **Release identity:** application/package `0.8.0`, source SHA
  `c1e9e16ffca3b3fd83ba7a150b16353445d7856e`, immutable annotated tag
  `v0.8.0`, and GitHub Release `v0.8.0`. The release manifest, BUILD_INFO and
  SHA256SUMS record the installer/EXE hashes. `Crawler tool\Current` and the
  Team Bid Reference are derived from this same verified identity.
- **Evidence:** merged Windows release mechanics, hosted CI, and the
  published v0.8.0 release artifacts.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## Explicitly not promoted

Vault/Shelf/Recovery, future storage hardening, HSNL, AI/Learning, legal
judgement, scoring, GO/HOLD/NO-GO, and future extraction work remain pending
unless a later Work Package is merged and verified.
