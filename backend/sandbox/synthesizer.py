"""
Procedural SQLite dataset generator.

Creates a synthetic database seeded from relaxed challenge metadata.
Injects real-world anomalies for students to diagnose:

  1. NULL values in a frequently-filtered column
  2. Missing index on a high-cardinality filter column (table scans)
  3. Unindexed foreign-key join path (nested loop on large tables)
"""

from __future__ import annotations

import hashlib
import random
import sqlite3
from pathlib import Path

from ..ai_pm.models import RelaxedPreview
from ..privacy_proxy.models import SanitizedMetadata

_DATASET_ROOT = Path(__file__).resolve().parent.parent / "generated_datasets"

ANOMALY_DESCRIPTIONS = [
    "NULL values injected in events.query_hash (~8% of rows)",
    "No index on events.execution_time_ms — filter queries perform full table scans",
    "sessions.event_id join is unindexed — large nested-loop joins under load",
]


def sqlite_data_doc(*, anomalies: list[str] | None = None) -> str:
    """Student-facing schema reference — visible in the browser file tree."""
    anomaly_lines = "\n".join(f"- {a}" for a in (anomalies or ANOMALY_DESCRIPTIONS))
    return f"""# Challenge dataset reference

Read this file in the browser workspace before editing query code. You do **not**
need to download the SQLite file to understand the schema.

## Tables

### `events`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Event identifier |
| `user_id` | INTEGER | Filter/join key (indexed) |
| `query_hash` | TEXT | Nullable — ~8% NULL rows injected |
| `execution_time_ms` | REAL | Latency metric — **no index** (anomaly) |
| `table_name` | TEXT | Logical table label |
| `index_hit` | INTEGER | 0/1 cache hit flag |
| `rows_scanned` | INTEGER | Scan volume hint |

### `sessions`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Session row id |
| `event_id` | INTEGER | FK to `events.id` — **no index** (anomaly) |
| `cache_status` | TEXT | HIT / MISS / STALE / BYPASS |
| `ttl_seconds` | INTEGER | Cache TTL |
| `response_time_ms` | REAL | End-to-end response time |

## Relationships

- `sessions.event_id` → `events.id` (many sessions per event possible)
- Typical student task: optimize `batch_session_lookup` and threshold counts in `src/queries.py`

## Known anomalies (for diagnosis)

{anomaly_lines}

## Browser vs local

- **Run Public Tests** in the platform mounts `sandbox.sqlite` for you automatically.
- Download **Dataset (.sqlite)** from the header only if you prefer a local IDE.
"""


def _rng_for_challenge(challenge_id: str) -> random.Random:
    digest = hashlib.md5(challenge_id.encode()).hexdigest()
    return random.Random(int(digest[:8], 16))


def _row_count(preview: RelaxedPreview, metadata: SanitizedMetadata) -> int:
    scale = preview.relaxed_row_scale or metadata.approximate_row_scale or 1000
    return max(500, min(scale, 5000))


def generate_dataset(
    challenge_id: str,
    preview: RelaxedPreview,
    metadata: SanitizedMetadata,
) -> tuple[Path, list[str]]:
    """
    Build a SQLite file for *challenge_id* and return (path, anomaly descriptions).

    The file is written to backend/generated_datasets/{challenge_id}.sqlite
    """
    _DATASET_ROOT.mkdir(parents=True, exist_ok=True)
    db_path = _DATASET_ROOT / f"{challenge_id}.sqlite"

    if db_path.exists():
        db_path.unlink()

    rng = _rng_for_challenge(challenge_id)
    n_events = _row_count(preview, metadata)
    n_sessions = max(200, n_events // 3)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            query_hash TEXT,
            execution_time_ms REAL NOT NULL,
            table_name TEXT NOT NULL,
            index_hit INTEGER,
            rows_scanned INTEGER NOT NULL
        );
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY,
            event_id INTEGER NOT NULL,
            cache_status TEXT NOT NULL,
            ttl_seconds INTEGER NOT NULL,
            response_time_ms REAL NOT NULL
        );
        """
    )

    table_names = ["users", "orders", "inventory", "audit_log", "metrics"]
    cache_statuses = ["HIT", "MISS", "STALE", "BYPASS"]

    events: list[tuple] = []
    for i in range(1, n_events + 1):
        # Anomaly 1: ~8% NULL query_hash
        if rng.random() < 0.08:
            query_hash = None
        else:
            query_hash = hashlib.sha256(f"{challenge_id}:{i}".encode()).hexdigest()[:16]

        execution_time_ms = round(rng.uniform(0.5, 120.0), 2)
        # Skew some rows slow (index miss pattern)
        if rng.random() < 0.15:
            execution_time_ms = round(rng.uniform(800.0, 5000.0), 2)

        events.append(
            (
                i,
                rng.randint(1, 5000),
                query_hash,
                execution_time_ms,
                rng.choice(table_names),
                1 if rng.random() > 0.35 else 0,
                rng.randint(1, 500_000),
            )
        )

    cur.executemany(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)",
        events,
    )

    sessions: list[tuple] = []
    for i in range(1, n_sessions + 1):
        event_id = rng.randint(1, n_events)
        sessions.append(
            (
                i,
                event_id,
                rng.choice(cache_statuses),
                rng.choice([60, 300, 900, 3600]),
                round(rng.uniform(1.0, 250.0), 2),
            )
        )

    cur.executemany(
        "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
        sessions,
    )

    # Anomaly 2 & 3: deliberately omit indexes on execution_time_ms and sessions.event_id
    cur.execute("CREATE INDEX idx_events_user_id ON events(user_id)")

    conn.commit()
    conn.close()

    return db_path, list(ANOMALY_DESCRIPTIONS)


def verify_anomalies(db_path: Path) -> dict[str, bool]:
    """Check that expected anomalies exist — used in tests."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM events WHERE query_hash IS NULL")
    null_count = cur.fetchone()[0]

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'"
    )
    event_indexes = {row[0] for row in cur.fetchall()}
    has_exec_index = any("execution_time" in idx for idx in event_indexes)

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='sessions'"
    )
    session_indexes = {row[0] for row in cur.fetchall()}
    has_session_fk_index = any("event_id" in idx for idx in session_indexes)

    conn.close()

    return {
        "has_null_query_hash": null_count > 0,
        "missing_execution_time_index": not has_exec_index,
        "missing_session_event_id_index": not has_session_fk_index,
    }
