"""Generate per-challenge starter file trees for the student workspace."""

from __future__ import annotations

STARTER_PATHS = (
    "README.md",
    "docs/DATA.md",
    "src/db.py",
    "src/queries.py",
    "src/main.py",
    "tests/test_public.py",
)


def format_edit_targets(edit_targets: list[str]) -> str:
    """Human-readable backtick list for PRD / README copy."""
    if not edit_targets:
        return "`src/`"
    if len(edit_targets) == 1:
        return f"`{edit_targets[0]}`"
    return ", ".join(f"`{t}`" for t in edit_targets)


def platform_sandbox_instructions(
    edit_targets: list[str] | None = None,
    *,
    data_plane: str = "none",
) -> list[str]:
    """Steps shown in the Micro-PRD — browser-first; local download is optional."""
    targets = edit_targets or ["src/queries.py"]
    focus = format_edit_targets(targets)
    uses_sqlite = data_plane == "sqlite"

    steps = [
        "Read the Context and Success criteria in the left panel.",
        "The starter project loads automatically in the editor (see the file tree). "
        f"Focus your changes on {focus}.",
    ]
    if uses_sqlite:
        steps.extend(
            [
                "Open **docs/DATA.md** in the file tree for table columns, relationships, "
                "and known anomalies — you do not need to download the database to start.",
                "Click **Run Public Tests** — the platform mounts the challenge dataset automatically.",
                "Optional: download **Dataset (.sqlite)** from the header only if you prefer a local IDE.",
            ]
        )
    else:
        steps.append(
            "Click **Run Public Tests** — starter files and tests are self-contained in the browser."
        )
    steps.extend(
        [
            "Edit existing starter files only — you cannot add new files in the browser workspace.",
            "When ready, click **Submit Project** to send your edited files for grading.",
            "Optional: download **Starter ZIP** to work locally, then use **Submit ZIP** to upload your project.",
        ]
    )
    return steps


def generate_starter_files(
    challenge_id: str,
    title: str,
    *,
    anomalies: list[str] | None = None,
) -> dict[str, str]:
    """Return a bounded multi-file starter scaffold for *challenge_id*."""
    from .synthesizer import sqlite_data_doc

    return {
        "README.md": _readme(challenge_id, title),
        "docs/DATA.md": sqlite_data_doc(anomalies=anomalies),
        "src/db.py": _db_py(),
        "src/queries.py": _queries_py(),
        "src/main.py": _main_py(),
        "tests/test_public.py": _test_public_py(),
    }


def _readme(challenge_id: str, title: str) -> str:
    return f"""# {title}

Challenge ID: `{challenge_id}`

## Setup (browser-first)

1. Read **docs/DATA.md** for schema and anomalies (visible in the file tree).
2. Edit `src/queries.py` to improve session/event lookup performance.
3. Click **Run Public Tests** in the platform — the dataset is mounted for you.
4. Optional local run: download **Dataset (.sqlite)**, place at `./sandbox.sqlite`, then `pytest tests/test_public.py -v`.

## Project layout

- `docs/DATA.md` — table schema and anomaly notes (read this first)
- `src/db.py` — SQLite connection helper
- `src/queries.py` — query layer (main edit target)
- `src/main.py` — local smoke entrypoint
- `tests/test_public.py` — tests you can run before submit
"""


def _db_py() -> str:
    return '''"""SQLite connection helper for the sandbox dataset."""

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
'''


def _queries_py() -> str:
    return '''"""Query layer — optimize these lookups for the sandbox challenge."""

from __future__ import annotations

import sqlite3


def batch_session_lookup(conn: sqlite3.Connection, event_ids: list[int]) -> list[sqlite3.Row]:
    """
    Return session rows joined with event timing for each event_id.

    TODO: This implementation is intentionally slow (per-id loop + nested join).
    Refactor for fewer round-trips and better index use.
    """
    results: list[sqlite3.Row] = []
    for event_id in event_ids:
        cur = conn.execute(
            """
            SELECT s.id, s.event_id, s.cache_status, s.response_time_ms,
                   e.execution_time_ms, e.table_name
            FROM sessions s
            JOIN events e ON e.id = s.event_id
            WHERE s.event_id = ?
            """,
            (event_id,),
        )
        results.extend(cur.fetchall())
    return results


def count_events_over_threshold(conn: sqlite3.Connection, threshold_ms: float) -> int:
    """Count events slower than threshold — full table scan (no index on execution_time_ms)."""
    cur = conn.execute(
        "SELECT COUNT(*) FROM events WHERE execution_time_ms > ?",
        (threshold_ms,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0
'''


def _main_py() -> str:
    return '''"""Local smoke entrypoint — run with: python -m src.main"""

from __future__ import annotations

from src.db import get_connection
from src.queries import batch_session_lookup, count_events_over_threshold


def main() -> None:
    conn = get_connection()
    try:
        sample_ids = [
            row[0]
            for row in conn.execute("SELECT id FROM events LIMIT 5").fetchall()
        ]
        rows = batch_session_lookup(conn, sample_ids)
        slow = count_events_over_threshold(conn, 500.0)
        print(f"sample sessions: {len(rows)}, slow events (>500ms): {slow}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
'''


def _test_public_py() -> str:
    return '''"""Public tests — runnable before submit (requires sandbox.sqlite)."""

from __future__ import annotations

import sqlite3

import pytest

from src.db import get_connection
from src.queries import batch_session_lookup, count_events_over_threshold


@pytest.fixture
def conn():
    try:
        connection = get_connection()
    except sqlite3.OperationalError as exc:
        pytest.skip(f"sandbox.sqlite not available: {exc}")
    yield connection
    connection.close()


def test_queries_module_imports():
    assert callable(batch_session_lookup)
    assert callable(count_events_over_threshold)


def test_batch_lookup_returns_rows(conn):
    event_ids = [row[0] for row in conn.execute("SELECT id FROM events LIMIT 3").fetchall()]
    assert event_ids
    rows = batch_session_lookup(conn, event_ids)
    assert len(rows) >= 1


def test_count_events_over_threshold(conn):
    count = count_events_over_threshold(conn, 0.0)
    assert count >= 0
'''
