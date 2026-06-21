"""SQLite connection helper for the sandbox dataset."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "sandbox.sqlite"


def get_connection() -> sqlite3.Connection:
    """Open the challenge SQLite database."""
    db_path = os.environ.get("SANDBOX_DB", str(DEFAULT_DB))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
