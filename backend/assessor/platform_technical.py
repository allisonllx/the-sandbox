"""Platform Signal — technical track (track-standard, globally comparable)."""

from __future__ import annotations

from pathlib import Path

from ..sandbox.models import SubmissionRecord
from .docker_runner import PlatformRunResult, run_platform_assessment
from .models import ScoreLayer
from .security_scan import scan_submission


def _tests_passed_score(result: PlatformRunResult) -> int:
    if result.tests_total <= 0:
        return 0
    return int(round(100 * result.tests_passed / result.tests_total))


def _perf_score(result: PlatformRunResult) -> int:
    if result.runner != "docker" or result.tests_total <= 0:
        return 0
    if result.tests_passed == 0:
        return 0
    # Perf test is last in secret bundle — if all passed, perf likely ok
    if result.exit_code == 0:
        return 100
    # Partial pass — scale by pass rate with cap
    return min(70, _tests_passed_score(result))


def _resource_efficiency_score(result: PlatformRunResult) -> int:
    if result.runner != "docker":
        return 0
    if result.duration_sec <= 0:
        return 50
    if result.duration_sec <= 5:
        return 100
    if result.duration_sec <= 15:
        return 80
    if result.duration_sec <= 30:
        return 60
    return max(20, 100 - int(result.duration_sec * 2))


def assess_platform_technical(
    record: SubmissionRecord,
    *,
    dataset_path: str | Path | None = None,
) -> ScoreLayer:
    """
    Objective technical rubric — same dimensions for every technical challenge.

    Secret tests run in Docker (no network, resource limits). Security scan
    runs statically on host before container execution.
    """
    security_baseline, violations = scan_submission(record.files)
    notes: list[str] = [
        "Execution Points derive from platform signal only.",
        f"Files submitted: {len(record.files)}",
    ]
    if violations:
        notes.extend(violations[:3])

    run_result = run_platform_assessment(record.files, dataset_path)

    if run_result.runner == "docker":
        notes.extend(run_result.notes)
        dimensions = {
            "tests_passed": _tests_passed_score(run_result),
            "perf_score": _perf_score(run_result),
            "security_baseline": security_baseline,
            "resource_efficiency": _resource_efficiency_score(run_result),
        }
        summary = (
            f"Platform signal: {run_result.tests_passed}/{run_result.tests_total} secret tests passed (Docker)."
            if run_result.tests_total
            else "Platform signal: secret test run completed."
        )
    else:
        notes.extend(run_result.notes)
        # Degraded heuristic when Docker/dataset unavailable — no host execution
        line_count = sum(len(c.splitlines()) for c in record.files.values())
        has_structure = "src/queries.py" in record.files
        dimensions = {
            "tests_passed": min(40, 20 + (10 if has_structure else 0)),
            "perf_score": min(40, 15 + line_count // 10),
            "security_baseline": security_baseline,
            "resource_efficiency": min(40, 20 + (5 if has_structure else 0)),
        }
        summary = "Platform signal (degraded) — Docker secret tests not run."

    score = int(round(sum(dimensions.values()) / len(dimensions)))

    return ScoreLayer(
        dimensions=dimensions,
        score=score,
        summary=summary,
        notes=notes,
    )
