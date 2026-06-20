"""
Tests for sandbox-001: Public Sandbox Terminal & Micro-PRD Framework.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm import store as backlog_store
from backend.ai_pm.models import BacklogStatus, RelaxationConfig
from backend.main import app
from backend.sandbox import submission_store
from backend.sandbox.synthesizer import generate_dataset, verify_anomalies
from backend.sandbox.starter_scaffold import STARTER_PATHS

client = TestClient(app)


def _publish_demo_item(item_id: str = "demo-003") -> None:
    """Publish a backlog item via the triage API."""
    config = RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=True,
        noise_level=0.3,
    )
    reward = {"reward_type": "cash_bounty", "amount_usd": 500, "interview_benchmark": 75, "locked": True}
    res = client.post(
        f"/api/v1/triage/publish/{item_id}",
        json={"config": config.model_dump(), "reward": reward},
    )
    assert res.status_code == 200, res.text


@pytest.fixture(autouse=True)
def _reset_submissions():
    submission_store.clear()
    yield
    submission_store.clear()


@pytest.fixture(autouse=True)
def _reset_drafts():
    from backend.sandbox import draft_store

    draft_store.clear_all()
    yield
    draft_store.clear_all()


class TestPublishFlow:
    def test_publish_sets_status_published(self):
        _publish_demo_item("demo-002")
        item = backlog_store.get_item("demo-002")
        assert item is not None
        assert item.status == BacklogStatus.published
        assert item.microprd is not None
        assert item.dataset_path is not None

    def test_publish_generates_starter_scaffold(self):
        _publish_demo_item("demo-001")
        item = backlog_store.get_item("demo-001")
        assert item is not None
        assert item.starter_files is not None
        assert set(item.starter_files.keys()) == set(STARTER_PATHS)

    def test_publish_generates_dataset_with_anomalies(self):
        _publish_demo_item("demo-001")
        item = backlog_store.get_item("demo-001")
        assert item is not None
        assert len(item.dataset_anomalies) >= 3
        checks = verify_anomalies(Path(item.dataset_path))
        assert checks["has_null_query_hash"]
        assert checks["missing_execution_time_index"]
        assert checks["missing_session_event_id_index"]


class TestSynthesizer:
    def test_generate_dataset_directly(self):
        item = backlog_store.get_item("demo-003")
        assert item is not None
        preview = item.relaxed_preview or __import__(
            "backend.ai_pm.relaxation", fromlist=["apply_relaxation"]
        ).apply_relaxation(item.metadata, RelaxationConfig(), "demo-003")

        path, anomalies = generate_dataset("test-gen", preview, item.metadata)
        assert path.exists()
        assert len(anomalies) == 3
        assert verify_anomalies(path)["has_null_query_hash"]


class TestSandboxAPI:
    def test_list_challenges_empty_before_publish(self):
        # demo items start pending — may have leftovers from other tests
        res = client.get("/api/v1/sandbox/challenges")
        assert res.status_code == 200

    def test_get_starter_after_publish(self):
        _publish_demo_item("demo-003")
        res = client.get("/api/v1/sandbox/challenges/demo-003/starter")
        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is True
        assert "src/queries.py" in body["files"]
        assert "tests/test_public.py" in body["files"]

    def test_sandbox_instructions_match_platform(self):
        _publish_demo_item("demo-003")
        detail = client.get("/api/v1/sandbox/challenges/demo-003").json()
        steps = detail["microprd"]["sandbox_instructions"]
        joined = " ".join(steps)
        assert "Submit Project" in joined
        assert "src/queries.py" in joined
        assert "solution.py" not in joined
        assert "benchmark.py" not in joined

    def test_download_starter_zip(self):
        _publish_demo_item("demo-003")
        res = client.get("/api/v1/sandbox/challenges/demo-003/starter/download")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/zip"
        assert len(res.content) > 100

    def test_validate_syntax_error(self):
        res = client.post(
            "/api/v1/sandbox/validate",
            json={"path": "bad.py", "content": "def oops(\n"},
        )
        assert res.status_code == 200
        diagnostics = res.json()["diagnostics"]
        assert len(diagnostics) >= 1

    def test_workspace_bootstrap_sets_cookie(self):
        _publish_demo_item("demo-003")
        res = client.get("/api/v1/sandbox/challenges/demo-003/workspace")
        assert res.status_code == 200
        assert res.json()["workspace_id"]
        assert "sandbox_workspace_id" in res.cookies

    def test_save_and_restore_draft(self):
        _publish_demo_item("demo-003")
        boot = client.get("/api/v1/sandbox/challenges/demo-003/workspace")
        cookies = boot.cookies
        files = {"src/queries.py": "updated = True\n"}
        save = client.put(
            "/api/v1/sandbox/challenges/demo-003/draft",
            json={"files": files, "client_revision": 1},
            cookies=cookies,
        )
        assert save.status_code == 200

        boot2 = client.get("/api/v1/sandbox/challenges/demo-003/workspace", cookies=cookies)
        draft = boot2.json()["draft"]
        assert draft is not None
        assert draft["files"]["src/queries.py"] == "updated = True\n"

    def test_submit_multifile_inline(self):
        _publish_demo_item("demo-003")
        files = {"src/queries.py": "def solve():\n    return 1\n"}
        res = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={"mode": "inline", "files": files, "language": "python"},
        )
        assert res.status_code == 200
        record = submission_store.get_submission(res.json()["submission_id"])
        assert record is not None
        assert record.files["src/queries.py"].startswith("def solve")

    def test_submit_zip_rejects_path_traversal(self):
        _publish_demo_item("demo-003")
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.py", "bad")
        buf.seek(0)

        res = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit/zip",
            content=buf.read(),
            headers={"Content-Type": "application/zip"},
        )
        assert res.status_code == 400

    def test_list_and_get_published_challenge(self):
        _publish_demo_item("demo-003")
        listed = client.get("/api/v1/sandbox/challenges").json()
        ids = [c["id"] for c in listed]
        assert "demo-003" in ids

        detail = client.get("/api/v1/sandbox/challenges/demo-003").json()
        assert detail["microprd"]["title"]
        assert detail["microprd"]["context"]
        assert detail["microprd"]["definition_of_success"]
        assert detail["microprd"]["structural_constraints"]
        assert detail["microprd"]["sandbox_instructions"]
        assert detail["dataset_ready"] is True
        assert len(detail["dataset_anomalies"]) >= 3

    def test_download_dataset(self):
        _publish_demo_item("demo-003")
        res = client.get("/api/v1/sandbox/challenges/demo-003/dataset")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/x-sqlite3"
        assert len(res.content) > 1000

        # Verify it's valid SQLite with expected tables
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tmp:
            tmp.write(res.content)
            tmp.flush()
            conn = sqlite3.connect(tmp.name)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        assert "events" in tables
        assert "sessions" in tables
        conn.close()

    def test_submit_solution(self):
        _publish_demo_item("demo-003")
        res = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={"code": "print('hello sandbox')", "language": "python"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is True
        assert body["status"] == "assessed"
        assert body["submission_id"]
        assert body["scorecard"] is not None

        record = submission_store.get_submission(body["submission_id"])
        assert record is not None
        assert record.code == "print('hello sandbox')"

        count = client.get("/api/v1/sandbox/challenges/demo-003/submissions/count").json()
        assert count["count"] == 1

    def test_submit_unknown_challenge_404(self):
        res = client.post(
            "/api/v1/sandbox/challenges/nonexistent/submit",
            json={"code": "x = 1"},
        )
        assert res.status_code == 404
