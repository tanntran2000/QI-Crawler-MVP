# EGP Crawler Python 0.2 — Crawler, ETL và báo cáo đấu thầu

Bộ mã này là nền tảng Python bất đồng bộ để thu thập **dữ liệu đấu thầu từ các nguồn mà doanh nghiệp được phép tự động truy cập**, nhập dữ liệu Excel/CSV, tải tệp đính kèm, lưu database và tạo báo cáo hằng ngày.

> Hệ thống giữ nguyên các hàng rào tuân thủ: domain allowlist, `robots.txt`, rate limit và dừng khi phát hiện CAPTCHA/trang chặn. Bản này **không** xoay proxy dân cư, giả mạo User-Agent, né phát hiện bot hoặc tự động giải CAPTCHA.

## 1. Thành phần đã nâng cấp

- Playwright bất đồng bộ (`async_playwright`).
- Tìm kiếm động và phân trang bằng selector cấu hình.
- Bắt sự kiện tải tệp bằng `page.expect_download()`.
- Tải HTTP cho URL trực tiếp; tải Playwright cho nút sinh file bằng JavaScript/session.
- Tên file an toàn, chống ghi đè, giới hạn dung lượng, allowlist phần mở rộng và SHA-256.
- Trạng thái attachment: `pending`, `downloading`, `downloaded`, `failed`, `manual_review`.
- Retry tệp tải lỗi.
- Import `.csv` và `.xlsx`, chuẩn hóa cột tiếng Việt/tiếng Anh, chống trùng và xuất dòng lỗi.
- Lưu HTML gốc trong `data/raw/`.
- Theo dõi `crawl_runs`: số bản ghi mới, cập nhật và lỗi.
- Báo cáo Excel nhiều sheet và gửi email SMTP tùy chọn.
- REST API FastAPI.
- Migration cộng thêm cho database SQLite/PostgreSQL cũ của bản MVP.
- GitHub Actions chạy test và Ruff.

## 2. Cài đặt trên Windows/VS Code

```powershell
cd "C:\duong-dan\egp-crawler-python"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install chromium

Copy-Item config.example.yaml config.yaml -Force
egp-crawler init-db
```


Nếu PowerShell chặn kích hoạt môi trường:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Kiểm thử

```powershell
python -m pytest -q
```

Kết quả của bản phát hành này:

```text
8 passed
```

## 4. Cấu hình quan trọng

Sửa `config.yaml`:

```yaml
compliance:
  obey_robots_txt: true
  stop_on_captcha: true
  identify_user_agent: "EGPResearchCrawler/0.2 (contact: email-cong-ty@example.com)"

crawl:
  requests_per_minute: 12
  concurrency: 1
  max_pages_per_run: 100
```

Selector được tách khỏi code:

```yaml
selectors:
  search_input: "input[name='keyword']"
  search_button: "button:has-text('Tìm kiếm')"
  result_ready: "table tbody tr"
  list_item: "table tbody tr"
  detail_link: "a.detail-link"
  next_page: "button:has-text('Sau')"

  attachment_rows: "table.attachments tbody tr"
  attachment_download_button: "button.download"
  attachment_name: "td.file-name"
```

Các selector trên chỉ là ví dụ. Phải thay bằng selector của nguồn thực tế được phép sử dụng. Ưu tiên `data-testid`, role hoặc nhãn ổn định; tránh XPath tuyệt đối.

## 5. Import Excel/CSV

Các tên cột được nhận diện:

- `Mã TBMT` / `notice_code`
- `Tên gói thầu` / `title`
- `Bên mời thầu` / `buyer`
- `Chủ đầu tư` / `investor`
- `Giá gói thầu` / `package_price`
- `Ngày đăng tải` / `published_at`
- `Thời điểm đóng thầu` / `closing_at`
- `URL` / `source_url`
- `Tệp đính kèm` / `attachments`

Chạy:

```powershell
egp-crawler import-file data\input.xlsx
egp-crawler import-file data\input.csv
```

Dòng thiếu cả mã TBMT hoặc tên gói thầu bị loại và ghi vào:

```text
data/rejects/
```

## 6. Crawl một hoặc nhiều URL

```powershell
egp-crawler crawl "URL_CHI_TIET_DUOC_PHEP"
```

Từ file URL:

```powershell
egp-crawler crawl-file data\urls.txt
```

HTML gốc được lưu trong `data/raw/html/` để kiểm tra lại parser.

## 7. Tìm kiếm động và phân trang

Sau khi cấu hình selector:

```powershell
egp-crawler collect-dynamic `
  "URL_TRANG_DANH_SACH_DUOC_PHEP" `
  --keyword "thiết bị mạng" `
  --max-pages 10 `
  --output data\urls.txt `
  --headed
```

Luồng này:

1. Mở trang bằng Playwright.
2. Nhập từ khóa và bấm tìm kiếm.
3. Chờ bảng kết quả.
4. Thu URL chi tiết.
5. Bấm trang tiếp theo đến giới hạn cấu hình.
6. Dừng nếu trang không thay đổi hoặc nút Next bị vô hiệu hóa.

## 8. Tải file bằng sự kiện Playwright

Dùng khi tệp chỉ được tạo sau khi click hoặc cần cookie/session của Browser Context:

```powershell
egp-crawler download-page `
  "URL_TRANG_CHI_TIET_DUOC_PHEP" `
  --package-id "IB2600012345" `
  --headed
```

Tệp được lưu theo cấu trúc:

```text
data/downloads/IB2600012345/
  HSMT.pdf
  Danh_muc_hang_hoa.xlsx
```

Metadata được lưu trong bảng `attachments`, gồm đường dẫn, SHA-256, dung lượng, phương thức tải và trạng thái.

Retry các URL tải trực tiếp bị lỗi:

```powershell
egp-crawler retry-downloads --limit 100
```

Tệp cần click động phải chạy lại `download-page`; crawler không tự đoán nút download khi selector chưa được cấu hình.

## 9. Discovery JSON/XHR

```powershell
egp-crawler discover `
  "URL_DUOC_PHEP" `
  --seconds 90 `
  --headed
```

Phản hồi JSON cùng domain được lưu trong `data/discovery/`. Đây là công cụ khảo sát cấu trúc API công khai, không bỏ qua `robots.txt`.

## 10. Xuất dữ liệu và báo cáo

Xuất toàn bộ dữ liệu:

```powershell
egp-crawler export --format xlsx --output data\notices.xlsx
egp-crawler export --format csv --output data\notices.csv
```

Báo cáo hằng ngày:

```powershell
egp-crawler report-daily
```

Các sheet:

- Gói thầu mới
- Sắp đóng thầu
- Tất cả gói thầu
- Tệp tải lỗi
- Chất lượng dữ liệu

Chọn ngày và khoảng sắp đóng thầu:

```powershell
egp-crawler report-daily --date 2026-07-28 --days-ahead 7
```

## 11. Gửi email báo cáo

Trong `config.yaml`:

```yaml
reporting:
  smtp_host: smtp.example.com
  smtp_port: 587
  smtp_username: bidding-bot@example.com
  smtp_use_tls: true
  email_from: bidding-bot@example.com
  email_to:
    - sales@example.com
    - bidding@example.com
```

Trong `.env`:

```env
EGP_SMTP_USERNAME=bidding-bot@example.com
EGP_SMTP_PASSWORD=mat-khau-ung-dung
```

Gửi báo cáo:

```powershell
egp-crawler report-daily --send-email
```

Không commit `.env` lên GitHub.

## 12. REST API

```powershell
egp-crawler serve --host 127.0.0.1 --port 8000
```

Mở:

```text
http://127.0.0.1:8000/docs
```

Endpoint:

- `GET /health`
- `GET /notices`
- `GET /notices/{id}`
- `GET /crawl-runs`
- `GET /stats`

## 13. PostgreSQL

```powershell
docker compose up -d postgres
```

`.env`:

```env
EGP_DATABASE_URL=postgresql+psycopg://egp:egp@localhost:5432/egp
```

```powershell
python -m pip install -e ".[postgres,dev]"
egp-crawler init-db
```

## 14. Lập lịch 8 giờ sáng trên Windows

Tạo `run_daily.ps1`:

```powershell
Set-Location "C:\duong-dan\egp-crawler-python"
.\.venv\Scripts\Activate.ps1

egp-crawler import-file data\input.xlsx
egp-crawler report-daily --send-email
```

Dùng **Windows Task Scheduler** để chạy file này lúc 08:00. Không lập lịch crawl một nguồn chưa được cho phép tự động truy cập.

## 15. Đưa lên GitHub

Repository đã loại khỏi Git:

- `.venv/`
- `.env`
- database SQLite
- file tải xuống
- dữ liệu raw/discovery/reject/report
- cache và `*.egg-info`

```powershell
git init
git add .
git commit -m "Upgrade crawler ETL downloads reporting"
git branch -M main
git remote add origin URL_REPOSITORY
git push -u origin main
```

## 16. Giới hạn và hướng production

- Cần adapter riêng cho API/file xuất chính thức của từng nguồn.
- Selector DOM có thể thay đổi và phải được kiểm thử định kỳ.
- Migration cộng thêm hiện phù hợp MVP; production nên chuyển sang Alembic.
- Nên lưu file trên S3/MinIO và quét malware trước khi phân tích.
- Cần quản lý secrets bằng Vault/Secret Manager khi triển khai công ty.
- CAPTCHA, HTTP 403/429 và chính sách từ chối truy cập được chuyển sang trạng thái dừng/manual review, không tự động vượt qua.
