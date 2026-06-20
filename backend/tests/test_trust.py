"""Tests for trust-001: scope guard + domain obfuscation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm import domain_obfuscator
from backend.ai_pm import store as backlog_store
from backend.ai_pm.models import ChallengeReward, RelaxationConfig, RewardType
from backend.main import app

client = TestClient(app)


def _locked_reward(**kwargs) -> dict:
    reward = ChallengeReward(reward_type=RewardType.cash_bounty, amount_usd=500, locked=True, **kwargs)
    return reward.model_dump()


def _publish(item_id: str, *, obfuscate_domain: bool = False, track: str | None = None) -> dict:
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
    return res


class TestScopeGuard:
    def test_demo_007_publish_blocked(self):
        res = _publish("demo-007")
        assert res.status_code == 422, res.text
        detail = res.json()["detail"]
        assert detail["code"] == "SCOPE_EXCEEDED"
        assert detail["suggested_breakdown"]

    def test_publish_without_locked_reward_blocked(self):
        config = RelaxationConfig().model_dump()
        res = client.post(
            "/api/v1/triage/publish/demo-003",
            json={"config": config, "reward": {"reward_type": "cash_bounty", "amount_usd": 500, "locked": False}},
        )
        assert res.status_code == 422
        assert res.json()["detail"]["code"] == "REWARD_NOT_LOCKED"


class TestDomainObfuscation:
    def test_demo_005_publish_obfuscated(self):
        res = _publish("demo-005", obfuscate_domain=True, track="product_feature")
        assert res.status_code == 200, res.text

        detail = client.get("/api/v1/sandbox/challenges/demo-005").json()
        prd = detail["microprd"]
        blob = f"{prd['title']} {prd['context']}".lower()
        assert domain_obfuscator.public_text_is_safe(blob)
        assert "equipment" in blob or "locker" in blob
        assert "restaurant" not in blob
        assert "dine" not in blob

    def test_demo_005_field_names_obfuscated_on_relax(self):
        config = RelaxationConfig(
            abstract_logic=False,
            synthesize_variables=False,
            obfuscate_domain=True,
        )
        res = client.post(
            "/api/v1/triage/relax/demo-005",
            json={"config": config.model_dump()},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        relaxed = body["preview"]["relaxed_fields"]
        assert "restaurant_id" not in relaxed
        assert "voucher_code" not in relaxed
        assert "dine_in_session" not in relaxed
        assert "locker_id" in relaxed
        assert "rental_credit_code" in relaxed
        assert "reservation_session" in relaxed

        domain_preview = body["domain_preview"]
        assert domain_preview["field_map"]["restaurant_id"] == "locker_id"
        assert domain_preview["public_fields"] == relaxed

    def test_field_map_unit(self):
        names = ["voucher_code", "restaurant_id", "checkout_step"]
        field_map = domain_obfuscator.build_field_map(names, "food_merchant")
        assert field_map["restaurant_id"] == "locker_id"
        assert field_map["voucher_code"] == "rental_credit_code"
        assert field_map["checkout_step"] == "redeem_step"

    def test_forbidden_tokens_detected(self):
        assert not domain_obfuscator.public_text_is_safe("Grab merchant checkout")
        assert domain_obfuscator.public_text_is_safe("Locker equipment rental hub")
