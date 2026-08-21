# QI-Crawler

QI-Crawler là công cụ nội bộ hỗ trợ Team Bid thu thập, đọc, tổ chức, tìm kiếm và truy xuất thông tin đấu thầu.

**Nguyên tắc cốt lõi:** QI-Crawler cung cấp dữ liệu và bằng chứng; con người kiểm tra, tính toán, đánh giá và quyết định.

## Chức năng chính

- Thu thập dữ liệu từ nguồn được cấu hình, gồm nguồn công khai và nguồn cần người dùng đăng nhập.
- Tiếp nhận tài liệu PDF, DOCX, XLSX và ZIP; lưu SHA, định danh, revision và provenance.
- Tìm kiếm, lọc và xuất dữ liệu TBMT/Excel phục vụ kiểm tra nghiệp vụ.
- Nhập KHMT Excel, giữ nguyên dữ liệu nguồn, tách PL base/revision và chuẩn hóa các trường có thể kiểm chứng.
- Tổng hợp Discovery theo tỉnh/thành, ngân sách và phương thức lựa chọn.
- Targeted Search theo ngân sách, tỉnh/thành, từ khóa và phương thức lựa chọn với reason codes giải thích kết quả.
- Ghi log chẩn đoán có cấu trúc và hỗ trợ sao chép thông tin kỹ thuật đã che dữ liệu nhạy cảm.

## Ranh giới an toàn

QI-Crawler không:

- tự vượt CAPTCHA, OTP hoặc cơ chế bảo mật;
- tự suy diễn mã IB từ mã PL;
- tự chọn nhà cung cấp, model hoặc SKU;
- tự đưa ra GO/HOLD/NO-GO, xác suất trúng thầu hoặc quyết định tham dự;
- coi dữ liệu máy xử lý là dữ liệu đã được con người phê duyệt.

`Machine Verified != Human Approved`.

SQLite là System of Record. Excel là nguồn nhập hoặc artifact xuất, không phải nguồn sự thật nội bộ thay thế database.

## Chạy từ source trên Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install chromium
QI-Crawler db-upgrade
python -m qi_crawler.gui
```

Nếu dùng launcher nội bộ đã được cài đặt, có thể khởi động QI-Crawler trực tiếp mà không cần chạy các lệnh trên.

## Tài liệu

- [Hướng dẫn sử dụng](HUONG_DAN_SU_DUNG.md)
- [Changelog](CHANGELOG.md)
- [Quy tắc phát triển](AGENTS.md)
- [KHMT data contract](docs/KHMT_DATA_CONTRACT.md)
- [Agent handoff hiện tại](docs/agent_handoff/CURRENT.md)

## Trạng thái

QI-Crawler đang được phát triển theo các Work Package nhỏ, có regression test, CI và independent audit trước khi merge. Dữ liệu runtime, session đăng nhập, tài liệu người dùng và file nghiệp vụ thật không được commit vào Git.
