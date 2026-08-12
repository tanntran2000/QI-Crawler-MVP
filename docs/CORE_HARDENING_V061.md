# Core Hardening v0.6.1

Muc tieu cua sprint nay la lam crawler co the kiem chung, chay lai an toan va phuc hoi
sau loi truoc khi them AI hoac Bid Control.

## WP1 - Baseline va Golden Dataset

- Tag baseline: `v0.6.1-core-baseline`.
- Database that luon backup va giu o may cuc bo; khong dua `data/egp.db` len Git.
- Fixture HTML e-GP trong `tests/fixtures/golden/source/` la snapshot co dinh de CI
  khong phu thuoc website that.
- Day la **golden persistence/idempotency baseline**: test kiem tra ma thong bao, ten goi,
  ben moi thau, gia, deadline, URL nguon va danh sach tep dinh kem sau khi du lieu da duoc
  chuyen thanh `ParsedNotice`.
- Test chay lai phai giu nguyen ID va khong tao ban ghi trung; khi thong bao cung ma thay doi,
  ban ghi phai duoc cap nhat tai cho thay vi tao ban sao.
- WP1 chua kiem tra HTML/JSON nguon qua Source Adapter va Parser. Day la pham vi cua WP2.

Gia tri trong fixture la snapshot nghiep vu, khong phai ket qua tim kiem moi. Khi them nguon
thuc te moi, nguoi phu trach phai xac nhan quyen su dung du lieu va cap nhat fixture bang pull
request co review.

## Work package tiep theo

1. WP2: adapter nguon, parser va idempotency; them sau raw JSON/HTML fixture de kiem tra
   toan bo luong nguon -> `ParsedNotice` -> database ma khong goi website that trong CI.
2. WP3: `crawl_tasks`, retry, checkpoint va resume. `crawl_runs` chi luu tong ket;
   tung URL luu rieng trang thai `PENDING`, `RUNNING`, `COMPLETED`,
   `FAILED_RETRYABLE` hoac `FAILED` de resume chinh xac.
3. WP4: Alembic migration co review tren ban sao `egp.db`. Revision `0003_complete_core_schema`
   tao du schema tren DB trang va chi them bang/cot thieu tren DB cu; khong dung `create_all()` trong migration.
   Lenh `QI-Crawler db-upgrade` sao luu SQLite truoc, stamp checkpoint `0001_add_crawl_tasks` cho
   database pre-Alembic da co `crawl_tasks`, roi moi nang cap den `head`.
4. WP5: golden-file test cho TBMT exporter.
5. WP6: FTS5 capability check, trigger thu cong va fallback search. Khi FTS5 co san,
   `tim-goi` dung `MATCH` tren title, buyer, mo ta va item; neu khong co thi fallback
   tim kiem cuc bo. Ca hai cach deu chuan hoa chu co dau va khong tu dong sua keyword pool.

## Runtime schema

Runtime khong goi `create_all()` hoac additive migration nua. Neu schema chua o revision hien tai,
QI-Crawler dung va yeu cau nguoi van hanh dong ung dung roi chay `QI-Crawler db-upgrade`.

Khong dua Celery/Redis, RBAC/JWT, LLM/OCR hoac dashboard lon vao sprint nay.

## Known limitation - attachment phien ban cu

Trong phien ban hien tai, attachment xuat hien o lan crawl truoc nhung khong con duoc
nguon liet ke o lan sau van duoc giu lai. He thong khong xoa tep de tranh mat bang chung,
nhung nguoi dung can kiem tra thoi diem tai va URL truoc khi su dung. Co che `is_current` va
`superseded_at` se duoc thiet ke cung phan versioning attachment o work package sau.
