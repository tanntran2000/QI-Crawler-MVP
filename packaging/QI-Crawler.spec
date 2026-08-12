# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules


ROOT = Path(SPECPATH).parent.resolve()
BROWSER_ROOT = Path(
    os.environ.get(
        "QI_CRAWLER_BROWSER_DIR",
        Path(os.environ["LOCALAPPDATA"]) / "ms-playwright",
    )
).resolve()

if not BROWSER_ROOT.is_dir():
    raise SystemExit(
        "Khong tim thay Playwright Chromium. "
        "Chay: .\\.venv\\Scripts\\python.exe -m playwright install chromium"
    )

playwright_datas, playwright_binaries, playwright_hidden = collect_all("playwright")

datas = [
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "alembic"), "alembic"),
    (str(ROOT / "alembic.ini"), "."),
    (str(ROOT / "config.example.yaml"), "."),
    (str(ROOT / "keyword-groups.yaml"), "."),
    (str(BROWSER_ROOT), "browsers"),
]
datas += playwright_datas

hiddenimports = collect_submodules("qi_crawler") + playwright_hidden

analysis = Analysis(
    [str(ROOT / "packaging" / "qi_crawler_gui_entry.py")],
    pathex=[str(ROOT / "src")],
    binaries=playwright_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="QI-Crawler",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    contents_directory="runtime",
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

collection = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="QI-Crawler",
)
