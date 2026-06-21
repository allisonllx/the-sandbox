"""Public tests — runnable before submit (requires sandbox.sqlite)."""

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
