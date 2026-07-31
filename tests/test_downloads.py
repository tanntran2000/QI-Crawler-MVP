from pathlib import Path

import pytest

from qi_crawler.downloads import normalize_extension, safe_filename, unique_destination


def test_safe_filename_removes_path_and_windows_characters():
    assert safe_filename(r"..\folder\HSMT:2026?.pdf") == "HSMT_2026_.pdf"


def test_unique_destination_does_not_overwrite(tmp_path: Path):
    first = tmp_path / "file.pdf"
    first.write_bytes(b"old")
    assert unique_destination(tmp_path, "file.pdf") == tmp_path / "file_2.pdf"


def test_normalize_extension_from_mime():
    assert normalize_extension("HSMT", "application/pdf", [".pdf"]) == "HSMT.pdf"
    with pytest.raises(ValueError):
        normalize_extension("script.exe", "application/octet-stream", [".pdf"])
