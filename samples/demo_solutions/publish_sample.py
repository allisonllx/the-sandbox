#!/usr/bin/env python3
"""Publish a demo backlog item before submitting a sample solution."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

PUBLISH_BODY: dict[str, dict] = {
    "demo-003": {
        "config": {
            "abstract_logic": True,
            "synthesize_variables": True,
            "abstract_brand": True,
        },
        "reward": {
            "reward_type": "cash_bounty",
            "amount_usd": 500,
            "interview_benchmark": 75,
            "locked": True,
        },
    },
    "demo-004": {
        "config": {
            "abstract_logic": True,
            "synthesize_variables": True,
            "abstract_brand": True,
        },
        "reward": {
            "reward_type": "cash_bounty",
            "amount_usd": 500,
            "locked": True,
        },
        "track": "product_feature",
    },
    "demo-005": {
        "config": {
            "abstract_logic": True,
            "synthesize_variables": True,
            "abstract_brand": True,
            "obfuscate_domain": True,
        },
        "reward": {
            "reward_type": "cash_bounty",
            "amount_usd": 500,
            "locked": True,
        },
        "track": "product_feature",
    },
    "demo-006": {
        "config": {
            "abstract_logic": True,
            "synthesize_variables": True,
            "abstract_brand": True,
        },
        "reward": {
            "reward_type": "cash_bounty",
            "amount_usd": 500,
            "locked": True,
        },
    },
}


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: publish_sample.py <challenge_id> [base_url]", file=sys.stderr)
        return 1

    challenge_id = sys.argv[1]
    base_url = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else "http://localhost:8000"

    if challenge_id not in PUBLISH_BODY:
        known = ", ".join(sorted(PUBLISH_BODY))
        print(f"Unknown or unpublishable demo '{challenge_id}'. Known: {known}", file=sys.stderr)
        print("Note: demo-007 always fails publish (scope cap demo).", file=sys.stderr)
        return 1

    url = f"{base_url}/api/v1/triage/publish/{challenge_id}"
    req = urllib.request.Request(
        url,
        data=json.dumps(PUBLISH_BODY[challenge_id]).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        print(f"Publish failed HTTP {exc.code}:\n{err}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Could not reach {base_url}: {exc.reason}", file=sys.stderr)
        return 1

    print(json.dumps(body, indent=2))
    print(f"\nStudent challenge: http://localhost:3000/student/challenges/{challenge_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
