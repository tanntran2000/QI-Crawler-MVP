# -*- mode: python ; coding: utf-8 -*-

import importlib.util
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

def _active_pyside6_root() -> Path:
    module_spec = importlib.util.find_spec("PySide6")
    locations = module_spec.submodule_search_locations if module_spec else None
    if not locations:
        raise SystemExit("Khong xac dinh duoc PySide6 package root")
    return Path(next(iter(locations))).resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def filter_foreign_unversioned_icu_binaries(binaries, pyside_root: Path):
    """Keep ICU binaries owned by PySide6; drop foreign unversioned copies."""
    icu_names = {"icuuc.dll", "icuin.dll", "icudt.dll"}
    filtered = []
    for binary in binaries:
        destination, source, *_ = binary
        name = Path(destination).name.lower()
        is_unversioned_icu = name in icu_names or name.startswith(("icuin", "icudt"))
        if is_unversioned_icu and not _is_within(Path(source).resolve(), pyside_root):
            continue
        filtered.append(binary)
    return filtered


PYSIDE6_ROOT = _active_pyside6_root()

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
analysis.binaries = filter_foreign_unversioned_icu_binaries(analysis.binaries, PYSIDE6_ROOT)

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
