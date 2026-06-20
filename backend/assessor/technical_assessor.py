"""Technical track assessor — MVP stub until Docker harness lands in assessor-001."""

from __future__ import annotations

from ..sandbox.models import SubmissionRecord


def assess_technical_submission(record: SubmissionRecord) -> dict:
    line_count = sum(len(c.splitlines()) for c in record.files.values())
    has_readme = any(p.lower().endswith("readme.md") for p in record.files)
    score = min(100, 40 + line_count // 2 + (10 if has_readme else 0))

    return {
        "track": "technical",
        "dimensions": {
            "Performance": score,
            "Security Resilience": min(100, score - 5),
            "Architectural Elegance": min(100, score + 5),
        },
        "summary": "Queued for full Docker test harness (assessor-001). Preview scores based on submission structure.",
        "notes": [
            "Full pytest + perf grading will replace this stub.",
            f"Files submitted: {len(record.files)}",
        ],
    }
