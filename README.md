# QI-Crawler MVP

QI-Crawler la cong cu noi bo ho tro QI Technologies tim kiem, sang loc va theo doi co hoi dau thau.
Nguoi dung co the tim goi theo ten Viet/Anh, thu thap du lieu tu nguon cong khai hoac website can dang nhap,
xuat Excel va danh gia so bo kha nang dap ung.

> QI-Crawler khong tu nop ho so, khong vuot CAPTCHA va khong tao bang chung nang luc. Ket qua tim kiem,
> phan loai va diem uu tien luon can nguoi phu trach kiem tra truoc khi su dung. Diem khong phai xac suat
> trung thau va khong thay the quyet dinh tham du.

## Co gi moi trong 0.7.0

- Nen tang da san sang cho Team Bid quan ly tai lieu va kiem tra du lieu truoc khi phan tich noi dung.
- QI-Crawler giu nguyen nguyen tac fail-closed khi gap bao mat, CAPTCHA hoac phien dang nhap khong hop le.

## Co gi moi trong 0.6.1

- Them lenh `xuat-tbmt` de tao file trinh bay dung mau `Ban tin dien tu` 18 cot QI dang su dung.
- File chi hien mot sheet nghiep vu; sheet `__QI_META` duoc an de luu thong tin truy vet.
- Tien va ngay gio duoc ghi dung kieu Excel; dong loi duoc tach sang file `_rejects.xlsx`.
- Template `templates/TBMT_template_v1.xlsx` khong bi ghi de; file trung ten tu them `_v2`, `_v3`.
- Cac cot khong co du lieu xac minh duoc de trong; QI-Crawler khong chen so lieu gia.
- Ho tro ma dinh danh rieng cua tung website: goi khong co ma TBMT e-GP van duoc xuat khi co `source_notice_id` va URL nguon.
- Xuat TBMT phan biet `PASS`, `WARNING`, `REJECT`; canh bao van duoc dua vao Excel, chi ban ghi khong xac dinh duoc moi bi tach ra.
- Lenh cu `xuat-bao-cao` van giu cac sheet ky thuat de nhap BOQ va kiem tra ton kho.
- `QI-Crawler -help` chi hien cac lenh hang ngay de nguoi moi de doc.
- `QI-Crawler -adv` tap hop lenh cau hinh va van hanh ky thuat.
- Lich su thay doi nam trong `CHANGELOG.md`; huong dan co vi du nam trong `HUONG_DAN_SU_DUNG.md`.

Xem lich su day du trong [CHANGELOG.md](CHANGELOG.md). Xem vi du thao tac trong
[HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md).

## Rao can hien tai va huong phat trien UI

QI-Crawler 0.6.1 van la MVP dung dong lenh. Nguoi dung can kich hoat `.venv`, mo Terminal va chay lenh nhu:

```powershell
QI-Crawler dang-nhap --source egp
QI-Crawler tim-tren-web --ten egp --tu-khoa "network switch"
QI-Crawler xep-hang
```

Khong can chay truc tiep `python src/qi_crawler/cli.py`. Cac file `.env` va `.yaml` van can cho cau hinh ky
thuat, do do nhan su moi co the can nguoi van hanh ho tro trong lan dau.

Roadmap phien ban tiep theo la Web UI cuc bo co nut bam cho dang nhap, tim goi, xep hang, xem trang thai va
xuat Excel. CLI/API van duoc giu de chay lich va xu ly nang cao.

## Tinh nang hien tai

- Crawl cac website dau thau duoc cau hinh va luu du lieu vao kho noi bo.
- Co cau hinh nhanh cho e-GP Viet Nam va lenh kiem tra selector sau khi dang nhap.
- Ket noi trang danh sach goi thau khac bang URL.
- Cho phep nguoi dung tu dang nhap, nhap OTP/CAPTCHA va luu phien cuc bo.
- Tim bang ten Viet, ten Anh, ten viet tat va bien the chinh ta.
- Tu phan loai tu khoa moi theo nhom nganh voi hang cho xac nhan khi chua chac chan.
- Luu du lieu vao SQLite va xuat bao cao Excel.
- Read requested quantities from structured tender data or an imported BOQ Excel/CSV file.
- Import verified QI inventory and produce a quantity-based response table.
- Doc metadata chi tiet, nhan dien goi trung theo ma thong bao va phien ban.
- Loc theo nhom keyword co trong so, dieu kien `OR`, `AND` va keyword loai tru.
- Cham `Opportunity Priority Score` co giai thich tung thanh phan.
- Tra trang thai `PRIORITY`, `REVIEW`, `SKIP`, `INSUFFICIENT_DATA`.
- Canh bao co hoi moi phu hop va goi sap dong thau.
- Giu cac hang rao an toan: domain allowlist, robots.txt, rate limit va dung khi gap chan truy cap.

## Cai dat tren Windows

Mo thu muc du an bang VS Code, chon **Terminal > New Terminal**, roi chay tung dong:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

Khi terminal hien `(.venv)`, nang cap database truoc khi dung lan dau, roi khoi dong MVP:

```powershell
QI-Crawler db-upgrade
QI-Crawler bat-dau
```

Neu `.venv` da ton tai, nhung lan sau chi can:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
```

### Danh cho Team Bid tren Windows

Sau khi IT da cai dat QI-Crawler va tao `.venv`, nhan su Bid khong can mo VS Code hay go lenh Python:

```text
double-click QI-Crawler.bat
-> chon chuc nang
-> dan URL
-> xem ket qua
-> xuat va kiem tra Excel
```

File `QI-Crawler.bat` tu mo dung thu muc du an, kich hoat `.venv` va chay `QI-Crawler menu`.
Neu launcher bao thieu `.venv` hoac lenh QI-Crawler, hay chup man hinh va gui IT; khong tu xoa database.

Ban thu nghiem giao dien desktop PySide6 co the duoc IT khoi dong bang:

```powershell
python -m qi_crawler.gui
```

GUI gom cac tab quet danh sach, tim kiem, xuat TBMT, crawl mot URL, dang nhap va xem nhat ky.
Day van la prototype; chua phai file EXE/installer. Tat ca thao tac tiep tuc dung crawler, database va exporter
chung voi CLI.

## Tro giup

Xem danh sach lenh va vi du:

```powershell
QI-Crawler -help
```

Nguoi van hanh ky thuat xem rieng cac lenh nang cao bang:

```powershell
QI-Crawler -adv
```

Cung co the dung:

```powershell
QI-Crawler -h
QI-Crawler help
QI-Crawler scan -help
QI-Crawler tim-goi -help
```

Khong go rieng `-help`, vi PowerShell yeu cau dong lenh bat dau bang ten chuong trinh.

## Quy trinh nhanh cho Bid Team

Quet trang danh sach Coteccons (toi da 3 **trang danh sach**, khong phai 3 goi):

```powershell
QI-Crawler scan "https://ebidding.coteccons.vn/Index" --max-pages 3
QI-Crawler tim-goi --tu-khoa "chong tham" --so-luong 50
QI-Crawler xuat-tbmt
```

Neu chi co mot URL chi tiet, dung:

```powershell
QI-Crawler crawl "https://ebidding.coteccons.vn/Index/ChiTiet/2607301"
QI-Crawler tim-goi --tu-khoa "chong tham" --so-luong 50
QI-Crawler xuat-tbmt
```

Quy trinh de xuat: `scan -> xem ket qua -> tim-goi -> xuat-tbmt -> kiem tra file Excel`.
`scan` va `crawl` ket noi website; `tim-goi` chi tim trong database da luu. QI-Crawler khong vuot
CAPTCHA, HTTP 403 hoac bien phap bao mat. Khi hien `HUMAN_REQUIRED`, nguoi dung phai dang nhap
hoac kiem tra chan truy cap truoc khi tiep tuc.

`xuat-tbmt` mac dinh gom tat ca goi hop le crawl trong ngay; dung `--all` cho toan bo kho hoac
`--run-id 123` de xuat mot lan crawl cu the.

### Check tender quantity against QI inventory

Use [templates/qi-inventory-template.csv](templates/qi-inventory-template.csv) or the provided Excel
template and keep one stock item per row. Import it with:

```powershell
QI-Crawler nhap-ton-kho data\qi-inventory.xlsx
```

When the source provides structured line items, QI-Crawler saves the requested quantity automatically.
If the quantity is only available in a BOQ
Excel/CSV attachment, import that file using the internal notice `id` shown in the report:

```powershell
QI-Crawler nhap-boq 12 data\tender-boq.xlsx
QI-Crawler xuat-bao-cao --tep data\tender-stock-response.xlsx
```

The exported workbook contains:

- `Notices`: one row per tender, including `requested_quantity_details` and `response_table`.
- `Response Table`: one row per requested item with required, available, shortage and status.
- `QI Inventory`: the verified stock snapshot used for the comparison.

Only inventory rows with `Verified=yes` are used. Missing quantity, unit mismatch and uncertain product
matching are sent to manual review. PDF/Word quantity extraction is not automatic in this MVP; import its
reviewed BOQ as Excel/CSV instead.

### Tim tren e-GP Viet Nam sau khi dang nhap

Tao cau hinh e-GP co san:

```powershell
QI-Crawler them-egp
QI-Crawler dang-nhap --source egp
```

Trong cua so trinh duyet do QI-Crawler mo, nguoi dung tu dang nhap, nhap OTP/CAPTCHA va di toi trang danh
sach goi thau. Quay lai terminal, nhan Enter de luu URL va phien dang nhap tai
`data/sessions/egp_storage_state.json`. `crawl` tu dung lai session nay cho URL e-GP; QI-Crawler khong luu
mat khau. Luon kiem tra selector truoc khi thu thap:

```powershell
QI-Crawler kiem-tra-nguon --ten egp
QI-Crawler tim-tren-web --ten egp --tu-khoa "cap quang" --so-luong 100
QI-Crawler xuat-bao-cao --tep data\egp-cap-quang.xlsx
```

Hoac crawl truc tiep URL chi tiet sau khi dang nhap:

```powershell
QI-Crawler crawl "https://muasamcong.mpi.gov.vn/..."
QI-Crawler xuat-tbmt
```

Neu session het han va website chuyen ve trang login, crawler dung va yeu cau chay lai
`QI-Crawler dang-nhap --source egp`. QI-Crawler bao `EGP_SESSION_EXPIRED`, dung an toan va khong tu vuot
CAPTCHA, OTP, 403 hay token bao mat.

Cau hinh e-GP uu tien cac dau hieu URL chi tiet on dinh nhu `contractor-selection`, `notifyNo` va
`step=tbmt`. Giao dien e-GP co the thay doi hoac tam dung mot thanh phan; vi vay `kiem-tra-nguon` la buoc bat
buoc trong van hanh. Neu ket qua la `Chua san sang`, dang nhap lai, di dung trang danh sach va khong crawl
cho den khi nguoi ky thuat cap nhat selector.

### Tim tren website can dang nhap khac

Khai bao URL trang danh sach mot lan:

```powershell
QI-Crawler them-nguon `
  --ten muasamcong `
  --url "URL_TRANG_DANH_SACH_GOI_THAU"
```

Mo trinh duyet do QI-Crawler quan ly va tu dang nhap:

```powershell
QI-Crawler dang-nhap --ten muasamcong
```

Sau khi dang nhap, di toi trang danh sach, quay lai terminal va nhan Enter. Tiep theo:

```powershell
QI-Crawler tim-tren-web --ten muasamcong --tu-khoa "sand" --so-luong 100
QI-Crawler xuat-bao-cao --tep data\sand-tenders.xlsx
```

Phien dang nhap duoc luu trong `data/sessions/`, khong duoc dua len Git. QI-Crawler khong luu mat khau va
khong tu vuot CAPTCHA. Website co cau truc dac biet co the can cau hinh selector rieng.

## Moc T-7 trong SOP

Tai T-7 ngay truoc han nop, nhan su phu trach can:

1. Chay QI-Crawler tren nguon e-GP da kiem tra selector.
2. Tai cac E-HSMT va tep dinh kem ma tai khoan duoc phep truy cap.
3. Boc tach tu khoa, xuat Excel va doi chieu du phien ban tai lieu.
4. Ban giao bao cao Excel, thu muc E-HSMT, nhat ky chay va danh muc ho so thieu cho cac bo phan tiep theo.

Quy trinh nay da duoc them vao ban SOP moi trong thu muc `docs/`; tai lieu goc khong bi ghi de.

## Tu khoa thong minh va nhom nganh

Tu dien [keyword-groups.yaml](keyword-groups.yaml) chua nhom nganh, ten san pham va ten tuong duong.

English is the canonical language in the taxonomy. For example, `cat`, `cat trang`, and equivalent accented
Vietnamese input are normalized and expanded to:

- `sand`, `cat`, `cat trang`, `white sand`, `silica sand`;
- category `Construction Materials`, with `Vat lieu xay dung/VLXD` as aliases.

Similarly, `mo dun 5G` is expanded to:

- `mo dun 5G`, `module 5G`, `modul 5G`, `5G module`;
- category `Information Technology`, with `Cong nghe thong tin/CNTT` as aliases.

Categories are used for classification and explanation, not to collect every tender in a broad industry.
Searching for `sand` therefore does not automatically collect steel or brick tenders.

### Them va tu phan loai tu khoa moi

```powershell
QI-Crawler them-tu-khoa `
  --tu-khoa "cap mang ngoai troi" `
  --ten-khac "outdoor network cable" `
  --ten-khac "outdoor LAN cable" `
  --mo-ta "Cap ket noi switch, router va thiet bi mang"
```

Neu tin hieu du ro, tu khoa duoc cap nhat vao dung nhom. Neu chua ro, no duoc dua vao `pending_keywords`.
Nguoi phu trach co the xac nhan thu cong:

```powershell
QI-Crawler them-tu-khoa `
  --tu-khoa "ten san pham" `
  --ten-khac "ten tieng Anh" `
  --nhom "Information Technology"
```

## Theo doi tu dong va xep hang co hoi

Tao cau hinh ca nhan tu file mau:

```powershell
Copy-Item monitoring.example.yaml monitoring.yaml
```

Mo `monitoring.yaml` va sua `keyword_groups`, `required_any`, `required_all` va `excluded_keywords`.
Chay mot luot de tao bang uu tien:

```powershell
QI-Crawler xep-hang
```

Neu ket qua dung, de chuong trinh chay theo chu ky:

```powershell
QI-Crawler theo-doi
```

Giu terminal mo va cau hinh Windows khong tu Sleep. Bao cao xep hang mac dinh nam tai
`data/reports/co-hoi-uu-tien.xlsx`. Voi van hanh lau dai, nen dung `--mot-lan` cung Windows Task Scheduler
thay vi phu thuoc vao mot terminal luon mo.

Diem toi da 100: keyword/linh vuc 30, san pham/giai phap 20, hop dong tuong tu 20, cung ung/ton kho 10,
tai chinh/thanh toan 10, thoi gian 5 va dia diem/SLA 5. Bao cao ghi ro keyword khop, bang chung duoc dung,
du lieu thieu, rui ro, canh bao va hanh dong tiep theo.

Neu thieu ma thong bao, ten goi, gia, deadline, URL hoac thong tin chi tiet, QI-Crawler tra
`INSUFFICIENT_DATA` va de trong diem. Nguoi dung phai bo sung metadata truoc khi xep hang.

## Gioi han MVP

MVP chi sang loc co hoi. Cac lenh compliance cu duoc giu an de nghien cuu ky thuat, khong nam trong giao dien
nguoi moi va khong duoc dung de tu ket luan ho so dat ky thuat. Chi tai/phan tich sau E-HSMT cho danh sach
`PRIORITY` da duoc chuyen gia thau chon.

## Du lieu va bao mat

Khong dua cac noi dung sau len GitHub hoac gui qua email/chat:

- `data/sessions/`: cookie va token phien dang nhap;
- `.env`, `config.yaml`: cau hinh cuc bo hoac secret;
- database va du lieu dau ra noi bo;
- tai lieu nang luc hoac ho so du thau chua duoc phep chia se.

File `data/company-evidence.*`, `data/*.xlsx` va `data/*.csv` duoc bo qua boi Git. Luu bang chung that o thu
muc rieng ngoai repository, chi import vao database cuc bo.

Database mac dinh van dung `data/egp.db` de bao toan du lieu tu phien ban cu. Day chi la ten file tuong thich,
khong phai ten san pham hien tai.

Neu phien ban moi yeu cau nang cap schema, dong QI-Crawler va chay `QI-Crawler db-upgrade`. Lenh tao backup
trong `data/backups/` truoc khi nang cap; khong can tu chay `alembic stamp`.

## Tai lieu va lich su phien ban

- [Huong dan su dung chi tiet](HUONG_DAN_SU_DUNG.md)
- [Lich su cap nhat](CHANGELOG.md)

### Quy tac cap nhat tai lieu

Moi tinh nang, lenh, canh bao, thay doi ket qua hoac ghi chu van hanh moi phai duoc cap nhat o cac noi phu hop:

1. `CHANGELOG.md`: ghi day du thay doi theo phien ban.
2. `HUONG_DAN_SU_DUNG.md`: giai thich bang vi du cho nguoi su dung.
3. `QI-Crawler -help`: chi giu cac lenh hang ngay; cap nhat khi luong thao tac doi.
4. `QI-Crawler -adv`: cap nhat khi them, doi hoac bo lenh ky thuat.

Khong lap lai changelog dai trong man hinh Terminal; nguoi dung xem chi tiet trong tai lieu.

## Kiem tra ky thuat

```powershell
python -m pytest -q
python -m ruff check src tests --no-cache
```

Bo kiem thu Windows co tinh huong rieng cho `Lanh Binh Thang` va `Cap quang` bang ky tu Unicode co dau. Bai
kiem thu xac nhan tu khoa duoc chuan hoa de tim kiem, dong thoi ten goi va ten ben moi thau van giu nguyen dau
khi xuat/nap lai Excel. GitHub Actions co the khac Windows ve font terminal; file Excel va logic so khop la
ket qua can doi chieu, khong danh gia bang hinh dang font trong terminal.
