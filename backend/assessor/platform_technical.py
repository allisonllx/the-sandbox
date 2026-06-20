"""Platform Signal — technical track (track-standard, globally comparable)."""

from __future__ import annotations

from ..sandbox.models import SubmissionRecord
from .models import ScoreLayer


def assess_platform_technical(record: SubmissionRecord) -> ScoreLayer:
    """
    Objective technical rubric — same dimensions for every technical challenge.

    Full Docker secret-test grading lands in assessor-001 Phase A.
    """
    line_count = sum(len(c.splitlines()) for c in record.files.values())
    has_readme = any(p.lower().endswith("readme.md") for p in record.files)
    has_tests = any("test" in p.lower() for p in record.files)

    tests_passed = min(100, 50 + (15 if has_tests else 0) + min(20, line_count // 5))
    perf_score = min(100, 45 + line_count // 3)
    security_baseline = min(100, 40 + (10 if has_readme else 0) + (5 if line_count > 20 else 0))
    resource_efficiency = min(100, 50 + min(30, line_count // 4))

    dimensions = {
        "tests_passed": tests_passed,
        "perf_score": perf_score,
        "security_baseline": security_baseline,
        "resource_efficiency": resource_efficiency,
    }
    score = int(round(sum(dimensions.values()) / len(dimensions)))

    return ScoreLayer(
        dimensions=dimensions,
        score=score,
        summary="Platform signal assessed (Docker harness pending assessor-001 Phase A).",
        notes=[
            "Execution Points derive from platform signal only.",
            f"Files submitted: {len(record.files)}",
        ],
    )
