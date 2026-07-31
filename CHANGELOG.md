# Changelog

Tai lieu nay ghi lai nhung thay doi quan trong cua QI-Crawler theo tung phien ban.

## Chua phat hanh

- Add `QI-Crawler -adv` to show technical commands separately from beginner help.
- Add the `them-egp` preset for Vietnam e-GP and `kiem-tra-nguon` selector/session validation.
- Save the exact list URL reached by the user after manual login for later authenticated runs.
- Match e-GP detail links through stable URL markers while requiring validation after site changes.
- Add a T-7 SOP checkpoint for E-HSMT collection, keyword extraction and Excel handoff.
- Add Windows Unicode regression tests for accented `Lanh Binh Thang` and `Cap quang` data, including
  Excel round-trip preservation.
- Add tender line-item quantity storage with source location and extraction confidence.
- Read Contracts Finder OCDS `tender.items` quantities automatically when provided by the source.
- Add beginner commands `nhap-ton-kho` and `nhap-boq`; keep the old English names hidden and compatible.
- Reduce root help to daily-use commands with short ASCII Vietnamese descriptions.
- Add `requested_quantity_details` and `response_table` to the tender export.
- Add detailed `Response Table` and `QI Inventory` workbook sheets.
- Detect stock shortage, missing quantity, unmatched products and unit mismatch without false approval.
- Add an English QI inventory workbook template for first-time users.
- Convert source text, CLI messages, tests, and documentation to ASCII-safe text without Vietnamese
  diacritics.
- Make English the canonical language for product names and industry categories.
- Keep ASCII Vietnamese aliases and normalize accented user input, for example `cat` -> `sand`.
- Them lenh `theo-doi` de quet mot luot hoac chay lien tuc theo chu ky.
- Them `monitoring.example.yaml` cho danh sach tu khoa, nguon va thoi gian quet.
- Them bao cao Excel xep hang co hoi kha thi so bo.
- Cham diem theo do khop san pham, bang chung da xac minh, han nop va do day du du lieu.
- Khong danh dau kha thi so bo neu chua co bang chung nang luc da xac minh.

## 0.4.0 - 2026-07-31

### Them moi

- Ho tro `QI-Crawler -help`, `QI-Crawler -h` va `QI-Crawler help`.
- Hien thi danh sach lenh cung vi du co the sao chep cho nguoi moi.
- Them `keyword-groups.yaml` de quan ly nhom nganh, san pham va ten tuong duong.
- Tim khong phan biet chu hoa/thuong va dau tieng Viet.
- Mo rong tu khoa theo ten Viet, ten Anh, ten viet tat va bien the chinh ta.
- Them lenh `them-tu-khoa` de tu phan loai va cap nhat san pham moi.
- Them `pending_keywords` cho truong hop chua du can cu phan loai.
- Use English canonical categories (`Construction Materials`, `Information Technology`) with ASCII
  Vietnamese aliases for backward-compatible searches.
- Them kiem thu cho help, mo rong tu khoa, phan loai tu dong va hang cho xac nhan.

### Thay doi

- Doi ten san pham va CLI tu `egp-crawler` thanh `QI-Crawler`.
- Doi package Python tu `egp_crawler` thanh `qi_crawler`.
- Viet lai README va hop nhat tai lieu huong dan cho nguoi moi.
- Khong dung ten nhom nganh rong de tu nhan moi goi, nham giam ket qua sai.

### An toan

- Chi tu cap nhat tu khoa khi co tin hieu phan loai du ro.
- Tu khoa mo ho luon cho con nguoi xac nhan.
- Khong tu dich hoac tu tao ten san pham khi chua co can cu.

## 0.3.0 - 2026-07-31

### Them moi

- Thu thap goi con han tu UK Contracts Finder qua OCDS API.
- Them website tuy chinh bang URL trang danh sach.
- Cho phep nguoi dung tu dang nhap, nhap OTP/CAPTCHA va luu phien cuc bo.
- Tai su dung cookie/session ma khong luu mat khau.
- Them lenh tieng Viet: `bat-dau`, `tim-goi`, `xuat-bao-cao`, `danh-gia`, `them-nguon`,
  `dang-nhap`, `tim-tren-web`.
- Them doi chieu yeu cau voi bang chung nang luc.
- Them cong quyet dinh `GO`, `HOLD`, `NO-GO` va xac nhan doc lap.
- Them ty le du doan ho tro sang loc voi gioi han cho `HOLD` va `NO-GO`.
- Them migration cong don de bao toan database cu.

### Thay doi

- Don gian hoa quy trinh su dung va giam tai lieu/script demo trung lap.
- Bao ve `data/sessions/` va `data/sources/` khoi Git.

## 0.2.0

- Them tim kiem dong va phan trang Playwright theo selector cau hinh.
- Them tai file bang `expect_download()` va luu SHA-256.
- Them trang thai tai file, retry va manual review.
- Them import CSV/XLSX, kiem tra chat luong du lieu va reject file.
- Them luu HTML raw, content hash va thong ke crawl run.
- Them bao cao Excel nhieu sheet va gui SMTP tuy chon.
- Mo rong API, cau hinh, kiem thu va GitHub Actions.

## 0.1.0

- Khoi tao crawler Python bat dong bo va cau truc database ban dau.
