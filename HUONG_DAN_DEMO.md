# Demo EGP Crawler

Bộ demo kiểm tra luồng an toàn, không truy cập website bên ngoài:

1. Tự tạo CSV mẫu theo ngày chạy.
2. Nhập CSV và lưu SQLite.
3. Tạo metadata tệp đính kèm ở trạng thái chờ tải.
4. Xuất toàn bộ dữ liệu ra Excel.
5. Tạo báo cáo nhiều sheet.

## Cách dùng

Giải nén nội dung bộ demo trực tiếp vào thư mục gốc `egp-crawler-python`.
Sau khi giải nén cần có file:

```text
egp-crawler-python/run_demo.ps1
```

Mở Terminal PowerShell tại thư mục dự án và chạy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_demo.ps1
```

Kết quả:

```text
data/egp.db
data/demo/du-lieu-mau.csv
data/demo/du-lieu-da-xuat.xlsx
data/reports/bao-cao-demo.xlsx
```

Các URL `example.com` chỉ là metadata minh họa. Script không truy cập hoặc tải dữ liệu từ chúng.
