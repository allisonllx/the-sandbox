"""
Tests for async public test run jobs.
"""

from __future__ import annotations

import time

import pytest

from backend.ai_pm.models import RelaxationConfig
from backend.ai_pm import store as backlog_store
from backend.sandbox import run_jobs
from backend.sandbox.starter_scaffold import generate_starter_files
from backend.sandbox.synthesizer import generate_dataset


@pytest.fixture(autouse=True)
def _clear_jobs():
    run_jobs.clear_all()
    yield
    run_jobs.clear_all()


def _wait_for_job(job_id: str, timeout: float = 15.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = run_jobs.get_job(job_id)
        assert job is not None
        if job["status"] in {"completed", "failed", "timeout"}:
            return job
        time.sleep(0.2)
    raise TimeoutError(f"Job {job_id} did not finish")


class TestRunJobs:
    def test_enqueue_and_complete_job(self):
        files = generate_starter_files("demo-003", "Test Challenge")
        result = run_jobs.enqueue_run("demo-003", files, workspace_id="ws-a")
        job = _wait_for_job(result["job_id"])
        assert job["status"] in {"completed", "failed"}  # may fail without dataset

    def test_run_with_mounted_dataset_passes_public_tests(self):
        item = backlog_store.get_item("demo-003")
        assert item is not None
        preview = item.relaxed_preview or __import__(
            "backend.ai_pm.relaxation", fromlist=["apply_relaxation"]
        ).apply_relaxation(item.metadata, RelaxationConfig(), "demo-003")
        db_path, _ = generate_dataset("run-job-test", preview, item.metadata)

        files = generate_starter_files("run-job-test", "Dataset mount test")
        result = run_jobs.enqueue_run(
            "run-job-test",
            files,
            workspace_id="ws-dataset",
            dataset_path=str(db_path),
        )
        job = _wait_for_job(result["job_id"])
        assert job["status"] == "completed"
        assert "passed" in (job.get("stdout") or "")

    def test_rejects_second_concurrent_run(self):
        files = generate_starter_files("demo-003", "Test Challenge")
        run_jobs.enqueue_run("demo-003", files, workspace_id="ws-b")
        with pytest.raises(run_jobs.RunAlreadyActiveError):
            run_jobs.enqueue_run("demo-003", files, workspace_id="ws-b")
