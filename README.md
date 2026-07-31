# QI-Crawler MVP

QI-Crawler là công cụ nội bộ hỗ trợ QI Technologies tìm kiếm, sàng lọc và theo dõi cơ hội đấu thầu.
Người dùng có thể tìm gói theo tên Việt/Anh, thu thập dữ liệu từ nguồn công khai hoặc website cần đăng nhập,
xuất Excel và đánh giá sơ bộ khả năng đáp ứng.

> QI-Crawler không tự nộp hồ sơ, không vượt CAPTCHA và không tạo bằng chứng năng lực. Kết quả tìm kiếm,
> phân loại và tỷ lệ dự đoán luôn cần người phụ trách kiểm tra trước khi sử dụng.

## Tính năng hiện tại

- Tìm gói còn hạn trên UK Contracts Finder.
- Kết nối trang danh sách gói thầu khác bằng URL.
- Cho phép người dùng tự đăng nhập, nhập OTP/CAPTCHA và lưu phiên cục bộ.
- Tìm bằng tên Việt, tên Anh, tên viết tắt và biến thể chính tả.
- Tự phân loại từ khóa mới theo nhóm ngành với hàng chờ xác nhận khi chưa chắc chắn.
- Lưu dữ liệu vào SQLite và xuất báo cáo Excel.
- Đối chiếu yêu cầu với bằng chứng năng lực.
- Trả kết luận `GO`, `HOLD`, `NO-GO` và tỷ lệ dự đoán hỗ trợ sàng lọc.
- Giữ các hàng rào an toàn: domain allowlist, robots.txt, rate limit và dừng khi gặp chặn truy cập.

## Cài đặt trên Windows

Mở thư mục dự án bằng VS Code, chọn **Terminal > New Terminal**, rồi chạy từng dòng:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

Khi terminal hiện `(.venv)`, kiểm tra chương trình:

```powershell
QI-Crawler bat-dau
```

Nếu `.venv` đã tồn tại, những lần sau chỉ cần:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
```

## Trợ giúp

Xem danh sách lệnh và ví dụ:

```powershell
QI-Crawler -help
```

Cũng có thể dùng:

```powershell
QI-Crawler -h
QI-Crawler help
QI-Crawler tim-goi -help
```

Không gõ riêng `-help`, vì PowerShell yêu cầu dòng lệnh bắt đầu bằng tên chương trình.

## Quy trình nhanh: tìm và xuất Excel

### Tìm gói trên Contracts Finder

```powershell
QI-Crawler tim-goi --tu-khoa "network switch" --so-luong 50
QI-Crawler xuat-bao-cao --tep data\bao-cao-switch.xlsx
```

QI-Crawler chỉ lưu các gói còn hạn trong phạm vi dữ liệu đã đọc.

### Tìm trên website cần đăng nhập

Khai báo URL trang danh sách một lần:

```powershell
QI-Crawler them-nguon `
  --ten muasamcong `
  --url "URL_TRANG_DANH_SACH_GOI_THAU"
```

Mở trình duyệt do QI-Crawler quản lý và tự đăng nhập:

```powershell
QI-Crawler dang-nhap --ten muasamcong
```

Sau khi đăng nhập, đi tới trang danh sách, quay lại terminal và nhấn Enter. Tiếp theo:

```powershell
QI-Crawler tim-tren-web --ten muasamcong --tu-khoa "xi măng" --so-luong 100
QI-Crawler xuat-bao-cao --tep data\goi-thau-xi-mang.xlsx
```

Phiên đăng nhập được lưu trong `data/sessions/`, không được đưa lên Git. QI-Crawler không lưu mật khẩu và
không tự vượt CAPTCHA. Website có cấu trúc đặc biệt có thể cần cấu hình selector riêng.

## Từ khóa thông minh và nhóm ngành

Từ điển [keyword-groups.yaml](keyword-groups.yaml) chứa nhóm ngành, tên sản phẩm và tên tương đương.

Ví dụ `cát trắng` được mở rộng thành:

- `cát trắng`, `white sand`, `silica sand`;
- nhóm `Vật liệu xây dựng/VLXD`.

Ví dụ `mô đun 5G` được mở rộng thành:

- `mô đun 5G`, `module 5G`, `modul 5G`, `5G module`;
- nhóm `Công nghệ thông tin/CNTT`.

Nhóm ngành dùng để phân loại và giải thích, không dùng để lấy mọi gói trong cả ngành. Vì vậy tìm `cát trắng`
không tự động lấy các gói thép hoặc gạch.

### Thêm và tự phân loại từ khóa mới

```powershell
QI-Crawler them-tu-khoa `
  --tu-khoa "cáp mạng ngoài trời" `
  --ten-khac "outdoor network cable" `
  --ten-khac "outdoor LAN cable" `
  --mo-ta "Cáp kết nối switch, router và thiết bị mạng"
```

Nếu tín hiệu đủ rõ, từ khóa được cập nhật vào đúng nhóm. Nếu chưa rõ, nó được đưa vào `pending_keywords`.
Người phụ trách có thể xác nhận thủ công:

```powershell
QI-Crawler them-tu-khoa `
  --tu-khoa "tên sản phẩm" `
  --ten-khac "tên tiếng Anh" `
  --nhom "Công nghệ thông tin"
```

## Đánh giá khả năng đáp ứng

Tạo file `data\yeu-cau.txt`, mỗi yêu cầu một dòng, rồi chạy:

```powershell
QI-Crawler danh-gia data\yeu-cau.txt
```

Ý nghĩa kết quả:

- `GO`: tiêu chí bắt buộc đã có bằng chứng và được xác nhận.
- `HOLD`: thiếu bằng chứng, thông số chưa rõ hoặc chưa có người kiểm tra.
- `NO-GO`: có ít nhất một tiêu chí bắt buộc không đáp ứng.

Tỷ lệ dự đoán chỉ hỗ trợ ưu tiên cơ hội; không phải xác suất thống kê đã hiệu chỉnh và không cam kết trúng thầu.

## Dữ liệu và bảo mật

Không đưa các nội dung sau lên GitHub hoặc gửi qua email/chat:

- `data/sessions/`: cookie và token phiên đăng nhập;
- `.env`, `config.yaml`: cấu hình cục bộ hoặc secret;
- database và dữ liệu đầu ra nội bộ;
- tài liệu năng lực hoặc hồ sơ dự thầu chưa được phép chia sẻ.

Database mặc định vẫn dùng `data/egp.db` để bảo toàn dữ liệu từ phiên bản cũ. Đây chỉ là tên file tương thích,
không phải tên sản phẩm hiện tại.

## Tài liệu và lịch sử phiên bản

- [Hướng dẫn sử dụng chi tiết](HUONG_DAN_SU_DUNG.md)
- [Lịch sử cập nhật](CHANGELOG.md)

## Kiểm tra kỹ thuật

```powershell
python -m pytest -q
python -m ruff check src tests --no-cache
```

Trạng thái kiểm thử cục bộ gần nhất: 22 bài kiểm thử đạt. GitHub Actions có thể khác Windows về cách hiển thị
Unicode trong terminal; lỗi CI cần được xử lý trước khi hợp nhất Pull Request.
