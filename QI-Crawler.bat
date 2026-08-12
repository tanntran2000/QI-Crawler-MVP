@echo off
setlocal
chcp 65001 >nul

set "QI_PROJECT_DIR=%~dp0"
pushd "%QI_PROJECT_DIR%" >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong the mo thu muc QI-Crawler.
    echo Vui long lien he IT de kiem tra thu muc cai dat.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [LOI] Chua tim thay moi truong .venv cua QI-Crawler.
    echo Vui long lien he IT de cai dat QI-Crawler tren may nay.
    popd
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [LOI] Khong the kich hoat QI-Crawler.
    echo Vui long lien he IT de kiem tra .venv.
    popd
    pause
    exit /b 1
)

if not exist ".venv\Scripts\QI-Crawler.exe" (
    echo [LOI] Chua tim thay lenh QI-Crawler trong .venv.
    echo Vui long lien he IT de cai dat lai ung dung.
    popd
    pause
    exit /b 1
)

set "PYTHONUTF8=1"
QI-Crawler menu
set "QI_EXIT_CODE=%ERRORLEVEL%"

if not "%QI_EXIT_CODE%"=="0" (
    echo.
    echo [LOI] QI-Crawler khong khoi dong hoac da dung bat thuong.
    echo Vui long chup man hinh nay va gui cho IT.
    popd
    pause
    exit /b %QI_EXIT_CODE%
)

popd
exit /b 0
