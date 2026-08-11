# Core Hardening v0.6.1

Muc tieu cua sprint nay la lam crawler co the kiem chung, chay lai an toan va phuc hoi
sau loi truoc khi them AI hoac Bid Control.

## WP1 - Baseline va Golden Dataset

- Tag baseline: `v0.6.1-core-baseline`.
- Database that luon backup va giu o may cuc bo; khong dua `data/egp.db` len Git.
- Fixture `tests/fixtures/golden/contracts_finder_v061.json` gom sau thong bao cong khai
  cua Contracts Finder, da co dinh de CI khong phu thuoc website that.
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

1. WP2: adapter nguon, parser va idempotency.
2. WP3: `crawl_tasks`, retry, checkpoint va resume.
3. WP4: Alembic migration co review tren ban sao `egp.db`.
4. WP5: golden-file test cho TBMT exporter.
5. WP6: FTS5 capability check, trigger thu cong va fallback search.

Khong dua Celery/Redis, RBAC/JWT, LLM/OCR hoac dashboard lon vao sprint nay.
