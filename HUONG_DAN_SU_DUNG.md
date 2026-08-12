# Huong dan su dung QI Tender Assistant MVP

## 1. MVP lam duoc gi?

MVP ho tro bon viec:

1. Crawl trang goi thau tu website duoc phep truy cap.
2. Luu thong tin vao database noi bo.
3. Tim lai trong kho va xuat danh sach ra Excel de trinh.
4. Cham diem va xep hang co hoi, kem ly do de nguoi phu trach quyet dinh.

MVP khong tu nop ho so, khong vuot CAPTCHA va khong tu xac nhan doanh nghiep du dieu kien phap ly.

## 2. Mo chuong trinh

Trong terminal VS Code, chay tung dong:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
QI-Crawler db-upgrade
QI-Crawler bat-dau
```

Neu terminal hien `>>`, nhan `Ctrl+C` roi nhap lai lenh.

## 3. Crawl va tim goi thau

```powershell
QI-Crawler crawl "https://ebidding.coteccons.vn/Index/ChiTiet/2607301"
QI-Crawler tim-goi --tu-khoa "chong tham"
```

Tuy chon:

```powershell
QI-Crawler tim-goi `
  --tu-khoa "wireless access point" `
  --tu-ngay 2026-01-01 `
  --so-luong 50
```

`crawl` ket noi website va luu du lieu. `tim-goi` chi tim trong database da luu, khong goi mang.

Chi cac nguon dang `enabled` trong `config.yaml` moi duoc hien trong `tim-goi` va `xuat-tbmt`.
Nguoi van hanh co the archive du lieu mau/nguon cu sau khi da kiem tra backup bang lenh ky thuat
`QI-Crawler clean-legacy-sources`; lenh nay khong xoa du lieu e-GP/Coteccons hop le.

## 4. Xuat file TBMT de trinh

```powershell
QI-Crawler xuat-tbmt
```

Hoac chon ten file:

```powershell
QI-Crawler xuat-tbmt --tep "C:\Users\Admin\Documents\TBMT-network.xlsx"
```

Vi du loc goi co tu khoa va to mau canh bao:

```powershell
QI-Crawler xuat-tbmt --tu-khoa "cap quang" --tu-ngay 2026-08-01 --den-ngay 2026-08-10 --to-canh-bao
```

Mac dinh file co ten `TBMT_ngay_thang_nam.xlsx` trong `data\reports`. Neu ten da ton tai, QI-Crawler
tu tao `_v2`, `_v3`; khong ghi de file cu.

Mac dinh, `xuat-tbmt` lay tat ca goi hop le da crawl trong ngay hien tai, ke ca khi den tu nhieu
`crawl run`. Dung `--all` de xuat toan bo kho, hoac `--run-id 123` de chi xuat mot lan crawl:

```powershell
QI-Crawler xuat-tbmt --all
QI-Crawler xuat-tbmt --run-id 123
```

### Kiem tra du lieu khi xuat

- `PASS`: du lieu chinh day du, duoc xuat Excel.
- `WARNING`: thieu truong phu nhu dia chi, du an, nguon von, gia, bao dam du thau hoac thoi gian hop dong;
  van duoc xuat Excel de nguoi phu trach doi chieu.
- `REJECT`: thieu ten goi, URL nguon, hoac thieu ca ma TBMT va ma rieng cua website; duoc dua vao
  `data\rejects\..._rejects.xlsx`.

Vi du, goi tren Coteccons khong co ma `IB...` van duoc xuat neu co URL va ma rieng `2607301`. O **GOI THAU**
se hien `Ma nguon: COTEC-2607301. Nguon: Coteccons eBidding`. O cot O luon la URL nguon de mo lai va doi chieu.

Khi mo file, sheet dau tien la `Ban tin dien tu`. Sheet nay co 18 cot theo mau TBMT, gom ben moi thau,
du an, goi thau, nguon von, gia goi thau, phuong thuc/hinh thuc lua chon, cac moc phat hanh - dong thau -
mo thau va thoi gian thuc hien hop dong.

Neu website khong cung cap mot truong, hoac QI-Crawler chua xac minh duoc, o do se de trong. Khong tu thay
o trong bang `0`, `20`, `23` hoac mot gia tri uoc doan. Nguoi phu trach can bam link nguon va doi chieu thong bao,
E-HSMT goc truoc khi trinh bao cao.

File `xuat-tbmt` chi hien sheet `Ban tin dien tu`. Sheet `__QI_META` duoc an de luu thong tin truy vet,
khong phai sheet nghiep vu. Header nam o dong 10, du lieu bat dau tu dong 11, dung 18 cot A:R.

Neu can file ky thuat gom BOQ va ton kho, dung lenh cu:

```powershell
QI-Crawler xuat-bao-cao
```

File ky thuat giu cac sheet:

- `Notices`: du lieu crawler day du va ma `id` dung khi nhap BOQ.
- `Response Table`: bang dap ung so luong chi tiet.
- `QI Inventory`: ton kho QI da xac minh.

Cac cot quan trong:

- `title`: ten goi.
- `buyer`: don vi mua sam.
- `package_price` va `currency`: gia tri uoc tinh.
- `closing_at`: han phan hoi.
- `location`, `sector`, `selection_method`: dia diem, linh vuc va phuong thuc lua chon.
- `notice_version`: phien ban thong bao; dung cung `notice_code` de tranh trung.
- `source_url`: trang thong bao goc.
- `source_kind`: nguon du lieu.
- `requested_quantity_details`: ten hang, so luong va don vi QI-Crawler doc duoc.
- `response_table`: tom tat tinh trang dap ung ton kho cua tung goi.

File Excel co them sheet `Response Table`. Day la bang dap ung chi tiet, gom so luong yeu cau,
so luong ton, phan thieu, SKU duoc ghep va nguon cua con so.

## 4A. Import ton kho QI va kiem tra so luong

Mo file mau `qi-inventory-template.xlsx`, hoac sao chep
`templates\qi-inventory-template.csv`. Moi mat hang de tren mot dong va dung cac cot sau:

- `SKU`: ma hang QI duy nhat; bat buoc.
- `Product Name`: ten san pham chuan bang tieng Anh; bat buoc.
- `Aliases`: cac ten tuong duong, ngan cach bang dau cham phay.
- `Quantity Available`: so luong ton co the su dung; bat buoc va khong duoc am.
- `Unit`: don vi, vi du `pieces`, `sets`, `kg`, `tonnes`, `metres`.
- `Warehouse`: vi tri kho.
- `Verified`: chi dien `yes` sau khi da kiem tra so ton thuc te.

Lenh import ngan gon:

```powershell
QI-Crawler nhap-ton-kho data\qi-inventory.xlsx
```

### Vi du day du 1 - Import file Excel nam ngoai thu muc du an

Gia su file ton kho duoc luu tai:

```text
C:\Users\Admin\Documents\QI Data\qi-stock.xlsx
```

File can co cac cot sau:

```text
SKU,Product Name,Aliases,Quantity Available,Unit,Warehouse,Verified
RTR-5G-001,5G Router,router 5g; cellular router,10,pieces,Main Warehouse,yes
SAND-W-001,White Sand,sand; silica sand; cat trang,25,tonnes,Materials Yard,yes
```

Trong VS Code, mo Terminal. Neu chua thay `(.venv)`, chay:

```powershell
.\.venv\Scripts\Activate.ps1
```

Sau do import file bang dung lenh:

```powershell
QI-Crawler nhap-ton-kho "C:\Users\Admin\Documents\QI Data\qi-stock.xlsx"
```

Dau ngoac kep la bat buoc khi duong dan co khoang trang, vi du thu muc `QI Data`.
Neu thanh cong, terminal se hien ket qua tuong tu:

```text
Inventory import completed: rows=20, inserted=18, updated=2, rejected=0.
```

Y nghia:

- `rows=20`: QI-Crawler da doc 20 dong;
- `inserted=18`: them moi 18 mat hang;
- `updated=2`: cap nhat 2 mat hang da co cung SKU;
- `rejected=0`: khong co dong loi.

Neu `rejected` lon hon `0`, kiem tra lai `SKU`, `Product Name`, `Quantity Available` va dam bao so luong
khong am.

### Vi du day du 2 - Import file nam trong thu muc QI-Crawler

Tao thu muc `data\imports\inventory`, sau do chep file vao:

```text
data\imports\inventory\qi-stock-2026-07-31.xlsx
```

Chay:

```powershell
QI-Crawler nhap-ton-kho "data\imports\inventory\qi-stock-2026-07-31.xlsx"
```

Sau khi import ton kho, xuat bao cao:

```powershell
QI-Crawler xuat-bao-cao --tep "data\tender-stock-response.xlsx"
```

Mo file vua tao va xem sheet `Response Table` de kiem tra so luong yeu cau, so ton va phan con thieu.

QI-Crawler tu doc so luong khi website co du lieu cau truc. Neu so luong chi nam trong BOQ Excel/CSV,
tim `id` noi bo cua goi thau trong sheet `Notices`, sau do chay:

```powershell
QI-Crawler nhap-boq 12 data\tender-boq.xlsx
QI-Crawler xuat-bao-cao --tep data\tender-stock-response.xlsx
```

### Vi du day du 3 - Import BOQ tu thu muc Documents

1. Chay `QI-Crawler xuat-bao-cao` va mo sheet `Notices`.
2. Tim cot `id` cua goi thau. Gia su goi can kiem tra co `id=12`.
3. Luu file BOQ tai `C:\Users\Admin\Documents\QI Data\tender-12-boq.xlsx`.
4. Chay lenh:

```powershell
QI-Crawler nhap-boq 12 "C:\Users\Admin\Documents\QI Data\tender-12-boq.xlsx"
```

5. Xuat lai bao cao:

```powershell
QI-Crawler xuat-bao-cao --tep "data\tender-12-response.xlsx"
```

6. Mo `data\tender-12-response.xlsx` va kiem tra ba sheet:

- `Notices`: tom tat goi thau va cot `response_table`;
- `Response Table`: tung san pham, so luong yeu cau, so ton va so con thieu;
- `QI Inventory`: du lieu ton kho duoc dung de doi chieu.

Dung `templates\tender-boq-template.csv` lam file BOQ mau. Cac cot gom:

```text
Item Code,Product Name,Quantity,Unit,Specification
1,5G Router,25,pieces,Three antenna ports
2,Network Switch,10,pieces,24 Gigabit ports
```

Cach doc trang thai:

- `MEETS_STOCK`: ton kho da xac minh du so luong.
- `STOCK_SHORTAGE`: da tim thay hang nhung van thieu so luong.
- `REVIEW_REQUIRED_QUANTITY`: chua doc duoc so luong yeu cau.
- `REVIEW_UNIT_MISMATCH`: don vi goi thau khac don vi ton kho.
- `NOT_IN_VERIFIED_STOCK`: khong tim thay mat hang ton kho da xac minh du tuong dong.
- `NO_QUANTITY_DATA`: goi thau chua co du lieu so luong chi tiet.

Khong dung trang thai tren nhu phe duyet cuoi cung neu chua kiem tra file ton kho moi nhat, phien ban BOQ,
hang da giu cho don khac, lich giao hang va tai lieu goc. MVP chua tu doc BOQ PDF/Word; can chuyen va
kiem tra du lieu sang Excel/CSV truoc khi import.

### Neu file la catalog san pham

Catalog PDF/Word nen luu tai `data\imports\catalogs`, vi du:

```text
data\imports\catalogs\airpro-product-guide-2026.pdf
```

MVP hien tai chua co lenh import catalog PDF/Word tu dong. Neu catalog la Excel va co so ton thuc te,
hay tao mot sheet theo dung cac cot ton kho roi chay:

```powershell
QI-Crawler nhap-ton-kho "C:\Users\Admin\Documents\QI Data\product-catalog-stock.xlsx"
```

Neu catalog chi chua thong so ky thuat va khong co so ton, khong dien thong so do thanh
`Quantity Available`. Ton kho va catalog ky thuat la hai nguon du lieu khac nhau.

## 5. Chuan bi du lieu nang luc QI

Bang chung that khong de trong repository. Tao file rieng, vi du:

```text
C:\Users\Admin\Documents\QI Private\company-evidence.csv
```

Cac cot:

```text
evidence_code,title,evidence_type,description,keywords,source_path,valid_until,verified
```

`evidence_type` nen dung mot trong cac nhom:

- `product`, `solution`, `manufacturer`: san pham/giai phap QI co the cung cap;
- `contract`, `project`, `reference`: hop dong hoac du an tuong tu;
- `supply`, `support`, `service`: kha nang cung ung va ho tro;
- `financial`, `payment`: bang chung tai chinh;
- `location`, `sla`, `delivery`: dia ban va SLA.

Nhap bang chung bang lenh nang cao:

```powershell
QI-Crawler import-evidence "C:\Users\Admin\Documents\QI Private\company-evidence.csv"
```

Chi dat `verified=true` sau khi da kiem tra tai lieu goc va hieu luc. Git bo qua
`data/company-evidence.*`, `data/*.csv` va `data/*.xlsx` de tranh lo du lieu noi bo.

## 6. Tao bang xep hang co hoi

Sao chep file cau hinh mau:

```powershell
Copy-Item monitoring.example.yaml monitoring.yaml
```

Sua cac nhom trong `monitoring.yaml`, sau do chay:

```powershell
QI-Crawler xep-hang
```

Ket qua mac dinh: `data\reports\co-hoi-uu-tien.xlsx`.

## 7. Cach doc Opportunity Priority Score

Diem toi da 100:

- keyword/linh vuc: 30;
- san pham hoac giai phap phu hop: 20;
- hop dong/du an tuong tu: 20;
- cung ung, ton kho va ho tro hang: 10;
- tai chinh va dieu kien thanh toan: 10;
- thoi gian con lai: 5;
- dia diem va SLA: 5.

Trang thai dau ra:

- `PRIORITY` (75-100): uu tien chuyen cho chuyen gia thau/Presales;
- `REVIEW` (55-74): can kiem tra them;
- `SKIP` (duoi 55 hoac khop keyword loai tru): bo qua/chi theo doi;
- `INSUFFICIENT_DATA`: thieu metadata quan trong, chua duoc xep hang.

Day la diem uu tien co hoi, khong phai xac suat trung thau.

## 8. Quy trinh MVP khuyen nghi

1. Crawler danh sach lon, vi du 1.000 goi.
2. Keyword duong/am giu lai cac goi lien quan.
3. `xep-hang` chon khoang 20-30 goi dang xem.
4. Nguoi phu trach kiem tra metadata va ly do cham diem.
5. Chi tai/phan tich sau E-HSMT cho 5-10 goi `PRIORITY` da duoc chon.
6. Chuyen gia thau quyet dinh goi nao chinh thuc bat dau.

## 9. Website can dang nhap hoac xac thuc

### Cach nhanh cho e-GP Viet Nam

Chay lan luot:

```powershell
QI-Crawler them-egp
QI-Crawler dang-nhap --source egp
```

Trinh duyet se mo. Nguoi dung tu dang nhap, nhap OTP/CAPTCHA va di den trang hien danh sach goi thau. Khi
da thay danh sach, quay lai terminal va nhan Enter. QI-Crawler se luu phien cuc bo tai
`data\sessions\egp_storage_state.json`, khong luu mat khau va ghi nho URL hien tai.

Kiem tra cau truc trang truoc khi tim:

```powershell
QI-Crawler kiem-tra-nguon --ten egp
```

Chi khi terminal bao `Nguon da san sang de tim goi`, moi chay:

```powershell
QI-Crawler tim-tren-web --ten egp --tu-khoa "cap quang" --so-luong 100
QI-Crawler xuat-bao-cao --tep data\egp-cap-quang.xlsx
```

Neu da co URL goi thau, crawl bang chinh session da luu:

```powershell
QI-Crawler crawl "https://muasamcong.mpi.gov.vn/..."
QI-Crawler xuat-tbmt
```

Neu session het han va website chuyen ve trang login, crawler dung va yeu cau chay lai
`QI-Crawler dang-nhap --source egp`. QI-Crawler bao `EGP_SESSION_EXPIRED`, dung an toan va khong tu vuot
CAPTCHA, OTP, 403 hay token bao mat.

Neu terminal bao `Chua san sang`, khong tiep tuc crawl. Hay dang nhap lai, di dung trang danh sach va nho
nguoi ky thuat cap nhat selector neu e-GP da thay doi giao dien.

### Buoc 1 - Them nguon

Sao chep URL cua trang hien thi danh sach goi thau:

```powershell
QI-Crawler them-nguon `
  --ten muasamcong `
  --url "URL_TRANG_DANH_SACH_GOI_THAU"
```

Ten nguon nen ngan, khong dau, vi du `muasamcong`, `portal-a`, `khach-hang-b`.

### Buoc 2 - Dang nhap thu cong

```powershell
QI-Crawler dang-nhap --ten muasamcong
```

Mot cua so Chromium se mo. Ban tu thuc hien:

1. Nhap tai khoan va mat khau.
2. Nhap OTP hoac CAPTCHA neu website yeu cau.
3. Di toi dung trang danh sach goi thau.
4. Quay lai terminal va nhan Enter.

MVP chi luu cookie/session cuc bo tai `data\sessions`. Thu muc nay khong duoc dua len Git.
Khong gui file session qua email/chat vi no co the cho phep truy cap tai khoan trong thoi gian con hieu luc.

### Buoc 3 - Tim tren phien da dang nhap

```powershell
QI-Crawler tim-tren-web `
  --ten muasamcong `
  --tu-khoa "switch" `
  --so-luong 50
```

Sau do xuat Excel:

```powershell
QI-Crawler xuat-bao-cao
```

Neu website dang xuat hoac bao phien het han, chay lai `dang-nhap`. MVP se dung neu gap CAPTCHA,
HTTP 403/429 hoac robots.txt khong cho phep tu dong truy cap.

### Gioi han cua che do tu dong

MVP tim keyword tren danh sach, sau do mo trang chi tiet cua ket qua phu hop de doc ma goi, chu dau tu/ben
moi thau, gia, ngay dang, deadline, dia diem, linh vuc, phuong thuc va phien ban. Neu trang chi tiet khong
doc duoc, ban ghi van duoc luu nhung se mang `INSUFFICIENT_DATA`. Website co iframe, API noi bo hoac nut
phan trang rieng co the can cap nhat selector; khong co parser duy nhat chinh xac tren moi website.

## 10. Vi du thuc hanh danh cho nguoi moi

Truoc khi lam vi du, hay mo dung thu muc du an trong VS Code, chon **Terminal > New Terminal**, roi chay:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
```

Khi thay `(.venv)` o dau dong terminal, chuong trinh da san sang.

### Vi du A - Crawl va tim thiet bi mang

Muc tieu: doc mot goi tu website duoc phep, tim lai trong kho va xuat danh sach ra Excel.

**Buoc 1:** crawl trang chi tiet:

```powershell
QI-Crawler crawl "https://example-tender.com/tenders/123"
```

**Buoc 2:** tim trong kho noi bo:

```powershell
QI-Crawler tim-goi --tu-khoa "network switch" --so-luong 50
```

**Buoc 3:** xuat Excel:

```powershell
QI-Crawler xuat-bao-cao --tep data\bao-cao-switch.xlsx
```

**Buoc 4:** trong Explorer cua VS Code, mo thu muc `data`, sau do mo file `bao-cao-switch.xlsx`.
Kiem tra lan luot `title`, `closing_at`, `package_price` va `source_url`. Bam `source_url` de doc thong bao goc
truoc khi trinh cap quan ly.

### Vi du B - Tim goi cho san pham Wi-Fi

Gia su QI co access point Wi-Fi 6, ho tro PoE va quan ly tap trung. Khong nen tim bang mot cau qua dai.
Hay tim tung nhom tu khoa:

```powershell
QI-Crawler tim-goi --tu-khoa "WiFi 6 access point" --so-luong 50
QI-Crawler tim-goi --tu-khoa "wireless network equipment" --so-luong 50
QI-Crawler tim-goi --tu-khoa "managed wireless LAN" --so-luong 50
QI-Crawler xuat-bao-cao --tep data\bao-cao-wifi.xlsx
```

Cac ket qua duoc luu chung trong database; chuong trinh khong tao ban ghi trung khi cung mot goi duoc tim thay nhieu lan.
Sau khi xuat Excel, nguoi phu trach van phai mo ho so goc de kiem tra so luong, chung chi, bao hanh, thoi han va dia diem giao hang.

### Vi du C - Website can dang nhap

Gia su trang danh sach goi thau sau khi dang nhap co dia chi:
`https://example-tender.com/tenders/list`. Hay thay dia chi mau bang URL that cua website ban duoc phep truy cap.

**Buoc 1 - Khai bao website mot lan:**

```powershell
QI-Crawler them-nguon --ten example-tender --url "https://example-tender.com/tenders/list"
```

Neu thanh cong, terminal se huong dan chay `dang-nhap`.

**Buoc 2 - Tu dang nhap:**

```powershell
QI-Crawler dang-nhap --ten example-tender
```

Mot cua so trinh duyet mo ra. Ban nhap tai khoan, mat khau, OTP hoac CAPTCHA nhu binh thuong. Sau khi nhin thay
danh sach goi thau, quay lai terminal va nhan **Enter**. Khong dong trinh duyet truoc khi nhan Enter.

**Buoc 3 - Tim bang phien vua luu:**

```powershell
QI-Crawler tim-tren-web --ten example-tender --tu-khoa "air purifier" --so-luong 50
```

**Buoc 4 - Xuat ket qua:**

```powershell
QI-Crawler xuat-bao-cao --tep data\bao-cao-air-purifier.xlsx
```

Lan tim kiem sau thuong khong can dang nhap lai. Neu website dua ve trang dang nhap hoac bao het phien, chay lai:

```powershell
QI-Crawler dang-nhap --ten example-tender
```

### Vi du D - Xep hang co hoi Wi-Fi

Sao chep file cau hinh mau va mo `monitoring.yaml`:

```powershell
Copy-Item monitoring.example.yaml monitoring.yaml
```

Trong file, dat nhom Wi-Fi co cac tu `wifi`, `wireless`, `access point`, `WLAN`; dat keyword loai tru nhu
`civil construction`, `medicine`, `food`. Sau do chay:

```powershell
QI-Crawler xep-hang
```

Mo `data\reports\co-hoi-uu-tien.xlsx`. Doc tu trai sang phai: muc uu tien, trang thai, diem, keyword khop,
bang chung QI, du lieu thieu, rui ro, canh bao va hanh dong tiep theo. Goi `INSUFFICIENT_DATA` phai duoc mo
trang chi tiet va bo sung metadata; khong tu dien diem.

### Mau cong viec hang ngay ngan gon

Nguoi dung thong thuong chi can nho bon viec:

```powershell
QI-Crawler tim-goi --tu-khoa "TU KHOA TIENG ANH"
QI-Crawler xep-hang
QI-Crawler xuat-bao-cao
QI-Crawler -help
```

Voi website can tai khoan, thay lenh `tim-goi` bang `tim-tren-web` sau khi da thuc hien `them-nguon` va `dang-nhap`.

## 11. Tim bang ten Viet, ten Anh va nhom nganh

Nguoi dung chi can nhap ten quen thuoc. QI-Crawler tu tim bang ten da nhap va cac ten tuong duong trong
`keyword-groups.yaml`.

Vi du:

```powershell
QI-Crawler tim-goi --tu-khoa "sand"
```

Chuong trinh se thong bao:

```text
Product keywords: sand, cat, cat trang, white sand, silica sand
Category: Construction Materials (Vat lieu xay dung, VLXD, building materials)
```

Mot vi du khac:

```powershell
QI-Crawler tim-goi --tu-khoa "mo dun 5G"
```

MVP se kiem tra dong thoi cac cach viet `5G module`, `mo dun 5G`, `module 5G` va `modul 5G`, sau do gan
ngu canh nhom `Information Technology` (`Cong nghe thong tin/CNTT`). Viec so khop khong phan biet chu hoa,
chu thuong hoac dau tieng Viet.

Nhom nganh chi dung de phan loai va giai thich. MVP khong lay tat ca goi trong `VLXD` khi nguoi dung chi tim
`sand`, vi lam vay se dua vao nhieu goi khong phu hop nhu thep, gach hoac son.

### Them san pham moi ma khong sua code

Mo file `keyword-groups.yaml`. Trong dung nhom nganh, them san pham theo mau:

```yaml
      - name: ten tieng Viet
        aliases:
          - ten tieng Anh
          - ten viet tat
          - cach viet thuong gap khac
```

Vi du them thiet bi tuong lua vao nhom Information Technology:

```yaml
      - name: thiet bi tuong lua
        aliases:
          - firewall
          - network firewall
          - next generation firewall
```

Giu nguyen khoang trang dau dong nhu cac san pham co san. Sau khi luu file, chay lai `tim-goi` hoac
`tim-tren-web`; khong can cai lai chuong trinh.

### Them tu khoa moi co xac nhan

Vi du them mot loai cap mang moi:

```powershell
QI-Crawler them-tu-khoa `
  --tu-khoa "cap mang ngoai troi" `
  --ten-khac "outdoor network cable" `
  --ten-khac "outdoor LAN cable" `
  --mo-ta "Cap ket noi switch, router va thiet bi mang"
```

QI-Crawler doc ten, ten khac va mo ta, sau do so voi cac `signals` cua tung nhom nganh. Neu du tin cay,
san pham duoc them ngay vao dung nhom trong `keyword-groups.yaml`. Cac lan tim sau tu dong su dung toan bo
ten tuong duong.

Neu tu khoa qua chung hoac co the thuoc nhieu nganh, chuong trinh khong tu doan. No luu tu khoa vao
`pending_keywords` de nguoi phu trach xem lai. Sau khi xac nhan, chay:

```powershell
QI-Crawler them-tu-khoa `
  --tu-khoa "ten san pham" `
  --ten-khac "ten tieng Anh" `
  --nhom "Information Technology"
```

`tim-goi` va `tim-tren-web` chi mo rong tu khoa da co de tim kiem; hai lenh nay khong tu hoc, them hoac sua
`keyword-groups.yaml`. Muon them mot san pham/tu khoa moi, dung lenh `QI-Crawler them-tu-khoa` va kiem tra
nhom nganh truoc khi xac nhan. QI-Crawler khong tu dich ten san pham khong co can cu: nguoi dung nen cung cap
`--ten-khac` hoac kiem tra lai ten do nha san xuat cong bo.

## 12. Theo doi tu dong khi de may chay

### Buoc 1 - Tao cau hinh

```powershell
Copy-Item monitoring.example.yaml monitoring.yaml
```

Mo `monitoring.yaml` va sua:

- `interval_minutes`: so phut giua hai luot quet, toi thieu 5 phut.
- `keywords`: cac san pham QI muon theo doi.
- `keyword_groups`: cac nhom keyword duong va trong so; tu trong mot nhom la dieu kien `OR`.
- `required_any`: chi can khop mot tu (`OR`).
- `required_all`: phai khop tat ca tu (`AND`).
- `excluded_keywords`: khop mot tu se dua goi ve `SKIP` (`NOT`).
- `authenticated_sources`: ten cac website da chay `them-nguon` va `dang-nhap`.
- `output`: vi tri bao cao Excel xep hang.

### Buoc 2 - Chay thu mot luot

```powershell
QI-Crawler xep-hang
```

Mo `data\reports\co-hoi-uu-tien.xlsx` va kiem tra ket qua. Cac trang thai gom:

- `PRIORITY`: diem tu 75 va du metadata quan trong.
- `REVIEW`: diem 55-74 va du metadata quan trong.
- `SKIP`: duoi 55, het han, khong dat keyword bat buoc hoac khop keyword loai tru.
- `INSUFFICIENT_DATA`: thieu ma goi, ten, gia, deadline, URL hoac thong tin chi tiet; diem de trong.

Cot `alerts` co `NEW_MATCH` khi co hoi moi phu hop va `CLOSING_SOON` khi deadline nam trong nguong canh bao.
Cot `score_explanation` giai thich tung thanh phan diem; cot `next_action` cho biet ai can xu ly tiep.

### Buoc 3 - Chay lien tuc

```powershell
QI-Crawler theo-doi
```

Giu terminal mo, may co Internet va khong de Windows tu Sleep. Nhan `Ctrl+C` de dung an toan. Neu phien cua
website dang nhap het han, chay lai `QI-Crawler dang-nhap --ten TEN-NGUON`.

De van hanh on dinh, nen cau hinh Windows Task Scheduler chay lenh sau moi gio:

```powershell
QI-Crawler theo-doi --mot-lan
```

Moi luot quet cap nhat ban ghi trung theo ma thong bao va phien ban. Opportunity Priority Score chi de xep
hang, khong thay the buoc tai ho so, kiem tra tieu chi bat buoc, phe duyet noi bo hoac quyet dinh tham du.

## Co gi moi trong 0.6.1

- `xuat-tbmt` tao file trinh bay theo form TBMT 18 cot, header dong 10 va du lieu tu dong 11.
- Tien/ngay gio la kieu Excel, URL nguon la hyperlink va co bo loc tai dong header.
- Dong loi tach sang file rejects; template va file cu khong bi ghi de.
- `--to-canh-bao` to mau deadline sap het han va truong quan trong con thieu.
- Cac truong khong co bang chung du lieu se de trong, khong dung gia tri gia de lam day bao cao.
- `xuat-bao-cao` van giu cac sheet ky thuat cho BOQ va ton kho.

Nguoi moi chay:

```powershell
QI-Crawler -help
```

Man hinh nay chi hien cac lenh hang ngay. Nguoi van hanh ky thuat chay:

```powershell
QI-Crawler -adv
```

Lich su thay doi luon nam trong `CHANGELOG.md`; tai lieu nay giu vi du thao tac day du.

Khi co thay doi, cap nhat `CHANGELOG.md` va tai lieu nay. Chi cap nhat `-help` hoac `-adv` neu danh sach
lenh va luong thao tac cua nguoi dung thay doi.

### Rao can hien tai cua MVP

QI-Crawler chua co giao dien nut bam. Nhan su van can mo Terminal, kich hoat `.venv` va dung mot so file cau
hinh. Lenh dung hien tai la:

```powershell
.\.venv\Scripts\Activate.ps1
QI-Crawler dang-nhap --source egp
QI-Crawler tim-tren-web --ten egp --tu-khoa "cap quang"
QI-Crawler xep-hang
```

Khong dung `python src/qi_crawler/cli.py login`; cach nay bo qua entry point da cai dat va ten lenh tieng Viet
cua MVP.

### Roadmap Web UI

Phien ban tiep theo du kien co Web UI cuc bo de nhan su Bid/Phap che/Hanh chinh co the:

1. Bam nut mo trinh duyet va tu dang nhap.
2. Nhap URL, tu khoa va nguon bang form.
3. Bam `Tim goi`, `Xep hang` va `Xuat Excel`.
4. Xem trang thai session, deadline, loi cau hinh va du lieu thieu bang thong bao de hieu.
5. Chon file ton kho/BOQ bang hop thoai thay vi go duong dan.

CLI va API van duoc giu cho nguoi van hanh ky thuat, Windows Task Scheduler va cac quy trinh tu dong.

## 13. Lenh nang cao

Cac lenh hang ngay nam trong `QI-Crawler -help`. Cac lenh ky thuat duoc tach rieng de nguoi moi khong bi
roi. Nguoi van hanh xem bang:

```powershell
QI-Crawler -adv
```

Bang nang cao co cac nhom lenh crawl truc tiep, import/xuat ky thuat, doi chieu bang chung, kiem tra selector
website, nang cap database va quan ly data warehouse. Vi du:

```text
import-file, export, analyze-bid, db-upgrade,
kiem-tra-nguon,
warehouse-status, report-daily
```

Xem tham so cua mot lenh cu the:

```powershell
QI-Crawler kiem-tra-nguon -help
QI-Crawler warehouse-status -help
```

### Nang cap database an toan

Khi QI-Crawler thong bao database can nang cap, dong cac cua so dang dung QI-Crawler roi chay:

```powershell
QI-Crawler db-upgrade
```

Lenh nay tu tao ban sao trong `data/backups/`, nhan dien database cu chua co Alembic nhung da co
`crawl_tasks`, sau do moi nang cap schema. Khong tu xoa du lieu. Khong dung lenh nay dong thoi tren
hai cua so Terminal.

Tim kiem `tim-goi` tu dong dung FTS5 neu SQLite cua may ho tro; neu khong, QI-Crawler tu quay ve
cach tim kiem cuc bo tuong thich. Ca hai cach deu ho tro tu co dau/khong dau, vi du `chống thấm`
va `chong tham`. Lenh tim kiem khong tu dong them hay sua tu khoa trong `keyword-groups.yaml`.

## 13A. Cong viec bat buoc tai T-7 ngay

Tai T-7 ngay truoc han nop, nhan su phu trach QI-Crawler thuc hien theo thu tu:

```powershell
QI-Crawler kiem-tra-nguon --ten egp
QI-Crawler tim-tren-web --ten egp --tu-khoa "TU KHOA SAN PHAM"
QI-Crawler xep-hang
```

Sau do kiem tra du phien ban E-HSMT/sua doi/lam ro va ban giao bon bang chung: bao cao Excel, thu muc
E-HSMT, nhat ky chay, danh muc phien ban kem ngay gio tai. Neu selector chua san sang hoac thieu tai lieu,
khong danh dau hoan tat T-7.

## 13B. Kiem tra tieng Viet tren Windows

QI-Crawler chap nhan tu khoa co dau nhu `Lanh Binh Thang` va `Cap quang` (khi go thuc te co the dung day du
dau tieng Viet). Logic tim kiem tu chuan hoa chu co dau; file Excel van giu chu co dau de nguoi dung doc.
Neu terminal hien sai font, chay truoc:

```powershell
$env:PYTHONUTF8="1"
```

Sau khi xuat Excel, mo file va kiem tra ten goi/ben moi thau; khong ket luan loi du lieu chi dua vao font cua
terminal.

## 14. Khac phuc loi thuong gap

- `gh is not recognized`: mo terminal moi sau khi cai GitHub CLI.
- Terminal hien `>>`: nhan `Ctrl+C`.
- Khong tim thay goi: dung tu khoa rong hon hoac tang khoang ngay.
- Ket qua `INSUFFICIENT_DATA`: mo trang chi tiet va bo sung gia, deadline hoac metadata dang thieu.
- File Excel khong cap nhat: dong file dang mo roi xuat lai.
- Website yeu cau dang nhap lai: phien da het han; chay lai `dang-nhap`.
