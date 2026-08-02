# QI-Crawler MVP

QI-Crawler la cong cu noi bo ho tro QI Technologies tim kiem, sang loc va theo doi co hoi dau thau.
Nguoi dung co the tim goi theo ten Viet/Anh, thu thap du lieu tu nguon cong khai hoac website can dang nhap,
xuat Excel va danh gia so bo kha nang dap ung.

> QI-Crawler khong tu nop ho so, khong vuot CAPTCHA va khong tao bang chung nang luc. Ket qua tim kiem,
> phan loai va diem uu tien luon can nguoi phu trach kiem tra truoc khi su dung. Diem khong phai xac suat
> trung thau va khong thay the quyet dinh tham du.

## Tinh nang hien tai

- Tim goi con han tren UK Contracts Finder.
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

Khi terminal hien `(.venv)`, kiem tra chuong trinh:

```powershell
QI-Crawler bat-dau
```

Neu `.venv` da ton tai, nhung lan sau chi can:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
```

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
QI-Crawler tim-goi -help
```

Khong go rieng `-help`, vi PowerShell yeu cau dong lenh bat dau bang ten chuong trinh.

## Quy trinh nhanh: tim va xuat Excel

### Tim goi tren Contracts Finder

```powershell
QI-Crawler tim-goi --tu-khoa "network switch" --so-luong 50
Copy-Item monitoring.example.yaml monitoring.yaml
QI-Crawler xep-hang
```

QI-Crawler chi luu cac goi con han trong pham vi du lieu da doc. Bang xep hang nam tai
`data/reports/co-hoi-uu-tien.xlsx`.

### Check tender quantity against QI inventory

Use [templates/qi-inventory-template.csv](templates/qi-inventory-template.csv) or the provided Excel
template and keep one stock item per row. Import it with:

```powershell
QI-Crawler nhap-ton-kho data\qi-inventory.xlsx
```

When the source provides structured line items, such as Contracts Finder OCDS `tender.items`,
QI-Crawler saves the requested quantity automatically. If the quantity is only available in a BOQ
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
QI-Crawler dang-nhap --ten egp-vietnam
```

Trong cua so trinh duyet do QI-Crawler mo, nguoi dung tu dang nhap, nhap OTP/CAPTCHA va di toi trang danh
sach goi thau. Quay lai terminal, nhan Enter de luu URL va phien dang nhap. Luon kiem tra selector truoc khi
thu thap:

```powershell
QI-Crawler kiem-tra-nguon --ten egp-vietnam
QI-Crawler tim-tren-web --ten egp-vietnam --tu-khoa "cap quang" --so-luong 100
QI-Crawler xuat-bao-cao --tep data\egp-cap-quang.xlsx
```

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

## Tai lieu va lich su phien ban

- [Huong dan su dung chi tiet](HUONG_DAN_SU_DUNG.md)
- [Lich su cap nhat](CHANGELOG.md)

## Kiem tra ky thuat

```powershell
python -m pytest -q
python -m ruff check src tests --no-cache
```

Bo kiem thu Windows co tinh huong rieng cho `Lanh Binh Thang` va `Cap quang` bang ky tu Unicode co dau. Bai
kiem thu xac nhan tu khoa duoc chuan hoa de tim kiem, dong thoi ten goi va ten ben moi thau van giu nguyen dau
khi xuat/nap lai Excel. GitHub Actions co the khac Windows ve font terminal; file Excel va logic so khop la
ket qua can doi chieu, khong danh gia bang hinh dang font trong terminal.
