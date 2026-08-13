# Build QI-Crawler standalone tren Windows

Ban WP8-C dung PyInstaller `onedir`. Nguoi dung cuoi nhan **toan bo** thu muc
`dist\QI-Crawler`; khong copy rieng file EXE.

## 1. Chuan bi may build

Dung Windows 64-bit va Python 3.11+:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,build]"
python -m playwright install chromium
```

Lenh `playwright install chromium` la thao tac ro rang tren may build. QI-Crawler.exe
khong tu tai browser khi chay va khong vuot CAPTCHA/403/TLS/security control.

## 2. Quality gate

```powershell
python -m pytest -q
python -m ruff check src tests
```

## 3. Build tai lap

```powershell
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```

Lenh PyInstaller chinh xac duoc script chay:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging\QI-Crawler.spec
```

Ket qua:

```text
dist\QI-Crawler\
|-- QI-Crawler.exe
`-- runtime\
    |-- qi_crawler va dependencies
    |-- templates\
    |-- alembic\
    `-- browsers\
```

## 4. Du lieu nguoi dung

Lan chay dau, ung dung tao va chi ghi vao:

```text
%LOCALAPPDATA%\QI-Crawler\
|-- config.yaml
|-- keyword-groups.yaml
|-- data\
|   |-- database\egp.db
|   |-- reports\
|   |-- sessions\
|   |-- downloads\
|   `-- backups\
|-- documents\
`-- logs\qi-crawler.log
```

Cap nhat bang cach thay thu muc ung dung khong ghi de database, report, session,
documents hay config cua nguoi dung.

## 5. Browser runtime

Spec bundle thu muc `%LOCALAPPDATA%\ms-playwright` vao `runtime\browsers` va dat
`PLAYWRIGHT_BROWSERS_PATH` khi khoi dong. Neu Chromium bi thieu, GUI hien loi tieng
Viet va dung; ung dung khong tu tai ngầm.

## 6. Kiem tra tren may Windows sach

Copy toan bo `dist\QI-Crawler` sang may khong co Python/VS Code, sau do double-click
`QI-Crawler.exe`. Kiem tra:

1. GUI hien `QI-Crawler v0.7.0`.
2. Tim kiem tren database test/da copy vao thu muc user data.
3. Xuat TBMT va mo file Excel.
4. Crawl mot URL chi tiet duoc phep.
5. Scan URL danh sach Coteccons.
6. Mo trinh duyet dang nhap; CAPTCHA/OTP do nguoi dung tu xu ly.

Khong phan phoi file session, database production hoac config chua secret trong bo cai.

Smoke test tu dong voi user data tach biet:

```powershell
$env:QI_CRAWLER_DATA_DIR="$env:TEMP\QI-Crawler-Smoke"
& .\dist\QI-Crawler\QI-Crawler.exe --smoke-test
Get-Content "$env:QI_CRAWLER_DATA_DIR\logs\standalone-smoke.json"
```

Che do tren kiem tra startup database, search, export va khoi dong Chromium. Release engineer
co the kiem tra live single-URL + list scan (van ton trong robots/security policy) bang:

```powershell
& .\dist\QI-Crawler\QI-Crawler.exe --smoke-test-network
```

Khong dung live network smoke neu website dang bao tri/chan truy cap; tuyet doi khong bypass.
