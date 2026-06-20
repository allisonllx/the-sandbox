"""Tests for dual-layer assessor: platform signal vs sponsor fit."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.ai_pm.models import RelaxationConfig
from backend.assessor.models import platform_execution_points
from backend.assessor.registry import assess_submission
from backend.main import app
from backend.sandbox.models import SubmissionRecord, SubmissionStatus
from backend.ai_pm.models import ChallengeTrack

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


class TestDualLayerScorecard:
    def test_platform_and_sponsor_layers_present(self):
        _publish("demo-003")
        res = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={
                "mode": "inline",
                "files": {
                    "solution.py": "def fix():\n    try:\n        pass\n    except Exception:\n        pass\n",
                    "README.md": "# Trade-offs\n\nIndex vs full scan.",
                },
                "language": "python",
            },
        )
        assert res.status_code == 200, res.text
        sc = res.json()["scorecard"]
        assert "platform" in sc
        assert "sponsor" in sc
        assert sc["execution_points"] == platform_execution_points(sc["platform"]["score"])
        assert sc["sponsor_fit_score"] == sc["sponsor"]["score"]
        assert sc["platform_score"] == sc["platform"]["score"]

    def test_execution_points_from_platform_only(self):
        record = SubmissionRecord(
            id="test",
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            files={"solution.py": "x = 1\n" * 50, "README.md": "# notes"},
            language="python",
            status=SubmissionStatus.received,
        )
        sc = assess_submission(record, ChallengeTrack.technical)
        assert sc["execution_points"] == platform_execution_points(sc["platform"]["score"])
        assert sc["sponsor_fit_score"] != sc["execution_points"] or sc["platform"]["score"] == sc["sponsor"]["score"]

    def test_product_platform_vs_sponsor_dimensions_differ(self):
        _publish("demo-004")
        files = {
            "DESIGN.md": "# Design\n\nTarget persona: mobile user.\n\nTrade-off: list vs map view.",
            "index.html": "<html><body>Merchants</body></html>",
            "src/app.js": "const cart = []; const merchants = [];",
            "src/styles.css": "@media (max-width: 768px) { .list { display: block; } }",
        }
        res = client.post(
            "/api/v1/sandbox/challenges/demo-004/submit",
            json={"mode": "inline", "files": files, "language": "html"},
        )
        assert res.status_code == 200, res.text
        sc = res.json()["scorecard"]
        assert "deliverable_completeness" in sc["platform"]["dimensions"]
        assert "persona_fit" in sc["sponsor"]["dimensions"]
        assert "Product Thinking" not in sc["dimensions"]

    def test_sponsor_matches_sort_by_sponsor_fit(self):
        _publish("demo-003")
        # Two submissions — stronger sponsor fit via README + try/except
        client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={"mode": "inline", "files": {"solution.py": "x=1"}, "language": "python"},
        )
        client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={
                "mode": "inline",
                "files": {
                    "solution.py": "try:\n    optimize()\nexcept:\n    pass\n" * 5,
                    "README.md": "# Trade-offs and edge cases",
                },
                "language": "python",
            },
        )
        matches = client.get("/api/v1/triage/backlog/demo-003/matches").json()
        assert matches["source"] == "live"
        assert len(matches["entries"]) >= 2
        fits = [e["sponsor_fit_score"] for e in matches["entries"]]
        assert fits == sorted(fits, reverse=True)
        assert "sponsor_fit_score" in matches["entries"][0]

    def test_scorecard_api_returns_layers(self):
        _publish("demo-004")
        sub = client.post(
            "/api/v1/sandbox/challenges/demo-004/submit",
            json={
                "mode": "inline",
                "files": {"DESIGN.md": "# Persona\n\nTrade-off.", "index.html": "<html/>"},
                "language": "html",
            },
        ).json()
        sc = client.get(
            f"/api/v1/sandbox/submissions/{sub['submission_id']}/scorecard"
        ).json()
        assert sc["platform"] is not None
        assert sc["sponsor"] is not None
        assert sc["execution_points"] is not None
        assert sc["sponsor_fit_score"] is not None
