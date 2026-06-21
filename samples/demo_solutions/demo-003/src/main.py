"""Local smoke entrypoint — run with: python -m src.main"""

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
