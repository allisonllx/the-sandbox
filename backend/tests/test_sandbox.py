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

client = TestClient(app)


def _publish_demo_item(item_id: str = "demo-003") -> None:
    """Publish a backlog item via the triage API."""
    config = RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=True,
        noise_level=0.3,
    )
    res = client.post(f"/api/v1/triage/publish/{item_id}", json={"config": config.model_dump()})
    assert res.status_code == 200, res.text


@pytest.fixture(autouse=True)
def _reset_submissions():
    submission_store.clear()
    yield
    submission_store.clear()


class TestPublishFlow:
    def test_publish_sets_status_published(self):
        _publish_demo_item("demo-002")
        item = backlog_store.get_item("demo-002")
        assert item is not None
        assert item.status == BacklogStatus.published
        assert item.microprd is not None
        assert item.dataset_path is not None

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
        assert body["status"] == "received"
        assert body["submission_id"]

        count = client.get("/api/v1/sandbox/challenges/demo-003/submissions/count").json()
        assert count["count"] == 1

    def test_submit_unknown_challenge_404(self):
        res = client.post(
            "/api/v1/sandbox/challenges/nonexistent/submit",
            json={"code": "x = 1"},
        )
        assert res.status_code == 404
