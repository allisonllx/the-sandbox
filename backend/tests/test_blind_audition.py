"""Tests for blind-002: Company Tech Profile blind audition."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm import company_profile as company_profile_module
from backend.ai_pm import domain_obfuscator
from backend.ai_pm import store as backlog_store
from backend.ai_pm.models import RelaxationConfig
from backend.ai_pm.public_sanitize import assert_public_challenge_safe
from backend.main import app

client = TestClient(app)


def _locked_reward(**kwargs) -> dict:
    return {
        "reward_type": "cash_bounty",
        "amount_usd": 500,
        "interview_benchmark": 75,
        "locked": True,
        **kwargs,
    }


def _publish(
    item_id: str,
    *,
    obfuscate_domain: bool = False,
    track: str | None = None,
) -> dict:
    config = RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=True,
        noise_level=0.2,
        abstract_brand=True,
        obfuscate_domain=obfuscate_domain,
    )
    body: dict = {"config": config.model_dump(), "reward": _locked_reward()}
    if track:
        body["track"] = track
    res = client.post(f"/api/v1/triage/publish/{item_id}", json=body)
    assert res.status_code == 200, res.text
    return res.json()


def _all_strings(obj) -> str:
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return " ".join(_all_strings(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(_all_strings(v) for v in obj)
    return ""


class TestCompanyProfileGenerator:
    def test_demo_005_omits_industry(self):
        item = backlog_store.get_item("demo-005")
        assert item is not None
        profile = company_profile_module.generate_profile(item, reward=_locked_reward())
        assert profile.industry_broad is None
        assert profile.stage == "Series A"
        assert profile.team_size_range == "11-50"

    def test_demo_003_includes_industry_when_locked(self):
        item = backlog_store.get_item("demo-003")
        assert item is not None
        profile = company_profile_module.generate_profile(item, reward=_locked_reward())
        assert profile.industry_broad == "Fintech Infrastructure"
        assert profile.verification_status == "verified"


class TestBlindAuditionPublicAPI:
    def test_demo_005_no_brand_or_domain_leaks(self):
        _publish("demo-005", obfuscate_domain=True, track="product_feature")
        detail = client.get("/api/v1/sandbox/challenges/demo-005").json()

        assert "brand_proxy" not in detail
        assert detail.get("company_profile") is not None
        assert detail["company_profile"]["industry_broad"] is None

        blob = _all_strings(detail).lower()
        assert "lockershare" not in blob
        assert "stealthco" not in blob
        assert "restaurant" not in blob
        assert "voucher" not in blob
        assert domain_obfuscator.public_text_is_safe(blob)

        assert detail["microprd"].get("brand_proxy") is None
        assert "Voucher redemption" not in blob

    def test_demo_003_verified_sponsor_and_escrow(self):
        _publish("demo-003")
        detail = client.get("/api/v1/sandbox/challenges/demo-003").json()

        assert detail["company_profile"]["verification_status"] == "verified"
        assert detail["reward_escrow_label"] is not None
        assert "brand_proxy" not in detail

    def test_relax_returns_company_profile_preview(self):
        config = RelaxationConfig(obfuscate_domain=True).model_dump()
        res = client.post(
            "/api/v1/triage/relax/demo-005",
            json={"config": config, "reward": _locked_reward()},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["company_profile"] is not None
        assert body["company_profile"]["industry_broad"] is None

    def test_public_challenge_passes_safety_assertion(self):
        _publish("demo-005", obfuscate_domain=True, track="product_feature")
        detail = client.get("/api/v1/sandbox/challenges/demo-005").json()
        from backend.sandbox.models import PublishedChallenge

        challenge = PublishedChallenge.model_validate(detail)
        assert_public_challenge_safe(challenge)

    def test_list_challenges_all_have_company_profile(self):
        _publish("demo-003")
        _publish("demo-004", track="product_feature")
        listed = client.get("/api/v1/sandbox/challenges").json()
        for ch in listed:
            assert "company_profile" in ch
            assert "brand_proxy" not in ch
