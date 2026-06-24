"""
Ephemeral Docker runner for platform secret tests.

Student code NEVER executes on the host — only inside an isolated container
with no network, memory/CPU limits, and dropped capabilities.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_IMAGE = "the-sandbox-runner:latest"
_DOCKERFILE = Path(__file__).resolve().parents[2] / "docker" / "sandbox-runner" / "Dockerfile"
_SECRET_TEST = Path(__file__).resolve().parent / "secret_tests" / "test_secret.py"
_RUN_TIMEOUT_SEC = 45
_MEMORY = "512m"
_CPUS = "1.0"


@dataclass
class PlatformRunResult:
    runner: str  # docker | unavailable
    exit_code: int | None = None
    tests_passed: int = 0
    tests_failed: int = 0
    tests_total: int = 0
    duration_sec: float = 0.0
    stdout: str = ""
    stderr: str = ""
    notes: list[str] = field(default_factory=list)


def docker_available() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def image_exists() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "image", "inspect", _IMAGE],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def build_runner_image() -> bool:
    """Build the sandbox runner image if Dockerfile is present."""
    if not _DOCKERFILE.exists():
        logger.warning("Sandbox runner Dockerfile not found: %s", _DOCKERFILE)
        return False
    context = _DOCKERFILE.parent
    logger.info("Building assessor image %s (may take ~1 min on first run)...", _IMAGE)
    proc = subprocess.run(
        ["docker", "build", "-t", _IMAGE, str(context)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "")[-2000:]
        logger.error("Docker build failed for %s: %s", _IMAGE, err)
        return False
    logger.info("Assessor image %s ready", _IMAGE)
    return True


def ensure_runner_image() -> bool:
    """
    Ensure the-sandbox-runner image exists when Docker is up.

    Called on API startup and again before the first secret-test run.
    """
    if not docker_available():
        return False
    if image_exists():
        return True
    return build_runner_image()


def _parse_pytest_summary(stdout: str) -> tuple[int, int, int]:
    """Parse pytest short summary lines like '4 passed, 1 failed'."""
    passed = failed = 0
    match = re.search(r"(\d+)\s+passed", stdout)
    if match:
        passed = int(match.group(1))
    match = re.search(r"(\d+)\s+failed", stdout)
    if match:
        failed = int(match.group(1))
    errors = 0
    match = re.search(r"(\d+)\s+error", stdout)
    if match:
        errors = int(match.group(1))
        failed += errors
    total = passed + failed
    return passed, failed, total


def _required_files_present(files: dict[str, str]) -> bool:
    return "src/queries.py" in files and "src/db.py" in files


def run_platform_assessment(
    files: dict[str, str],
    dataset_path: str | Path | None,
) -> PlatformRunResult:
    """
    Run track-standard secret tests against *files* inside Docker.

    Returns structured result for platform_technical scoring.
    """
    if not docker_available():
        return PlatformRunResult(
            runner="unavailable",
            notes=["Docker not available — secret tests skipped. Install Docker for full platform grading."],
        )

    if not _required_files_present(files):
        return PlatformRunResult(
            runner="unavailable",
            notes=["Submission missing src/queries.py or src/db.py — cannot run secret tests."],
        )

    ds = Path(dataset_path) if dataset_path else None
    if not ds or not ds.exists():
        return PlatformRunResult(
            runner="unavailable",
            notes=["Challenge dataset not found — secret tests skipped."],
        )

    if not ensure_runner_image():
        return PlatformRunResult(
            runner="unavailable",
            notes=[
                f"Runner image {_IMAGE} not available "
                f"(auto-build failed — ensure Docker is running and retry submit)."
            ],
        )

    if not _SECRET_TEST.exists():
        return PlatformRunResult(
            runner="unavailable",
            notes=["Secret test bundle missing on server."],
        )

    workdir = Path(tempfile.mkdtemp(prefix="sandbox-assess-"))
    try:
        for rel, content in files.items():
            target = workdir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        shutil.copy2(ds, workdir / "sandbox.sqlite")

        cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            _MEMORY,
            "--memory-swap",
            _MEMORY,
            "--cpus",
            _CPUS,
            "--pids-limit",
            "128",
            "--security-opt",
            "no-new-privileges",
            "--cap-drop",
            "ALL",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "-v",
            f"{workdir.resolve()}:/workspace:rw",
            "-v",
            f"{_SECRET_TEST.resolve()}:/secret_tests/test_secret.py:ro",
            "-e",
            "SANDBOX_DB=/workspace/sandbox.sqlite",
            "-e",
            "PYTHONPATH=/workspace",
            "-w",
            "/workspace",
            _IMAGE,
            "python",
            "-m",
            "pytest",
            "/secret_tests/test_secret.py",
            "-q",
            "--tb=line",
        ]

        import time

        start = time.perf_counter()
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_RUN_TIMEOUT_SEC,
        )
        duration = time.perf_counter() - start

        passed, failed, total = _parse_pytest_summary(proc.stdout + proc.stderr)
        notes = ["Secret tests executed in isolated Docker container (network disabled)."]
        if proc.returncode != 0 and total == 0:
            notes.append("Pytest did not report test counts — check submission structure.")
            failed = 1
            total = 1

        return PlatformRunResult(
            runner="docker",
            exit_code=proc.returncode,
            tests_passed=passed,
            tests_failed=failed,
            tests_total=total,
            duration_sec=round(duration, 2),
            stdout=proc.stdout[-4000:] if proc.stdout else "",
            stderr=proc.stderr[-2000:] if proc.stderr else "",
            notes=notes,
        )
    except subprocess.TimeoutExpired:
        return PlatformRunResult(
            runner="docker",
            exit_code=None,
            duration_sec=float(_RUN_TIMEOUT_SEC),
            notes=[f"Secret test run exceeded {_RUN_TIMEOUT_SEC}s timeout."],
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def run_result_to_json(result: PlatformRunResult) -> dict:
    """Serialize for scorecard notes / debugging."""
    return {
        "runner": result.runner,
        "exit_code": result.exit_code,
        "tests_passed": result.tests_passed,
        "tests_failed": result.tests_failed,
        "tests_total": result.tests_total,
        "duration_sec": result.duration_sec,
    }
