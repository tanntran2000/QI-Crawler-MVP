# QI Tender Assistant MVP

Công cụ nội bộ giúp QI tìm gói thầu công khai, lưu dữ liệu, xuất Excel và kiểm tra sơ bộ
khả năng đáp ứng. MVP không tự nộp hồ sơ và không thay thế quyết định của người phụ trách.

## Bắt đầu nhanh

Mở terminal VS Code tại thư mục dự án:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
python -m pip install -e ".[dev]"
QI-Crawler bat-dau
```

## Bốn lệnh chính

### 1. Khởi tạo

```powershell
QI-Crawler bat-dau
```

### 2. Tìm gói thầu còn hạn

Contracts Finder sử dụng tiếng Anh:

```powershell
QI-Crawler tim-goi --tu-khoa "network switch" --so-luong 20
```

Có thể dùng các từ khóa như `PoE switch`, `wireless access point`, `Wi-Fi 7`, `firewall`,
`server` hoặc `fiber optic`.

### 3. Xuất báo cáo Excel

```powershell
QI-Crawler xuat-bao-cao
```

File mặc định: `data\bao-cao-goi-thau.xlsx`.

### 4. Đánh giá yêu cầu

Tạo file văn bản UTF-8, mỗi yêu cầu một dòng, rồi chạy:

```powershell
QI-Crawler danh-gia data\yeu-cau.txt
```

Kết quả:

- `GO`: yêu cầu bắt buộc đã đáp ứng và được xác nhận.
- `HOLD`: cần thêm bằng chứng hoặc người kiểm tra.
- `NO-GO`: có yêu cầu bắt buộc không đáp ứng.

## Nguyên tắc an toàn

- Chỉ dùng tài liệu và năng lực có thật.
- Không tự coi thông số cao hơn là bù được thông số bắt buộc bị thiếu.
- Mỗi kết luận kỹ thuật cần ghi rõ tài liệu, trang và người kiểm tra.
- Chỉ thu thập nguồn công khai trong allowlist và tôn trọng robots.txt/rate limit.
- Tỷ lệ trúng thầu chỉ là ước tính hỗ trợ ưu tiên, không phải cam kết kết quả.

## Website cần đăng nhập

```powershell
QI-Crawler them-nguon --ten muasamcong --url "URL_TRANG_DANH_SACH"
QI-Crawler dang-nhap --ten muasamcong
QI-Crawler tim-tren-web --ten muasamcong --tu-khoa "switch"
QI-Crawler xuat-bao-cao
```

Bạn tự nhập tài khoản, mật khẩu, OTP hoặc CAPTCHA trong cửa sổ trình duyệt. MVP không lưu mật khẩu
và không tự vượt cơ chế bảo vệ của website.

## Tài liệu

Xem [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md) để biết quy trình chi tiết và các lệnh nâng cao.

## Kiểm tra kỹ thuật

```powershell
python -m pytest -q
python -m ruff check src tests
```
