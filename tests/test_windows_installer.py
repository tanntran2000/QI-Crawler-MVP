from pathlib import Path

ROOT = Path(__file__).parent.parent
INSTALLER = ROOT / "packaging" / "QI-Crawler.iss"
BUILD_SCRIPT = ROOT / "build_installer.ps1"


def test_installer_is_per_user_and_preserves_bid_data() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert '#define AppVersion "0.7.0"' in script
    assert "OutputBaseFilename=QI-Crawler-Setup-v{#AppVersion}" in script
    assert "DefaultDirName={localappdata}\\Programs\\QI-Crawler" in script
    assert "PrivilegesRequired=lowest" in script
    assert "Source: \"..\\dist\\QI-Crawler\\*\"" in script
    assert "{autoprograms}\\QI-Crawler" in script
    assert "{autodesktop}\\QI-Crawler" in script
    assert "[UninstallDelete]" not in script
    assert "{userappdata}" not in script
    assert "{localappdata}\\QI-Crawler" not in script


def test_installer_build_is_reproducible_from_safe_onedir_bundle() -> None:
    script = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert "build_windows.ps1" in script
    assert "QI-Crawler.iss" in script
    assert "ISCC.exe" in script
    assert "QI_CRAWLER_ISCC" in script
    assert "Inno Setup 7" in script
    assert "$iscc = @($isccCandidates)[0]" in script
    assert "QI-Crawler-Setup-v0.7.0.exe" in script
    assert "dist\\QI-Crawler\\QI-Crawler.exe" in script
