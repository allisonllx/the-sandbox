"""Tests for LLM sponsor fit layer (assessor-001 Phase B)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm.llm_client import LLMClient, reset_default_client, set_default_client
from backend.ai_pm.models import ChallengeTrack, RelaxationConfig
from backend.assessor.models import ChallengeContext
from backend.assessor.sponsor_fit import assess_sponsor_fit
from backend.main import app
from backend.sandbox.models import SubmissionRecord, SubmissionStatus
from backend.sandbox.starter_scaffold import generate_starter_files

client = TestClient(app)


class SponsorFitStub:
    """Mock LLM returning fixed sponsor-fit dimensions."""

    def __init__(
        self,
        dimensions: dict[str, int] | None = None,
        *,
        track: str = "technical",
    ) -> None:
        if dimensions is None:
            dimensions = (
                {
                    "criteria_alignment": 88,
                    "architectural_taste": 92,
                    "edge_case_handling": 85,
                    "tradeoff_reasoning": 90,
                }
                if track == "technical"
                else {
                    "persona_fit": 86,
                    "problem_framing": 90,
                    "ux_judgment": 84,
                    "communication": 88,
                }
            )
        self.dimensions = dimensions
        self.calls: list[dict[str, str]] = []

    def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> dict[str, Any]:
        self.calls.append({"system": system, "user": user})
        return {
            "dimensions": self.dimensions,
            "summary": "LLM sponsor fit: strong alignment with success criteria.",
            "notes": ["Mock LLM assessor"],
        }


@pytest.fixture(autouse=True)
def _restore_llm_client():
    yield
    reset_default_client()


def _publish(item_id: str) -> None:
    config = RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=True,
        abstract_brand=True,
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


class TestSponsorFitLLM:
    def test_llm_path_returns_stub_dimensions(self):
        stub = SponsorFitStub()
        set_default_client(stub)  # type: ignore[arg-type]

        record = SubmissionRecord(
            id="t1",
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            files=generate_starter_files("demo-003", "Test"),
            language="python",
            status=SubmissionStatus.received,
        )
        context = ChallengeContext(
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            definition_of_success=["Reduce query latency", "Document index trade-offs"],
            evaluation_focus=["Performance", "Readability"],
            microprd_title="Optimize session lookup",
        )
        layer = assess_sponsor_fit(record, context)
        assert layer.dimensions["architectural_taste"] == 92
        assert layer.score >= 85
        assert any("LLM" in n for n in layer.notes)
        assert len(stub.calls) == 1

    def test_llm_payload_excludes_brand_proxy(self):
        stub = SponsorFitStub()
        set_default_client(stub)  # type: ignore[arg-type]
        _publish("demo-003")

        from backend.ai_pm import store as backlog_store

        item = backlog_store.get_item("demo-003")
        assert item and item.brand_proxy

        res = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={
                "mode": "inline",
                "files": generate_starter_files("demo-003", "Test"),
                "language": "python",
            },
        )
        assert res.status_code == 200, res.text
        assert stub.calls
        user_payload = stub.calls[-1]["user"]
        assert item.brand_proxy not in user_payload

    def test_well_structured_scores_higher_than_naive_via_llm(self):
        class ComparativeStub:
            def chat(
                self,
                *,
                system: str,
                user: str,
                temperature: float = 0.2,
                **kwargs: Any,
            ) -> dict[str, Any]:
                is_strong = "README" in user or "trade" in user.lower()
                base = 85 if is_strong else 45
                return {
                    "dimensions": {
                        "criteria_alignment": base,
                        "architectural_taste": base + 5,
                        "edge_case_handling": base - 5,
                        "tradeoff_reasoning": base,
                    },
                    "summary": "Comparative LLM fit",
                    "notes": [],
                }

        set_default_client(ComparativeStub())  # type: ignore[arg-type]

        context = ChallengeContext(
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            definition_of_success=["Fix slow queries"],
        )
        naive = SubmissionRecord(
            id="n",
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            files={"solution.py": "x=1"},
            language="python",
            status=SubmissionStatus.received,
        )
        strong = SubmissionRecord(
            id="s",
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            files={
                "src/queries.py": "def batch_session_lookup(conn, ids):\n    return []",
                "README.md": "# Trade-offs\n\nIndex vs scan.",
            },
            language="python",
            status=SubmissionStatus.received,
        )
        naive_score = assess_sponsor_fit(naive, context).score
        strong_score = assess_sponsor_fit(strong, context).score
        assert strong_score > naive_score

    def test_product_track_llm_dimensions(self):
        stub = SponsorFitStub(track="product")
        set_default_client(stub)  # type: ignore[arg-type]

        record = SubmissionRecord(
            id="p1",
            challenge_id="demo-004",
            track=ChallengeTrack.product_feature,
            files={"DESIGN.md": "# Persona\n\nTrade-off.", "index.html": "<html/>"},
            language="html",
            status=SubmissionStatus.received,
        )
        context = ChallengeContext(
            challenge_id="demo-004",
            track=ChallengeTrack.product_feature,
            definition_of_success=["Ship responsive prototype"],
        )
        layer = assess_sponsor_fit(record, context)
        assert "persona_fit" in layer.dimensions
        assert layer.dimensions["persona_fit"] == 86

    def test_heuristic_fallback_without_api_key(self):
        set_default_client(LLMClient(api_key=None))

        record = SubmissionRecord(
            id="h1",
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            files={"README.md": "# Trade-offs", "solution.py": "try:\n pass\nexcept: pass"},
            language="python",
            status=SubmissionStatus.received,
        )
        context = ChallengeContext(
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            definition_of_success=["Handle edge cases"],
        )
        layer = assess_sponsor_fit(record, context)
        assert any("heuristic" in n.lower() for n in layer.notes)
        assert layer.score > 0

    def test_match_radar_uses_llm_summary(self):
        stub = SponsorFitStub()
        set_default_client(stub)  # type: ignore[arg-type]
        _publish("demo-003")

        client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={
                "mode": "inline",
                "files": generate_starter_files("demo-003", "Test"),
                "language": "python",
            },
        )
        matches = client.get("/api/v1/triage/backlog/demo-003/matches").json()
        assert matches["source"] == "live"
        assert "LLM sponsor fit" in matches["entries"][0]["summary"]
