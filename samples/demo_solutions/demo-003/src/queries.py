"""Query layer — batch lookup optimized for platform secret tests."""

from __future__ import annotations

import sqlite3


def batch_session_lookup(conn: sqlite3.Connection, event_ids: list[int]) -> list[sqlite3.Row]:
    """Single round-trip IN query instead of per-id loop."""
    if not event_ids:
        return []
    placeholders = ",".join("?" * len(event_ids))
    cur = conn.execute(
        f"""
        SELECT s.id, s.event_id, s.cache_status, s.response_time_ms,
               e.execution_time_ms, e.table_name
        FROM sessions s
        JOIN events e ON e.id = s.event_id
        WHERE s.event_id IN ({placeholders})
        """,
        event_ids,
    )
    return cur.fetchall()


def count_events_over_threshold(conn: sqlite3.Connection, threshold_ms: float) -> int:
    cur = conn.execute(
        "SELECT COUNT(*) FROM events WHERE execution_time_ms > ?",
        (threshold_ms,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0
