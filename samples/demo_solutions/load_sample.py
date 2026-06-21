#!/usr/bin/env python3
"""Load a sample solution directory into a files dict for submit API."""

from __future__ import annotations

from pathlib import Path

SKIP_NAMES = {".DS_Store", "__pycache__"}


def load_sample_files(sample_dir: Path) -> dict[str, str]:
    if not sample_dir.is_dir():
        raise FileNotFoundError(f"Sample directory not found: {sample_dir}")

    files: dict[str, str] = {}
    for path in sorted(sample_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIP_NAMES:
            continue
        if any(part.startswith(".") for part in path.relative_to(sample_dir).parts):
            continue
        rel = path.relative_to(sample_dir).as_posix()
        files[rel] = path.read_text(encoding="utf-8")
    if not files:
        raise ValueError(f"No files under {sample_dir}")
    return files


LANGUAGE_BY_CHALLENGE: dict[str, str] = {
    "demo-003": "python",
    "demo-004": "html",
    "demo-005": "html",
    "demo-006": "python",
}
