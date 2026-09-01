# WP-TB-BASIC-CRAWLER-03 - Micro-C Real Operational Closure

Status: authorized in progress; evidence-only acceptance.

## Entry and boundaries

- Entry head: `6220c1296a6b20d59626731560ee1bf00515d2a9`.
- Primary release: `IB2500585490-00` (base `IB2500585490`, revision `00`).
- No production, test, schema, migration, database, source-file, push, PR, merge, release, or Team Bid pilot writes.
- Live DB is forbidden. All operational checks use an isolated temporary acceptance root.
- Preserve original attachment filenames and bytes; never rename, move, delete, or overwrite the user sources.

## Verified source assets

- PDF `Ho so moi thau_Bai2.pdf`; SHA-256 `C92D6BD81C582867563679F8B0574E98BF2E4EEBDD429CF6F7E0F7E6A2A51D52`.
- DOCX `Bai2_Chuong III.docx`; SHA-256 `3BCED58DBFCDE84A6F08761733040B1D1C2A777DA52436ACFAE3DB70D5EAC45A`.
- DOCX `Bai2-Chuong V.docx`; SHA-256 `0C941C7DFF67E76632C426886FD391D1A1052863BBCD9B65DC4A4601F253D00E`.

## Acceptance sequence

1. Copy the three verified assets to `D:\\QI Technology\\Temp\\QI-Crawler-Acceptance\\WP-TB-BASIC-CRAWLER-03-MICRO-C` and record source/copy hashes; use an isolated temporary database only.
2. Through the existing public operational seam, scan and create the exact `IB2500585490-00` case/release. Capture document, membership, workspace, and revision-event counts before/after and prove scan is zero-write.
3. Human-confirm A1 alone; prove A2/A3 remain unselected and zero-write. Rehash immediately before each intake to exercise the TOCTOU guard, then confirm A2 and A3 separately.
4. Prove same-package DOCX authority, preserved original filenames and SHA values, managed projection, restart/reopen, exact-release search/manifest, and controlled export.
5. Dispose the DB/service completely, create a fresh instance, and verify the same release, memberships, authority classes, logical names, original filenames, and hashes.
6. Run a bounded local search for genuine `QuyetDinh_PL2600263838.pdf`; if absent record `REAL_REFERENCE_OPERATIONAL_EVIDENCE=EVIDENCE_GAP` and do not substitute a file.
7. Run a bounded local search for genuine `IB2500585490-01/-02`; if absent record `REAL_MULTI_REVISION_EVIDENCE=EVIDENCE_GAP` and do not synthesize a revision. At most one official-source retrieval pass is allowed by the Work Order.
8. Run targeted B1+B2 regression, full pytest, Ruff, pip check, and diff-check. Keep temporary logs/scripts outside tracked repository paths.

## Stop conditions

Stop and return to Planner without code edits if behavior differs from the B1/B2 contract, any false-safe or fabricated identity appears, foreign source contamination occurs, a live DB or user-source mutation occurs, or product/test/schema changes become necessary. Evidence gaps for a second revision or foreign reference are not product defects.
