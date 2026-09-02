# Changelog

Tai lieu nay ghi lai nhung thay doi quan trong cua QI-Crawler theo tung phien ban.

## Unreleased

## 0.9.0 - 2026-09-02

- WP-TB-BASIC-CRAWLER-03 merged controlled folder intake and operational
  revision transition: folder discovery is read-only until explicit Human
  confirmation; managed short names preserve original filenames/bytes; newer
  accepted revisions remain pending until adjacent previous/latest comparison
  and explicit activation; downgrade is forbidden and prior revisions remain
  readable. Real same-package PDF/DOCX restart/reopen and controlled export
  passed; genuine second-revision and foreign-reference evidence remain
  explicit gaps. No Team Bid release or pilot is implied.
- Bid Radar confirmed opportunities now hand off safely to Tender Workspace,
  preserving exact IB revisions and creating provisional PL cases without
  fabricating IB identities.
- Harden source integrity: preserve immutable raw HTML evidence, scope notice
  identity by source, and make parsed semantic change detection complete and
  deterministic.
- Bổ sung vận hành Workspace Team Bid domain-first: tìm đúng IB revision,
  dashboard exact-release, thêm/thay thế/correction có lịch sử append-only,
  integrity verification và export bảy zone an toàn, giữ nguyên Document Store
  bất biến.
- Them nhan dang va routing Excel KHMT/TBMT theo filename + schema + PL/IB,
  co human override append-only; TBMT duoc dua vao luong Opportunity
  source-neutral sau khi xac minh identity.
- Them adapter intake TBMT XLSX source-neutral theo IB Opportunity; xac nhan
  read-only tren workbook TBMT that bao phu cac dang identity da quan sat,
  giu nguyen revision HSMT (`-00` lan phat hanh dau, `-01` lan cap nhat sau
  chinh sua) va giu tach biet PL/IB. Luong da merge gom filter/search,
  Human Review persistence, confirmed XLSX va thin Bid Radar GUI.
- Hoan tat Business Fast-Track MI-0 -> MI-6 va xac nhan end-to-end bang workbook KHMT that `KHMT_19_8_2026.xlsx`.
- Real Golden Team Bid: import 413 goi, preset HCM/0-500 trieu loc 9 ung vien, Human Authority ghi 3 `CONFIRMED`, 6 `NEEDS_REVIEW`, 0 `REJECTED`.
- Xac minh `current_confirmed()` chi tra 3 goi da duoc con nguoi xac nhan; 6 goi `NEEDS_REVIEW` khong duoc xuat.
- Xac minh confirmed XLSX va 3 Legal DOCX mo lai dung PL/revision/source-row, khong cross-package contamination va khong mutate review history.
- Xac minh SHA-256 workbook nguon khong thay doi truoc/sau Real Golden; business data, acceptance DB va generated output khong duoc commit vao Git.
- Them Bid Radar GUI cho import KHMT, filter, Human Review va export, voi source-identity guard de chan export neu workbook tai cung duong dan da bi thay noi dung.
- WP-MI-TBMT-02C da merge: source-neutral TBMT delivery closure, KHMT Legal DOCX
  compatibility va vertical KHMT/TBMT acceptance da duoc ghi nhan; TBMT Legal
  DOCX va API integration van explicitly unsupported/future scope.
- Local Parent verification dat 628 tests passed / 628 collected; hosted CI
  dang trong temporary infrastructure waiver, khong claim CI PASS va official
  Team Bid release van bi block boi pending retro-CI.
- Local regression dat 448 tests; GitHub CI exact-head cua Real Golden PASS tren Code Quality, Ubuntu 3.12, Ubuntu 3.11 va Windows 3.12.
- Trusted Storage/Warehouse tiep tuc la lane uu tien: managed-copy behavior da ton tai, nhung SHA Vault, Canonical Package Shelf va Missing/Recoverable/Safe Restore chua duoc coi la da hoan tat.
- Them source-child lifecycle cho Attachment va TenderItem: snapshot thanh cong
  reconcile active membership, giu nguyen historical evidence, reactivation va
  chan auto-download/retry doi voi child da bien mat khoi nguon.

## 0.8.0 - 2026-08-23

- Dong bo version ung dung, giao dien va goi Windows theo mot nguon version
  canonical.
- Bo sung release metadata de doi chieu commit, Alembic head va hash artifact
  truoc khi phat hanh cho Team Bid.
- Khoa quy trinh kiem tra candidate tach biet khoi du lieu Team Bid va release
  chinh thuc.

## 0.7.1 - 2026-08-13

- Hoan tat goi phat hanh Windows cho Team Bid va dong bo version ung dung/installer.
- On dinh nen tang xu ly tai lieu va giao dien noi bo truoc giai doan phat trien tiep theo.
- Bo sung quy trinh tao Windows Setup de cai dat QI-Crawler khong can Python, VS Code hay Git.

## 0.6.1 - 2026-08-12

- Cai thien kha nang xu ly du lieu dau thau tu nhieu nguon va xuat bao cao theo mau chung.
- Bo sung kiem tra du lieu de ho tro van hanh an toan hon.
- Ho tro tai su dung phien dang nhap cuc bo khi crawl nguon da cau hinh.
- Bo sung quy trinh nang cap database cuc bo co sao luu va kiem tra tuong thich.
- Ho tro tim kiem SQLite FTS5 co fallback an toan va chuan hoa tu khoa tieng Viet.
- Chi tim kiem va xuat TBMT tu nguon dang bat; du lieu mau/nguon cu duoc sao luu va archive cuc bo truoc khi loai khoi tap van hanh.

## 0.6.0 - 2026-08-10

- Cap nhat chuc nang xu ly va xuat bao cao dau thau.
- Cai thien do on dinh, kiem thu va tai lieu van hanh.
- Bo sung cac nang cap ky thuat noi bo phuc vu phat trien MVP.

## 0.5.2 - 2026-08-10

- Them sheet dau tien `Ban tin dien tu` theo bieu mau TBMT 18 cot do QI cung cap.
- Giu lai `Notices`, `Response Table` va `QI Inventory` de khong anh huong quy trinh BOQ va ton kho.
- Lay cac truong co san tu du lieu da crawl; truong chua co hoac chua xac minh se de trong thay vi dien gia.
- Them dong ghi chu kiem tra nguon, bo loc, dong bang tieu de, xu ly xuong dong va lien ket nguon trong Excel.
- Them kiem thu ve thu tu cot, noi dung tieng Viet, gia goi thau va an toan xuat du lieu.

## Ke hoach phien ban tiep theo

- Xay dung Web UI cuc bo voi nut bam cho cac viec: dang nhap, tim goi, xep hang va xuat Excel.
- Them man hinh cau hinh de nguoi dung khong phai sua truc tiep `.env` hoac `.yaml` cho tac vu thong thuong.
- Them nut khoi dong mot lan tren Windows, tu kiem tra `.venv` va huong dan khi thieu thanh phan.
- Giu CLI va API lam nen tang cho van hanh ky thuat, Task Scheduler va tu dong hoa.
- Chi dua UI vao su dung noi bo sau khi kiem tra quyen truy cap, session dang nhap va cach hien thi loi.

## 0.5.1 - 2026-08-02

- Hien phien ban va tom tat thay doi moi ngay trong `QI-Crawler -help` cho nguoi moi.
- Hien them ghi chu ky thuat cua ban cap nhat trong `QI-Crawler -adv`.
- Dung chung mot nguon release highlights trong code de hai man hinh tro giup khong bi lech nhau.
- Them muc `Co gi moi` va quy tac cap nhat dong bo vao README va huong dan su dung.
- Them kiem thu bat buoc phien ban hien tai phai co trong `CHANGELOG.md`, huong dan, `-help` va `-adv`.
- API lay version truc tiep tu package thay vi ghi lap mot chuoi version rieng.
- Cong khai han che hien tai: MVP van can Terminal, `.venv` va file cau hinh cho mot so tac vu.
- Ghi nhan Web UI nut bam va cau hinh don gian la uu tien cua phien ban tiep theo.

## 0.5.0 - 2026-08-02

- Refocus the main MVP on opportunity collection, keyword screening, explainable scoring and ranking.
- Add `QI-Crawler xep-hang` and hide legacy GO/NO-GO analysis from beginner help and public API schema.
- Replace win-probability language with `Opportunity Priority Score` and statuses `PRIORITY`, `REVIEW`,
  `SKIP`, `INSUFFICIENT_DATA`.
- Add a seven-component 100-point framework with evidence, inventory, time, financial and SLA reasons.
- Add weighted keyword groups, synonyms, required `OR`, required `AND` and excluded `NOT` terms.
- Add `NEW_MATCH` and `CLOSING_SOON` alerts with an explicit next action in the ranked workbook.
- Parse location, sector, selection method and notice version from detail pages and structured sources.
- Open matched authenticated detail pages before saving metadata; incomplete records remain unranked.
- Deduplicate by notice code plus version while preserving revised notices.
- Normalize Vietnamese `d`/`D` with stroke correctly and preserve accented source text in Excel.
- Neutralize untrusted spreadsheet formula prefixes in CSV/XLSX exports.
- Remove the tracked sample capability file and ignore private evidence/data workbooks.

- Add `QI-Crawler -adv` to show technical commands separately from beginner help.
- Add the `them-egp` preset for Vietnam e-GP and `kiem-tra-nguon` selector/session validation.
- Save the exact list URL reached by the user after manual login for later authenticated runs.
- Match e-GP detail links through stable URL markers while requiring validation after site changes.
- Add a T-7 SOP checkpoint for E-HSMT collection, keyword extraction and Excel handoff.
- Add Windows Unicode regression tests for accented `Lanh Binh Thang` and `Cap quang` data, including
  Excel round-trip preservation.
- Add tender line-item quantity storage with source location and extraction confidence.
- Read structured tender line-item quantities automatically when provided by a source.
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

- Them luong crawl URL va luu du lieu nguon vao kho noi bo.
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
