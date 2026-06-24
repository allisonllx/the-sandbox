"""Tests for CTO submission review via Match Radar."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm.models import RelaxationConfig
from backend.main import app
from backend.sandbox import submission_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_submissions():
    submission_store.clear()
    yield
    submission_store.clear()


def _publish(item_id: str = "demo-003") -> None:
    config = RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=True,
        noise_level=0.3,
    )
    reward = {
        "reward_type": "cash_bounty",
        "amount_usd": 500,
        "interview_benchmark": 75,
        "locked": True,
    }
    res = client.post(
        f"/api/v1/triage/publish/{item_id}",
        json={"config": config.model_dump(), "reward": reward},
    )
    assert res.status_code == 200, res.text


class TestSponsorSubmissionReview:
    def test_matches_include_submission_id_after_live_submit(self):
        _publish("demo-003")
        submit = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={"code": "print('hello review')", "language": "python"},
        )
        assert submit.status_code == 200, submit.text
        submission_id = submit.json()["submission_id"]

        matches = client.get("/api/v1/triage/backlog/demo-003/matches")
        assert matches.status_code == 200
        body = matches.json()
        assert body["source"] == "live"
        assert len(body["entries"]) >= 1
        submission_ids = [e["submission_id"] for e in body["entries"]]
        assert submission_id in submission_ids

    def test_get_submission_detail_returns_files_and_scorecard(self):
        _publish("demo-003")
        submit = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={"code": "print('review me')", "language": "python"},
        )
        submission_id = submit.json()["submission_id"]

        res = client.get(f"/api/v1/triage/backlog/demo-003/submissions/{submission_id}")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["submission_id"] == submission_id
        assert body["challenge_id"] == "demo-003"
        assert body["candidate_id"].startswith("CAND-")
        assert "solution.py" in body["files"] or body["files"]
        assert body["scorecard"] is not None

    def test_wrong_challenge_id_returns_404(self):
        _publish("demo-003")
        _publish("demo-005")
        submit = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={"code": "x = 1", "language": "python"},
        )
        submission_id = submit.json()["submission_id"]

        res = client.get(f"/api/v1/triage/backlog/demo-005/submissions/{submission_id}")
        assert res.status_code == 404

    def test_submission_not_found_404(self):
        _publish("demo-003")
        res = client.get("/api/v1/triage/backlog/demo-003/submissions/nonexistent-id")
        assert res.status_code == 404

    def test_demo_matches_have_no_submission_id(self):
        _publish("demo-003")
        matches = client.get("/api/v1/triage/backlog/demo-003/matches").json()
        if matches["source"] == "demo":
            for entry in matches["entries"]:
                assert entry.get("submission_id") is None
