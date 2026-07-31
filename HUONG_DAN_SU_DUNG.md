# Hướng dẫn sử dụng QI Tender Assistant MVP

## 1. MVP làm được gì?

MVP hỗ trợ bốn việc:

1. Tìm gói thầu công khai trên UK Contracts Finder.
2. Lưu thông tin vào database nội bộ.
3. Xuất danh sách ra Excel để trình và phân công xử lý.
4. Đối chiếu yêu cầu với bằng chứng, trả kết luận GO/HOLD/NO-GO.

MVP không tự nộp hồ sơ, không vượt CAPTCHA và không tự xác nhận doanh nghiệp đủ điều kiện pháp lý.

## 2. Mở chương trình

Trong terminal VS Code, chạy từng dòng:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
QI-Crawler bat-dau
```

Nếu terminal hiện `>>`, nhấn `Ctrl+C` rồi nhập lại lệnh.

## 3. Tìm gói thầu

```powershell
QI-Crawler tim-goi --tu-khoa "network switch"
```

Tùy chọn:

```powershell
QI-Crawler tim-goi `
  --tu-khoa "wireless access point" `
  --tu-ngay 2026-01-01 `
  --so-luong 50
```

MVP chỉ lưu gói còn hạn. Từ khóa Contracts Finder nên viết bằng tiếng Anh và đủ cụ thể.

## 4. Xuất Excel

```powershell
QI-Crawler xuat-bao-cao
```

Hoặc chọn tên file:

```powershell
QI-Crawler xuat-bao-cao --tep data\bao-cao-network.xlsx
```

Các cột quan trọng:

- `title`: tên gói.
- `buyer`: đơn vị mua sắm.
- `package_price` và `currency`: giá trị ước tính.
- `closing_at`: hạn phản hồi.
- `source_url`: trang thông báo gốc.
- `source_kind`: nguồn dữ liệu.

## 5. Chuẩn bị bằng chứng năng lực

File `data\company-evidence.csv` gồm:

```text
evidence_code,title,evidence_type,description,keywords,source_path,valid_until,verified
```

Nhập bằng chứng:

```powershell
QI-Crawler import-evidence data\company-evidence.csv
```

Chỉ đặt `verified=true` sau khi đã kiểm tra tài liệu gốc và hiệu lực.

## 6. Đánh giá một gói

Tạo `data\yeu-cau.txt`, mỗi yêu cầu một dòng:

```text
Nhà thầu phải cung cấp switch Layer 3 có tối thiểu 24 cổng Gigabit.
Thiết bị phải có ít nhất 4 cổng uplink 10Gbps.
Nhà thầu phải cung cấp bảo hành tối thiểu 36 tháng.
```

Chạy:

```powershell
QI-Crawler danh-gia data\yeu-cau.txt
```

Ý nghĩa kết quả:

- `GO`: toàn bộ yêu cầu bắt buộc đã covered và có người xác nhận.
- `HOLD`: chưa đủ bằng chứng, chưa rõ spec hoặc chưa có người kiểm tra độc lập.
- `NO-GO`: có ít nhất một tiêu chí bắt buộc không đáp ứng.

## 7. Xác nhận sau khi kiểm tra

```powershell
QI-Crawler confirm-assessment 12 `
  --reviewer "Nguyen Van A" `
  --decision covered `
  --note "Đã kiểm tra datasheet trang 5"
```

Sau đó:

```powershell
QI-Crawler bid-gate
QI-Crawler predict-win
```

Không xác nhận `covered` nếu model, BOM, license, phụ kiện hoặc trang bằng chứng chưa rõ.

## 8. Quy trình làm việc khuyến nghị

1. Tìm gói bằng từ khóa cụ thể.
2. Mở `source_url` và tải đủ tài liệu còn hiệu lực.
3. Loại gói đã đóng hoặc không thuộc phạm vi QI.
4. Tách từng yêu cầu bắt buộc thành một dòng.
5. Đối chiếu model, BOM và bằng chứng.
6. Người lập và người kiểm tra phải là hai bước độc lập.
7. Chỉ trình cấp có thẩm quyền khi không còn blocker.

## 9. Website cần đăng nhập hoặc xác thực

### Bước 1 - Thêm nguồn

Sao chép URL của trang hiển thị danh sách gói thầu:

```powershell
QI-Crawler them-nguon `
  --ten muasamcong `
  --url "URL_TRANG_DANH_SACH_GOI_THAU"
```

Tên nguồn nên ngắn, không dấu, ví dụ `muasamcong`, `portal-a`, `khach-hang-b`.

### Bước 2 - Đăng nhập thủ công

```powershell
QI-Crawler dang-nhap --ten muasamcong
```

Một cửa sổ Chromium sẽ mở. Bạn tự thực hiện:

1. Nhập tài khoản và mật khẩu.
2. Nhập OTP hoặc CAPTCHA nếu website yêu cầu.
3. Đi tới đúng trang danh sách gói thầu.
4. Quay lại terminal và nhấn Enter.

MVP chỉ lưu cookie/session cục bộ tại `data\sessions`. Thư mục này không được đưa lên Git.
Không gửi file session qua email/chat vì nó có thể cho phép truy cập tài khoản trong thời gian còn hiệu lực.

### Bước 3 - Tìm trên phiên đã đăng nhập

```powershell
QI-Crawler tim-tren-web `
  --ten muasamcong `
  --tu-khoa "switch" `
  --so-luong 50
```

Sau đó xuất Excel:

```powershell
QI-Crawler xuat-bao-cao
```

Nếu website đăng xuất hoặc báo phiên hết hạn, chạy lại `dang-nhap`. MVP sẽ dừng nếu gặp CAPTCHA,
HTTP 403/429 hoặc robots.txt không cho phép tự động truy cập.

### Giới hạn của chế độ tự động

Mặc định MVP tìm keyword trong nội dung link trên trang. Website có cấu trúc đặc biệt, iframe,
API nội bộ hoặc nút phân trang riêng có thể cần cấu hình selector một lần bởi người kỹ thuật.
Không có parser duy nhất hoạt động chính xác trên mọi website.

## 10. Ví dụ thực hành dành cho người mới

Trước khi làm ví dụ, hãy mở đúng thư mục dự án trong VS Code, chọn **Terminal > New Terminal**, rồi chạy:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
```

Khi thấy `(.venv)` ở đầu dòng terminal, chương trình đã sẵn sàng.

### Ví dụ A - Tìm thiết bị mạng trên Contracts Finder

Mục tiêu: tìm các gói có nội dung liên quan đến switch mạng và xuất danh sách ra Excel.

**Bước 1:** chạy lệnh tìm kiếm:

```powershell
QI-Crawler tim-goi --tu-khoa "network switch" --so-luong 50
```

Chờ đến khi terminal thông báo đã đọc và lưu kết quả. Nếu không có kết quả, thử từ khóa rộng hơn:

```powershell
QI-Crawler tim-goi --tu-khoa "network equipment" --so-luong 100
```

**Bước 2:** xuất Excel:

```powershell
QI-Crawler xuat-bao-cao --tep data\bao-cao-switch.xlsx
```

**Bước 3:** trong Explorer của VS Code, mở thư mục `data`, sau đó mở file `bao-cao-switch.xlsx`.
Kiểm tra lần lượt `title`, `closing_at`, `package_price` và `source_url`. Bấm `source_url` để đọc thông báo gốc
trước khi trình cấp quản lý.

### Ví dụ B - Tìm gói cho sản phẩm Wi-Fi

Giả sử QI có access point Wi-Fi 6, hỗ trợ PoE và quản lý tập trung. Không nên tìm bằng một câu quá dài.
Hãy tìm từng nhóm từ khóa:

```powershell
QI-Crawler tim-goi --tu-khoa "WiFi 6 access point" --so-luong 50
QI-Crawler tim-goi --tu-khoa "wireless network equipment" --so-luong 50
QI-Crawler tim-goi --tu-khoa "managed wireless LAN" --so-luong 50
QI-Crawler xuat-bao-cao --tep data\bao-cao-wifi.xlsx
```

Các kết quả được lưu chung trong database; chương trình không tạo bản ghi trùng khi cùng một gói được tìm thấy nhiều lần.
Sau khi xuất Excel, người phụ trách vẫn phải mở hồ sơ gốc để kiểm tra số lượng, chứng chỉ, bảo hành, thời hạn và địa điểm giao hàng.

### Ví dụ C - Website cần đăng nhập

Giả sử trang danh sách gói thầu sau khi đăng nhập có địa chỉ:
`https://example-tender.com/tenders/list`. Hãy thay địa chỉ mẫu bằng URL thật của website bạn được phép truy cập.

**Bước 1 - Khai báo website một lần:**

```powershell
QI-Crawler them-nguon --ten example-tender --url "https://example-tender.com/tenders/list"
```

Nếu thành công, terminal sẽ hướng dẫn chạy `dang-nhap`.

**Bước 2 - Tự đăng nhập:**

```powershell
QI-Crawler dang-nhap --ten example-tender
```

Một cửa sổ trình duyệt mở ra. Bạn nhập tài khoản, mật khẩu, OTP hoặc CAPTCHA như bình thường. Sau khi nhìn thấy
danh sách gói thầu, quay lại terminal và nhấn **Enter**. Không đóng trình duyệt trước khi nhấn Enter.

**Bước 3 - Tìm bằng phiên vừa lưu:**

```powershell
QI-Crawler tim-tren-web --ten example-tender --tu-khoa "air purifier" --so-luong 50
```

**Bước 4 - Xuất kết quả:**

```powershell
QI-Crawler xuat-bao-cao --tep data\bao-cao-air-purifier.xlsx
```

Lần tìm kiếm sau thường không cần đăng nhập lại. Nếu website đưa về trang đăng nhập hoặc báo hết phiên, chạy lại:

```powershell
QI-Crawler dang-nhap --ten example-tender
```

### Ví dụ D - Đánh giá khả năng đáp ứng một gói

Tạo file `data\yeu-cau-switch.txt` và nhập mỗi yêu cầu trên một dòng, ví dụ:

```text
Switch phải có tối thiểu 24 cổng Gigabit Ethernet.
Switch phải có tối thiểu 4 cổng uplink 10Gbps.
Thiết bị phải được bảo hành tối thiểu 36 tháng.
Nhà thầu phải có tài liệu chứng minh xuất xứ sản phẩm.
```

Lưu file rồi chạy:

```powershell
QI-Crawler danh-gia data\yeu-cau-switch.txt
```

Đọc kết quả theo nguyên tắc:

- `GO`: có thể chuyển sang bước kiểm tra và phê duyệt nội bộ.
- `HOLD`: chưa đủ thông tin; cần bổ sung datasheet, chứng chỉ hoặc người xác nhận.
- `NO-GO`: có yêu cầu bắt buộc mà sản phẩm hoặc doanh nghiệp không đáp ứng.

Phần trăm dự đoán chỉ là chỉ báo hỗ trợ sàng lọc, không phải cam kết trúng thầu. Không được đổi một tiêu chí thành
`covered` chỉ để tăng điểm nếu chưa có tài liệu chứng minh.

### Mẫu công việc hằng ngày ngắn gọn

Người dùng thông thường chỉ cần nhớ bốn việc:

```powershell
QI-Crawler tim-goi --tu-khoa "TỪ KHÓA TIẾNG ANH"
QI-Crawler xuat-bao-cao
QI-Crawler danh-gia data\yeu-cau.txt
QI-Crawler --help
```

Với website cần tài khoản, thay lệnh `tim-goi` bằng `tim-tren-web` sau khi đã thực hiện `them-nguon` và `dang-nhap`.

## 11. Lệnh nâng cao

Các lệnh kỹ thuật cũ vẫn được giữ cho người quản trị:

```text
collect-contracts-finder, import-file, export, analyze-bid,
confirm-assessment, bid-gate, predict-win, report-daily, serve
```

Xem toàn bộ bằng:

```powershell
QI-Crawler --help
```

## 12. Khắc phục lỗi thường gặp

- `gh is not recognized`: mở terminal mới sau khi cài GitHub CLI.
- Terminal hiện `>>`: nhấn `Ctrl+C`.
- Không tìm thấy gói: dùng từ khóa rộng hơn hoặc tăng khoảng ngày.
- Kết quả luôn `HOLD`: chưa có người kiểm tra xác nhận bằng chứng.
- File Excel không cập nhật: đóng file đang mở rồi xuất lại.
- Website yêu cầu đăng nhập lại: phiên đã hết hạn; chạy lại `dang-nhap`.
