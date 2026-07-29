$ErrorActionPreference = "Stop"

Write-Host "=== EGP Crawler Demo ===" -ForegroundColor Cyan

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Không tìm thấy .venv. Hãy chạy script từ thư mục gốc egp-crawler-python."
}

& ".\.venv\Scripts\Activate.ps1"

New-Item -ItemType Directory -Force ".\data\demo" | Out-Null
New-Item -ItemType Directory -Force ".\data\reports" | Out-Null

$today = Get-Date
$published = $today.ToString("yyyy-MM-dd")
$closing1 = $today.AddDays(3).ToString("yyyy-MM-dd 09:00:00")
$closing2 = $today.AddDays(5).ToString("yyyy-MM-dd 14:00:00")
$closing3 = $today.AddDays(12).ToString("yyyy-MM-dd 10:30:00")

$inputFile = ".\data\demo\du-lieu-mau.csv"
$exportFile = ".\data\demo\du-lieu-da-xuat.xlsx"
$reportFile = ".\data\reports\bao-cao-demo.xlsx"

@"
ma_tbmt,ten_goi_thau,ben_moi_thau,chu_dau_tu,gia_goi_thau,loai_tien,ngay_dang_tai,thoi_diem_dong_thau,url,tep_dinh_kem
IB2600001001,Mua sắm thiết bị chuyển mạch mạng LAN,Trung tâm Công nghệ Thông tin A,Sở Thông tin và Truyền thông A,2500000000 VND,VND,$published,$closing1,https://example.com/tenders/IB2600001001,https://example.com/files/IB2600001001-HSMT.pdf;https://example.com/files/IB2600001001-BOQ.xlsx
IB2600001002,Trang bị hệ thống tường lửa và bản quyền bảo mật,Ban Quản lý Dự án B,Cơ quan B,4800000000 VND,VND,$published,$closing2,https://example.com/tenders/IB2600001002,https://example.com/files/IB2600001002-HSMT.pdf
IB2600001003,Mua sắm máy chủ và hệ thống lưu trữ dữ liệu,Phòng Kế hoạch C,Đơn vị C,7200000000 VND,VND,$published,$closing3,https://example.com/tenders/IB2600001003,
"@.Trim() | Set-Content -Path $inputFile -Encoding utf8

Write-Host "`n[1/4] Khởi tạo database..." -ForegroundColor Yellow
egp-crawler init-db

Write-Host "`n[2/4] Import dữ liệu mẫu..." -ForegroundColor Yellow
egp-crawler import-file $inputFile

Write-Host "`n[3/4] Xuất toàn bộ dữ liệu ra Excel..." -ForegroundColor Yellow
egp-crawler export --format xlsx --output $exportFile

Write-Host "`n[4/4] Tạo báo cáo nhiều sheet..." -ForegroundColor Yellow
egp-crawler report-daily --output $reportFile --days-ahead 7

Write-Host "`nHOÀN TẤT" -ForegroundColor Green
Write-Host "Database:    .\data\egp.db"
Write-Host "CSV mẫu:     $inputFile"
Write-Host "Excel xuất:  $exportFile"
Write-Host "Báo cáo:     $reportFile"
Write-Host "`nMở thư mục kết quả bằng lệnh:"
Write-Host "explorer .\data"
