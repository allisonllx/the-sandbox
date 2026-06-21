#!/usr/bin/env python3
"""Submit a sample solution from samples/demo_solutions/{challenge_id}/."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from load_sample import LANGUAGE_BY_CHALLENGE, load_sample_files

ROOT = Path(__file__).resolve().parent


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: submit_sample.py <challenge_id> [base_url]", file=sys.stderr)
        print("Example: submit_sample.py demo-003 http://localhost:8000", file=sys.stderr)
        return 1

    challenge_id = sys.argv[1]
    base_url = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else "http://localhost:8000"

    if challenge_id not in LANGUAGE_BY_CHALLENGE:
        known = ", ".join(sorted(LANGUAGE_BY_CHALLENGE))
        print(f"Unknown challenge_id '{challenge_id}'. Known: {known}", file=sys.stderr)
        return 1

    sample_dir = ROOT / challenge_id
    files = load_sample_files(sample_dir)
    payload = {
        "mode": "inline",
        "files": files,
        "language": LANGUAGE_BY_CHALLENGE[challenge_id],
    }

    url = f"{base_url}/api/v1/sandbox/challenges/{challenge_id}/submit"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        print(f"Submit failed HTTP {exc.code}:\n{err}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Could not reach {base_url}: {exc.reason}", file=sys.stderr)
        print("Start backend: python -m uvicorn backend.main:app --reload --port 8000", file=sys.stderr)
        return 1

    print(json.dumps(body, indent=2))
    submission_id = body.get("submission_id")
    if submission_id:
        print(f"\nScorecard: {base_url}/api/v1/sandbox/submissions/{submission_id}/scorecard")
        print(f"Match radar: {base_url}/api/v1/triage/backlog/{challenge_id}/matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
