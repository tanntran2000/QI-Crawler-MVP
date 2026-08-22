# Build QI-Crawler standalone va installer tren Windows

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

## 4. Tao Setup cho Team Bid

Cai [Inno Setup 7](https://jrsoftware.org/isdl.php) tren may build, sau do chay:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

Lenh tren chi tao build local trong `dist`; khong thay doi thu muc user-visible
`Crawler tool`. Chi publish sau khi da merge vao `main`, working tree sach va
da smoke-test:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1 -Publish
```

`-Publish` tao candidate trong staging, kiem tra EXE/installer va sau do cap nhat
an toan:

```text
..\Crawler tool\
|-- Current\
|   |-- QI-Crawler\QI-Crawler.exe
|   |-- QI-Crawler-Setup-v0.7.1.exe
|   `-- BUILD_INFO.txt
`-- Previous\
```

`BUILD_INFO.txt` ghi version, commit SHA, branch, thoi diem build va SHA-256 cua
EXE/installer. Neu staging hoac verification that bai, `Current` duoc giu nguyen.
Chi giu mot ban `Previous`; cac report/DB/documents/session nam ngoai release.

Neu Inno Setup nam o mot vi tri rieng, dat duong dan compiler trong phien
PowerShell truoc khi build:

```powershell
$env:QI_CRAWLER_ISCC = "C:\Tools\Inno Setup 7\ISCC.exe"
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

Ket qua la mot file duy nhat:

```text
dist\installer\QI-Crawler-Setup-v0.7.1.exe
```

Nguoi dung cuoi chi can chay Setup. Setup tao shortcut Start Menu va Desktop,
dong goi day du Qt/PySide6, Playwright va Chromium. Khong can Python, VS Code hay Git.

Setup chi ghi application vao `%LOCALAPPDATA%\Programs\QI-Crawler`. Database, document HSMT,
report, config va session luon nam o `%LOCALAPPDATA%\QI-Crawler`, nen upgrade va uninstall
khong xoa du lieu Bid.

## 5. Du lieu nguoi dung

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

## 6. Browser runtime

Spec bundle thu muc `%LOCALAPPDATA%\ms-playwright` vao `runtime\browsers` va dat
`PLAYWRIGHT_BROWSERS_PATH` khi khoi dong. Neu Chromium bi thieu, GUI hien loi tieng
Viet va dung; ung dung khong tu tai ngầm.

## 7. Kiem tra tren may Windows sach

Copy toan bo `dist\QI-Crawler` sang may khong co Python/VS Code, sau do double-click
`QI-Crawler.exe`. Kiem tra:

1. GUI hien `QI-Crawler v0.7.1`.
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
