from __future__ import annotations

import hashlib
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


@dataclass(slots=True)
class DownloadedFile:
    file_name: str
    local_path: Path
    sha256: str
    size_bytes: int
    content_type: str | None = None
    source_url: str | None = None
    method: str = "playwright"


def safe_filename(name: str | None, fallback: str = "attachment.bin") -> str:
    """Return a Windows-safe basename; never trust a server-provided filename."""
    cleaned = unquote(name or "").replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned[:180] or fallback


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_destination(directory: Path, filename: str) -> Path:
    destination = directory / filename
    if not destination.exists():
        return destination

    for number in range(2, 100_000):
        candidate = directory / f"{destination.stem}_{number}{destination.suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Không thể tạo tên file duy nhất trong {directory}")


def normalize_extension(
    filename: str,
    content_type: str | None,
    allowed_extensions: list[str],
) -> str:
    """Validate/repair the extension using a conservative allowlist."""
    allowed = {item.lower() for item in allowed_extensions}
    suffix = Path(filename).suffix.lower()
    if suffix in allowed:
        return filename

    mime = (content_type or "").split(";", 1)[0].strip().lower()
    guessed = mimetypes.guess_extension(mime) if mime else None
    if guessed == ".jpe":
        guessed = ".jpg"
    if guessed in allowed:
        return f"{filename}{guessed}"

    raise ValueError(f"Loại tệp không được phép: {content_type or suffix or 'không xác định'}")


def filename_from_url(url: str, fallback: str = "attachment.bin") -> str:
    return safe_filename(urlparse(url).path.rsplit("/", 1)[-1], fallback=fallback)
