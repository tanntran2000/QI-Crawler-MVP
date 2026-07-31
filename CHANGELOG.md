# Changelog

Tài liệu này ghi lại những thay đổi quan trọng của QI-Crawler theo từng phiên bản.

## 0.4.0 - 2026-07-31

### Thêm mới

- Hỗ trợ `QI-Crawler -help`, `QI-Crawler -h` và `QI-Crawler help`.
- Hiển thị danh sách lệnh cùng ví dụ có thể sao chép cho người mới.
- Thêm `keyword-groups.yaml` để quản lý nhóm ngành, sản phẩm và tên tương đương.
- Tìm không phân biệt chữ hoa/thường và dấu tiếng Việt.
- Mở rộng từ khóa theo tên Việt, tên Anh, tên viết tắt và biến thể chính tả.
- Thêm lệnh `them-tu-khoa` để tự phân loại và cập nhật sản phẩm mới.
- Thêm `pending_keywords` cho trường hợp chưa đủ căn cứ phân loại.
- Thêm tín hiệu nhận diện cho nhóm Vật liệu xây dựng và Công nghệ thông tin.
- Thêm kiểm thử cho help, mở rộng từ khóa, phân loại tự động và hàng chờ xác nhận.

### Thay đổi

- Đổi tên sản phẩm và CLI từ `egp-crawler` thành `QI-Crawler`.
- Đổi package Python từ `egp_crawler` thành `qi_crawler`.
- Viết lại README và hợp nhất tài liệu hướng dẫn cho người mới.
- Không dùng tên nhóm ngành rộng để tự nhận mọi gói, nhằm giảm kết quả sai.

### An toàn

- Chỉ tự cập nhật từ khóa khi có tín hiệu phân loại đủ rõ.
- Từ khóa mơ hồ luôn chờ con người xác nhận.
- Không tự dịch hoặc tự tạo tên sản phẩm khi chưa có căn cứ.

## 0.3.0 - 2026-07-31

### Thêm mới

- Thu thập gói còn hạn từ UK Contracts Finder qua OCDS API.
- Thêm website tùy chỉnh bằng URL trang danh sách.
- Cho phép người dùng tự đăng nhập, nhập OTP/CAPTCHA và lưu phiên cục bộ.
- Tái sử dụng cookie/session mà không lưu mật khẩu.
- Thêm lệnh tiếng Việt: `bat-dau`, `tim-goi`, `xuat-bao-cao`, `danh-gia`, `them-nguon`,
  `dang-nhap`, `tim-tren-web`.
- Thêm đối chiếu yêu cầu với bằng chứng năng lực.
- Thêm cổng quyết định `GO`, `HOLD`, `NO-GO` và xác nhận độc lập.
- Thêm tỷ lệ dự đoán hỗ trợ sàng lọc với giới hạn cho `HOLD` và `NO-GO`.
- Thêm migration cộng dồn để bảo toàn database cũ.

### Thay đổi

- Đơn giản hóa quy trình sử dụng và giảm tài liệu/script demo trùng lặp.
- Bảo vệ `data/sessions/` và `data/sources/` khỏi Git.

## 0.2.0

- Thêm tìm kiếm động và phân trang Playwright theo selector cấu hình.
- Thêm tải file bằng `expect_download()` và lưu SHA-256.
- Thêm trạng thái tải file, retry và manual review.
- Thêm import CSV/XLSX, kiểm tra chất lượng dữ liệu và reject file.
- Thêm lưu HTML raw, content hash và thống kê crawl run.
- Thêm báo cáo Excel nhiều sheet và gửi SMTP tùy chọn.
- Mở rộng API, cấu hình, kiểm thử và GitHub Actions.

## 0.1.0

- Khởi tạo crawler Python bất đồng bộ và cấu trúc database ban đầu.
