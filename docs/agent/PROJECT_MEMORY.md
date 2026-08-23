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
- **Evidence:** merged Windows release mechanics and hosted CI success.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## Explicitly not promoted

Vault/Shelf/Recovery, future storage hardening, HSNL, AI/Learning, legal
judgement, scoring, GO/HOLD/NO-GO, and future extraction work remain pending
unless a later Work Package is merged and verified.

## MEM-006 — SA Excel source routing (pending merge)

- **State:** PENDING MERGE
- **Since branch:** `wp/mi-source-type-routing-ground-truth`.
- **Contract:** Excel intake treats filename as a hint, validates KHMT/TBMT
  schema and PL/IB namespace evidence, requires named Human correction for
  unknown/conflicting sources, and records corrections append-only. TBMT is
  recognized but is not converted into KHMT PlanPackage records.
- **Evidence:** WP-MI-SRC-01 implementation and focused regression suite.
- **Implementation commit:** `660a33a` (`Add SA Excel source routing and human corrections`).
