"""Tests for founder-editable publish draft."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.ai_pm.models import CompanyTechProfile, PublishDraft, RelaxationConfig
from backend.main import app

client = TestClient(app)


def _locked_reward() -> dict:
    return {
        "reward_type": "cash_bounty",
        "amount_usd": 500,
        "interview_benchmark": 75,
        "locked": True,
    }


def _custom_draft(title: str = "Custom Equipment Discovery Sprint") -> dict:
    return PublishDraft(
        title=title,
        context="Founder-edited context for blind audition release.",
        definition_of_success=[
            "Ship responsive discovery UI",
            "Document IA trade-offs in DESIGN.md",
            "Founder-added criterion: include empty-state handling",
        ],
        structural_constraints=["HTML/CSS/JS starter only"],
        evaluation_focus=["Discovery IA", "Founder-added focus: accessibility"],
        company_profile=CompanyTechProfile(
            stage="Series A",
            team_size_range="11-50",
            tech_stack=["Go", "React", "AWS"],
            industry_broad=None,
            verification_status="verified",
            verification_label="Platform-verified sponsor",
        ),
        user_persona="Urban renter, mobile-first",
        problem_framing="How would you structure locker discovery?",
        design_considerations=["Touch targets"],
        deliverable_requirements=["DESIGN.md required"],
    ).model_dump()


class TestPublishDraft:
    def test_relax_returns_challenge_draft(self):
        config = RelaxationConfig(obfuscate_domain=True).model_dump()
        res = client.post(
            "/api/v1/triage/relax/demo-005",
            json={"config": config, "reward": _locked_reward()},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body.get("challenge_draft") is not None
        assert body["challenge_draft"]["title"]
        assert len(body["challenge_draft"]["definition_of_success"]) >= 1

    def test_publish_applies_founder_draft(self):
        config = RelaxationConfig(
            abstract_logic=True,
            synthesize_variables=True,
            abstract_brand=True,
        ).model_dump()
        custom_title = "Founder Custom Inventory Discovery Challenge"
        draft = _custom_draft(custom_title)
        draft["evaluation_focus"] = ["Discovery IA", "Founder-added focus: accessibility"]
        res = client.post(
            "/api/v1/triage/publish/demo-004",
            json={
                "config": config,
                "reward": _locked_reward(),
                "track": "product_feature",
                "draft": draft,
            },
        )
        assert res.status_code == 200, res.text

        public = client.get("/api/v1/sandbox/challenges/demo-004").json()
        assert public["title"] == custom_title
        assert "Founder-edited context" in public["microprd"]["context"]
        assert any("Founder-added" in s for s in public["evaluation_focus"])
        assert any("Founder-added" in s for s in public["microprd"]["definition_of_success"])
