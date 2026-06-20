"""In-process async Run jobs for public tests (MVP — no Redis)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

_JOB_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "jobs"
_RUN_TIMEOUT_SEC = 30
_MAX_ACTIVE_JOBS = 10

_lock = threading.Lock()
_active_by_workspace: dict[str, str] = {}
_active_count = 0


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    timeout = "timeout"


class RunAlreadyActiveError(Exception):
    pass


class RunnerBusyError(Exception):
    pass


def _job_dir(job_id: str) -> Path:
    return _JOB_ROOT / job_id


def _write_meta(job_id: str, meta: dict) -> None:
    path = _job_dir(job_id)
    path.mkdir(parents=True, exist_ok=True)
    (path / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _read_meta(job_id: str) -> dict | None:
    meta_path = _job_dir(job_id) / "meta.json"
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _run_pytest(workspace_dir: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_public.py", "-v", "--tb=short"],
        cwd=str(workspace_dir),
        capture_output=True,
        text=True,
        timeout=_RUN_TIMEOUT_SEC,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _execute_job(job_id: str, files: dict[str, str]) -> None:
    global _active_count
    meta = _read_meta(job_id)
    if not meta:
        return

    meta["status"] = JobStatus.running.value
    meta["started_at"] = datetime.now(timezone.utc).isoformat()
    _write_meta(job_id, meta)

    job_path = _job_dir(job_id)
    job_path.mkdir(parents=True, exist_ok=True)
    stdout_path = job_path / "stdout.txt"
    stderr_path = job_path / "stderr.txt"

    try:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            for rel, content in files.items():
                target = work / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            exit_code, stdout, stderr = _run_pytest(work)
            meta["exit_code"] = exit_code
            meta["status"] = (
                JobStatus.completed.value if exit_code == 0 else JobStatus.failed.value
            )
    except subprocess.TimeoutExpired:
        meta["exit_code"] = None
        meta["status"] = JobStatus.timeout.value
        stdout = ""
        stderr = f"Run exceeded {_RUN_TIMEOUT_SEC}s timeout"
    except Exception as exc:  # noqa: BLE001 — job runner must capture all failures
        meta["exit_code"] = 1
        meta["status"] = JobStatus.failed.value
        stdout = ""
        stderr = str(exc)

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    meta["finished_at"] = datetime.now(timezone.utc).isoformat()
    _write_meta(job_id, meta)

    workspace_id = meta.get("workspace_id")
    with _lock:
        _active_count = max(0, _active_count - 1)
        if workspace_id and _active_by_workspace.get(workspace_id) == job_id:
            del _active_by_workspace[workspace_id]


def enqueue_run(
    challenge_id: str,
    files: dict[str, str],
    workspace_id: str | None = None,
) -> dict:
    global _active_count

    with _lock:
        if _active_count >= _MAX_ACTIVE_JOBS:
            raise RunnerBusyError("Runner pool is busy")
        if workspace_id and workspace_id in _active_by_workspace:
            raise RunAlreadyActiveError("A run is already active for this workspace")
        _active_count += 1
        if workspace_id:
            job_id = str(uuid.uuid4())
            _active_by_workspace[workspace_id] = job_id
        else:
            job_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc).isoformat()
    meta = {
        "job_id": job_id,
        "challenge_id": challenge_id,
        "workspace_id": workspace_id,
        "status": JobStatus.queued.value,
        "exit_code": None,
        "started_at": None,
        "finished_at": None,
        "created_at": now,
    }
    _write_meta(job_id, meta)

    thread = threading.Thread(
        target=_execute_job,
        args=(job_id, files),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id, "status": JobStatus.queued.value}


def get_job(job_id: str) -> dict | None:
    meta = _read_meta(job_id)
    if not meta:
        return None

    job_path = _job_dir(job_id)
    stdout = (job_path / "stdout.txt").read_text(encoding="utf-8") if (job_path / "stdout.txt").exists() else ""
    stderr = (job_path / "stderr.txt").read_text(encoding="utf-8") if (job_path / "stderr.txt").exists() else ""

    return {
        "job_id": job_id,
        "status": meta.get("status"),
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": meta.get("exit_code"),
        "started_at": meta.get("started_at"),
        "finished_at": meta.get("finished_at"),
    }


def clear_all() -> None:
    """Test helper."""
    global _active_count
    with _lock:
        _active_by_workspace.clear()
        _active_count = 0
    if _JOB_ROOT.exists():
        import shutil

        shutil.rmtree(_JOB_ROOT)
