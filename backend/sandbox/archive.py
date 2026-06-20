"""Safe ZIP pack/unpack for student project submissions."""

from __future__ import annotations

import io
import zipfile
from pathlib import PurePosixPath

MAX_FILES = 50
MAX_TOTAL_BYTES = 500_000
MAX_ZIP_BYTES = 600_000


class ArchiveError(ValueError):
    pass


def _safe_relative_path(name: str) -> str:
    normalized = PurePosixPath(name.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ArchiveError(f"Unsafe path in archive: {name}")
    return str(normalized)


def extract_zip(data: bytes) -> dict[str, str]:
    """Extract a ZIP archive into a path → content dict."""
    if len(data) > MAX_ZIP_BYTES:
        raise ArchiveError(f"Archive exceeds {MAX_ZIP_BYTES} bytes")

    files: dict[str, str] = {}
    total_bytes = 0

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            rel = _safe_relative_path(info.filename)
            if not rel or rel.startswith("__MACOSX/"):
                continue
            content_bytes = zf.read(info)
            total_bytes += len(content_bytes)
            if len(files) >= MAX_FILES:
                raise ArchiveError(f"Archive exceeds {MAX_FILES} files")
            if total_bytes > MAX_TOTAL_BYTES:
                raise ArchiveError(f"Archive exceeds {MAX_TOTAL_BYTES} bytes")
            try:
                files[rel] = content_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ArchiveError(f"Non-text file not allowed: {rel}") from exc

    if not files:
        raise ArchiveError("Archive contains no files")
    return files


def build_zip(files: dict[str, str]) -> bytes:
    """Pack *files* into a ZIP archive."""
    if len(files) > MAX_FILES:
        raise ArchiveError(f"Too many files: {len(files)}")
    total = sum(len(c.encode("utf-8")) for c in files.values())
    if total > MAX_TOTAL_BYTES:
        raise ArchiveError(f"Content exceeds {MAX_TOTAL_BYTES} bytes")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in sorted(files.items()):
            safe = _safe_relative_path(path)
            zf.writestr(safe, content)
    return buf.getvalue()
