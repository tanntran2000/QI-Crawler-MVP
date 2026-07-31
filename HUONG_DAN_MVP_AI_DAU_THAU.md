# Hướng dẫn sử dụng MVP AI hỗ trợ đấu thầu

## 1. Mục đích

MVP hỗ trợ thu thập dữ liệu gói thầu, quản lý bằng chứng năng lực, tách yêu cầu E-HSMT,
đối chiếu yêu cầu với bằng chứng và tạo tỷ lệ trúng thầu **ước tính**.

Hệ thống không tự nộp E-HSDT, không vượt CAPTCHA hoặc cơ chế kiểm soát truy cập, không tạo
bằng chứng giả và không bảo đảm kết quả lựa chọn nhà thầu.

## 2. Khởi động trong VS Code

Mở Terminal tại thư mục dự án và chạy từng dòng:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
python -m pip install -e ".[dev]"
egp-crawler init-db
```

Nếu Terminal hiện `>>`, nhấn `Ctrl+C` rồi nhập lại lệnh. Không sao chép dấu ba backtick của
khối mã vào Terminal.

## 3. Chuẩn bị kho bằng chứng

Tạo `data\company-evidence.csv` với mã hóa UTF-8:

```csv
evidence_code,title,evidence_type,description,keywords,source_path,valid_until,verified
CERT-001,Chứng chỉ CCNP,certificate,Kỹ sư có chứng chỉ mạng Cisco,CCNP Cisco,D:\HoSo\CCNP.pdf,2027-12-31,true
EXP-001,Hợp đồng mạng LAN,contract,Triển khai switch và mạng LAN,mạng LAN switch,D:\HoSo\HopDong.pdf,,true
```

Quy tắc quan trọng:

- `evidence_code` phải duy nhất.
- Chỉ đặt `verified=true` sau khi người phụ trách đã kiểm tra tài liệu gốc và hiệu lực.
- `source_path` nên trỏ tới tài liệu chứng minh thực tế.
- Không ghi một năng lực mà doanh nghiệp hoặc nhân sự không thực sự có.

Nhập dữ liệu:

```powershell
egp-crawler import-evidence data\company-evidence.csv
```

## 4. Phân tích yêu cầu E-HSMT

Trong MVP hiện tại, chuyển phần tiêu chuẩn đánh giá/yêu cầu kỹ thuật thành file văn bản UTF-8,
mỗi yêu cầu đặt trên một dòng, ví dụ `data\ehsmt-requirements.txt`:

```text
Nhà thầu phải có tối thiểu một kỹ sư sở hữu chứng chỉ CCNP Cisco.
Nhà thầu phải có kinh nghiệm triển khai hệ thống mạng LAN.
Nhà thầu phải có doanh thu bình quân tối thiểu 10 tỷ đồng.
Nhà thầu phải có chứng chỉ ISO 27001 còn hiệu lực.
```

Phân tích:

```powershell
egp-crawler analyze-bid data\ehsmt-requirements.txt
```

Nếu gói thầu đã có trong bảng `notices`, gắn kết quả bằng ID:

```powershell
egp-crawler analyze-bid data\ehsmt-requirements.txt --notice-id 1
```

Ý nghĩa trạng thái:

- `covered`: keyword phù hợp và bằng chứng đã được xác minh.
- `partial`: có liên quan nhưng độ phủ thấp hoặc bằng chứng chưa được xác minh.
- `gap`: chưa tìm thấy bằng chứng phù hợp.

Mọi trạng thái đều cần chuyên gia presales/đấu thầu đọc lại nguyên văn yêu cầu.

## 5. Tạo tỷ lệ trúng thầu ước tính

Sau khi chạy `analyze-bid`:

```powershell
egp-crawler predict-win
```

Hoặc với gói thầu cụ thể:

```powershell
egp-crawler predict-win --notice-id 1
```

Kết quả gồm:

- `Điểm sẵn sàng hồ sơ`: mức độ đáp ứng dựa trên bằng chứng.
- `Tỷ lệ trúng thầu ước tính`: proxy thận trọng, bị giới hạn trong khoảng 5–80%.
- `Độ tin cậy`: tối đa 35% ở phiên bản MVP do chưa có dữ liệu lịch sử để hiệu chỉnh.
- Coverage yêu cầu bắt buộc và danh sách rủi ro.

Không dùng riêng con số này để quyết định tham dự thầu. Giá dự thầu, đối thủ, tiêu chí chấm,
tính hợp lệ của hồ sơ và đánh giá của tổ chuyên gia chưa được mô hình hiện tại quan sát đầy đủ.

## 6. Xem kết quả qua API

```powershell
egp-crawler serve
```

Mở `http://127.0.0.1:8000/docs` và kiểm tra:

- `GET /bid-compliance`
- `GET /bid-predictions`
- `GET /notices`
- `GET /stats`

Dừng API bằng `Ctrl+C`.

## 7. Crawl một URL công khai

```powershell
egp-crawler crawl "URL_CHI_TIET_GOI_THAU"
egp-crawler export --format xlsx --output data\ket-qua-crawl.xlsx
```

Chỉ dùng URL thuộc allowlist trong `config.yaml`. Khi website từ chối truy cập, yêu cầu CAPTCHA
hoặc robots.txt không cho phép, crawler sẽ dừng và chuyển sang rà soát thủ công.

## 8. Quy trình sử dụng khuyến nghị

1. Crawl/import thông tin gói thầu.
2. Kiểm tra nguồn và phiên bản E-HSMT.
3. Trích từng yêu cầu thành một dòng.
4. Cập nhật kho bằng chứng đã xác minh.
5. Chạy `analyze-bid`.
6. Xử lý toàn bộ `gap`, rồi kiểm tra lại `partial`.
7. Chạy `predict-win` để ưu tiên nguồn lực, không dùng như bảo đảm kết quả.
8. Một người lập hồ sơ và một người kiểm soát độc lập xác nhận trước khi nộp.

## 9. Kiểm tra kỹ thuật

```powershell
python -m pytest -q
python -m ruff check src tests
```

Database mặc định nằm tại `data\egp.db`. Nên sao lưu trước các đợt nhập dữ liệu lớn.
