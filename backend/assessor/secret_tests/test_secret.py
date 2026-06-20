"""
Platform secret tests — never shipped in starter scaffold.

Mounted read-only into the assessor Docker container at grading time.
"""

from __future__ import annotations

import time

import pytest

from src.db import get_connection
from src.queries import batch_session_lookup, count_events_over_threshold


@pytest.fixture
def conn():
    connection = get_connection()
    yield connection
    connection.close()


def test_batch_lookup_empty_list(conn):
    assert batch_session_lookup(conn, []) == []


def test_batch_lookup_returns_expected_rows(conn):
    event_ids = [row[0] for row in conn.execute("SELECT id FROM events LIMIT 5").fetchall()]
    assert event_ids
    rows = batch_session_lookup(conn, event_ids)
    assert len(rows) >= 1
    returned_event_ids = {row["event_id"] for row in rows}
    for eid in event_ids:
        assert eid in returned_event_ids


def test_count_threshold_matches_sql(conn):
    threshold = 500.0
    expected = conn.execute(
        "SELECT COUNT(*) FROM events WHERE execution_time_ms > ?",
        (threshold,),
    ).fetchone()[0]
    assert count_events_over_threshold(conn, threshold) == expected


def test_batch_lookup_performance(conn):
    """Platform perf signal — must complete 40 lookups within generous bound."""
    event_ids = [row[0] for row in conn.execute("SELECT id FROM events LIMIT 40").fetchall()]
    assert len(event_ids) >= 10
    start = time.perf_counter()
    batch_session_lookup(conn, event_ids)
    elapsed = time.perf_counter() - start
    assert elapsed < 8.0, f"batch_session_lookup too slow: {elapsed:.2f}s"
