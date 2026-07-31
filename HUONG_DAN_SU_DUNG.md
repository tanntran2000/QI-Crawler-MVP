# Huong dan su dung QI Tender Assistant MVP

## 1. MVP lam duoc gi?

MVP ho tro bon viec:

1. Tim goi thau cong khai tren UK Contracts Finder.
2. Luu thong tin vao database noi bo.
3. Xuat danh sach ra Excel de trinh va phan cong xu ly.
4. Doi chieu yeu cau voi bang chung, tra ket luan GO/HOLD/NO-GO.

MVP khong tu nop ho so, khong vuot CAPTCHA va khong tu xac nhan doanh nghiep du dieu kien phap ly.

## 2. Mo chuong trinh

Trong terminal VS Code, chay tung dong:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
QI-Crawler bat-dau
```

Neu terminal hien `>>`, nhan `Ctrl+C` roi nhap lai lenh.

## 3. Tim goi thau

```powershell
QI-Crawler tim-goi --tu-khoa "network switch"
```

Tuy chon:

```powershell
QI-Crawler tim-goi `
  --tu-khoa "wireless access point" `
  --tu-ngay 2026-01-01 `
  --so-luong 50
```

MVP chi luu goi con han. Tu khoa Contracts Finder nen viet bang tieng Anh va du cu the.

## 4. Xuat Excel

```powershell
QI-Crawler xuat-bao-cao
```

Hoac chon ten file:

```powershell
QI-Crawler xuat-bao-cao --tep data\bao-cao-network.xlsx
```

Cac cot quan trong:

- `title`: ten goi.
- `buyer`: don vi mua sam.
- `package_price` va `currency`: gia tri uoc tinh.
- `closing_at`: han phan hoi.
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

## 5. Chuan bi bang chung nang luc

File `data\company-evidence.csv` gom:

```text
evidence_code,title,evidence_type,description,keywords,source_path,valid_until,verified
```

Nhap bang chung:

```powershell
QI-Crawler import-evidence data\company-evidence.csv
```

Chi dat `verified=true` sau khi da kiem tra tai lieu goc va hieu luc.

## 6. Danh gia mot goi

Tao `data\yeu-cau.txt`, moi yeu cau mot dong:

```text
Nha thau phai cung cap switch Layer 3 co toi thieu 24 cong Gigabit.
Thiet bi phai co it nhat 4 cong uplink 10Gbps.
Nha thau phai cung cap bao hanh toi thieu 36 thang.
```

Chay:

```powershell
QI-Crawler danh-gia data\yeu-cau.txt
```

Y nghia ket qua:

- `GO`: toan bo yeu cau bat buoc da covered va co nguoi xac nhan.
- `HOLD`: chua du bang chung, chua ro spec hoac chua co nguoi kiem tra doc lap.
- `NO-GO`: co it nhat mot tieu chi bat buoc khong dap ung.

## 7. Xac nhan sau khi kiem tra

```powershell
QI-Crawler confirm-assessment 12 `
  --reviewer "Nguyen Van A" `
  --decision covered `
  --note "Da kiem tra datasheet trang 5"
```

Sau do:

```powershell
QI-Crawler bid-gate
QI-Crawler predict-win
```

Khong xac nhan `covered` neu model, BOM, license, phu kien hoac trang bang chung chua ro.

## 8. Quy trinh lam viec khuyen nghi

1. Tim goi bang tu khoa cu the.
2. Mo `source_url` va tai du tai lieu con hieu luc.
3. Loai goi da dong hoac khong thuoc pham vi QI.
4. Tach tung yeu cau bat buoc thanh mot dong.
5. Doi chieu model, BOM va bang chung.
6. Nguoi lap va nguoi kiem tra phai la hai buoc doc lap.
7. Chi trinh cap co tham quyen khi khong con blocker.

## 9. Website can dang nhap hoac xac thuc

### Cach nhanh cho e-GP Viet Nam

Chay lan luot:

```powershell
QI-Crawler them-egp
QI-Crawler dang-nhap --ten egp-vietnam
```

Trinh duyet se mo. Nguoi dung tu dang nhap, nhap OTP/CAPTCHA va di den trang hien danh sach goi thau. Khi
da thay danh sach, quay lai terminal va nhan Enter. QI-Crawler se luu phien cuc bo va ghi nho URL hien tai.

Kiem tra cau truc trang truoc khi tim:

```powershell
QI-Crawler kiem-tra-nguon --ten egp-vietnam
```

Chi khi terminal bao `Nguon da san sang de tim goi`, moi chay:

```powershell
QI-Crawler tim-tren-web --ten egp-vietnam --tu-khoa "cap quang" --so-luong 100
QI-Crawler xuat-bao-cao --tep data\egp-cap-quang.xlsx
```

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

Mac dinh MVP tim keyword trong noi dung link tren trang. Website co cau truc dac biet, iframe,
API noi bo hoac nut phan trang rieng co the can cau hinh selector mot lan boi nguoi ky thuat.
Khong co parser duy nhat hoat dong chinh xac tren moi website.

## 10. Vi du thuc hanh danh cho nguoi moi

Truoc khi lam vi du, hay mo dung thu muc du an trong VS Code, chon **Terminal > New Terminal**, roi chay:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
```

Khi thay `(.venv)` o dau dong terminal, chuong trinh da san sang.

### Vi du A - Tim thiet bi mang tren Contracts Finder

Muc tieu: tim cac goi co noi dung lien quan den switch mang va xuat danh sach ra Excel.

**Buoc 1:** chay lenh tim kiem:

```powershell
QI-Crawler tim-goi --tu-khoa "network switch" --so-luong 50
```

Cho den khi terminal thong bao da doc va luu ket qua. Neu khong co ket qua, thu tu khoa rong hon:

```powershell
QI-Crawler tim-goi --tu-khoa "network equipment" --so-luong 100
```

**Buoc 2:** xuat Excel:

```powershell
QI-Crawler xuat-bao-cao --tep data\bao-cao-switch.xlsx
```

**Buoc 3:** trong Explorer cua VS Code, mo thu muc `data`, sau do mo file `bao-cao-switch.xlsx`.
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

### Vi du D - Danh gia kha nang dap ung mot goi

Tao file `data\yeu-cau-switch.txt` va nhap moi yeu cau tren mot dong, vi du:

```text
Switch phai co toi thieu 24 cong Gigabit Ethernet.
Switch phai co toi thieu 4 cong uplink 10Gbps.
Thiet bi phai duoc bao hanh toi thieu 36 thang.
Nha thau phai co tai lieu chung minh xuat xu san pham.
```

Luu file roi chay:

```powershell
QI-Crawler danh-gia data\yeu-cau-switch.txt
```

Doc ket qua theo nguyen tac:

- `GO`: co the chuyen sang buoc kiem tra va phe duyet noi bo.
- `HOLD`: chua du thong tin; can bo sung datasheet, chung chi hoac nguoi xac nhan.
- `NO-GO`: co yeu cau bat buoc ma san pham hoac doanh nghiep khong dap ung.

Phan tram du doan chi la chi bao ho tro sang loc, khong phai cam ket trung thau. Khong duoc doi mot tieu chi thanh
`covered` chi de tang diem neu chua co tai lieu chung minh.

### Mau cong viec hang ngay ngan gon

Nguoi dung thong thuong chi can nho bon viec:

```powershell
QI-Crawler tim-goi --tu-khoa "TU KHOA TIENG ANH"
QI-Crawler xuat-bao-cao
QI-Crawler danh-gia data\yeu-cau.txt
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

### De QI-Crawler tu phan loai va cap nhat

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

Khi chay `tim-goi` hoac `tim-tren-web` voi mot tu khoa chua co, MVP cung thu phan loai tu dong. Chi truong hop
co tin hieu ro moi duoc cap nhat; truong hop chua ro luon di vao hang cho. QI-Crawler khong tu dich ten san pham
khong co can cu: nguoi dung nen cung cap `--ten-khac` hoac kiem tra lai ten do nha san xuat cong bo.

## 12. Theo doi tu dong khi de may chay

### Buoc 1 - Tao cau hinh

```powershell
Copy-Item monitoring.example.yaml monitoring.yaml
```

Mo `monitoring.yaml` va sua:

- `interval_minutes`: so phut giua hai luot quet, toi thieu 5 phut.
- `keywords`: cac san pham QI muon theo doi.
- `contracts_finder`: bat/tat Contracts Finder.
- `authenticated_sources`: ten cac website da chay `them-nguon` va `dang-nhap`.
- `output`: vi tri bao cao Excel xep hang.

### Buoc 2 - Chay thu mot luot

```powershell
QI-Crawler theo-doi --mot-lan
```

Mo `data\reports\co-hoi-kha-thi.xlsx` va kiem tra ket qua. Cac trang thai gom:

- `KHA_THI_SO_BO`: khop san pham, co bang chung da xac minh va du diem so bo.
- `CAN_XEM`: co lien quan nhung thieu bang chung hoac thong tin; can nguoi phu trach xem.
- `THAP`: do phu hop thap.
- `HET_HAN`: khong dua vao danh sach co hoi dang xu ly.

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

Moi luot quet cap nhat ban ghi trung thay vi tao them ban sao. Diem kha thi chi de xep hang uu tien, khong thay
the buoc tai ho so, kiem tra tieu chi bat buoc, phe duyet noi bo hoac quyet dinh tham du.

## 13. Lenh nang cao

Cac lenh hang ngay nam trong `QI-Crawler -help`. Cac lenh ky thuat duoc tach rieng de nguoi moi khong bi
roi. Nguoi van hanh xem bang:

```powershell
QI-Crawler -adv
```

Bang nang cao co cac nhom lenh crawl truc tiep, import/xuat ky thuat, doi chieu bang chung, kiem tra selector
website va quan ly data warehouse. Vi du:

```text
collect-contracts-finder, import-file, export, analyze-bid,
confirm-assessment, bid-gate, predict-win, kiem-tra-nguon,
warehouse-status, report-daily
```

Xem tham so cua mot lenh cu the:

```powershell
QI-Crawler kiem-tra-nguon -help
QI-Crawler warehouse-status -help
```

## 13A. Cong viec bat buoc tai T-7 ngay

Tai T-7 ngay truoc han nop, nhan su phu trach QI-Crawler thuc hien theo thu tu:

```powershell
QI-Crawler kiem-tra-nguon --ten egp-vietnam
QI-Crawler tim-tren-web --ten egp-vietnam --tu-khoa "TU KHOA SAN PHAM"
QI-Crawler xuat-bao-cao --tep data\bao-cao-T7.xlsx
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
- Ket qua luon `HOLD`: chua co nguoi kiem tra xac nhan bang chung.
- File Excel khong cap nhat: dong file dang mo roi xuat lai.
- Website yeu cau dang nhap lai: phien da het han; chay lai `dang-nhap`.
