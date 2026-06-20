"""Tests for sponsor-scoped vs enterprise-global rank views."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.ai_pm.models import RelaxationConfig
from backend.main import app
from backend.sandbox import sponsor_matches as sponsor_matches_module

client = TestClient(app)


def _publish(item_id: str, **kwargs) -> None:
    config = RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=True,
        abstract_brand=True,
        **kwargs,
    ).model_dump()
    res = client.post(
        f"/api/v1/triage/publish/{item_id}",
        json={
            "config": config,
            "reward": {
                "reward_type": "cash_bounty",
                "amount_usd": 500,
                "locked": True,
            },
        },
    )
    assert res.status_code == 200, res.text


class TestRankViews:
    def test_sponsor_matches_scoped_to_challenge(self):
        _publish("demo-003")
        res = client.get("/api/v1/triage/backlog/demo-003/matches")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["challenge_id"] == "demo-003"
        assert len(body["entries"]) >= 1
        for entry in body["entries"]:
            assert "demo-005" not in entry["summary"].lower()

    def test_sponsor_matches_not_published_422(self):
        res = client.get("/api/v1/triage/backlog/demo-001/matches")
        assert res.status_code == 422
        assert res.json()["detail"]["code"] == "CHALLENGE_NOT_PUBLISHED"

    def test_enterprise_radar_distinct_from_leaderboard(self):
        lb = client.get("/api/v1/sandbox/leaderboard").json()
        ent = client.get("/api/v1/sandbox/enterprise/radar").json()
        assert lb["entries"]
        assert ent["entries"]
        assert ent["tier"]
        lb_highlights = {e["highlight"] for e in lb["entries"]}
        assert not any("demo-003" in h for h in lb_highlights)

    def test_demo_matches_never_cross_challenges(self):
        m3 = sponsor_matches_module.get_sponsor_matches("demo-003")
        m5 = sponsor_matches_module.get_sponsor_matches("demo-005")
        assert m3.entries
        assert m5.entries
        assert m3.entries[0].candidate_id != m5.entries[0].candidate_id
