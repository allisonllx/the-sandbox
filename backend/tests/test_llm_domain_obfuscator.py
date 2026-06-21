"""Tests for LLM domain obfuscation fallback."""

from __future__ import annotations

from typing import Any

import pytest

from backend.ai_pm import llm_domain_obfuscator
from backend.ai_pm.domain_obfuscator import obfuscate_domain
from backend.ai_pm.models import SensitivityTag
from backend.privacy_proxy.models import FieldMetadata, SanitizedMetadata


def _generic_metadata() -> SanitizedMetadata:
    return SanitizedMetadata(
        fields=[
            FieldMetadata(name="widget_id", inferred_type="integer", nullable=False),
            FieldMetadata(name="widget_status", inferred_type="string", nullable=True),
        ],
        format_detected="json",
        approximate_row_scale=5000,
    )


class _SafeDomainStub:
    def chat(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "domain_proxy": "inventory_hub",
            "public_title": "Community Inventory Hub",
            "public_narrative": "Students build a locker inventory console for shared equipment.",
            "transform_rationale": "Generic widget fields mapped to equipment inventory.",
            "brand_proxy": "GearShare",
            "field_map": {
                "widget_id": "locker_id",
                "widget_status": "locker_status",
            },
        }


class _LeakyDomainStub:
    def chat(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "domain_proxy": "bad",
            "public_title": "Grab Food Merchant Portal",
            "public_narrative": "Delivery dashboard.",
            "transform_rationale": "leak",
            "brand_proxy": "BadCo",
            "field_map": {"widget_id": "restaurant_id", "widget_status": "status"},
        }


def test_llm_suggest_returns_valid_transform():
    transform = llm_domain_obfuscator.suggest_domain_transform(
        _generic_metadata(),
        "internal-jira",
        "Widget sync bug",
        client=_SafeDomainStub(),  # type: ignore[arg-type]
    )
    assert transform is not None
    assert transform.field_map["widget_id"] == "locker_id"
    assert "[LLM domain obfuscation]" in transform.transform_rationale


def test_llm_suggest_rejects_leaky_output():
    transform = llm_domain_obfuscator.suggest_domain_transform(
        _generic_metadata(),
        "internal-jira",
        "Widget sync bug",
        client=_LeakyDomainStub(),  # type: ignore[arg-type]
    )
    assert transform is None


def test_obfuscate_domain_uses_llm_for_generic_yellow(monkeypatch: pytest.MonkeyPatch):
    from backend.ai_pm.domain_obfuscator import DomainTransform

    def _fake_suggest(*_args, **_kwargs):
        return DomainTransform(
            domain_proxy="inventory_hub",
            public_title="Community Inventory Hub",
            public_narrative="Students build a locker inventory console.",
            internal_intent="Internal (CTO only): Widget sync bug — internal-jira",
            transform_rationale="LLM mask [LLM domain obfuscation]",
            brand_proxy="GearShare",
            field_map={"widget_id": "locker_id", "widget_status": "locker_status"},
        )

    monkeypatch.setattr(
        llm_domain_obfuscator,
        "suggest_domain_transform",
        _fake_suggest,
    )
    transform = obfuscate_domain(
        _generic_metadata(),
        "internal-jira",
        "Widget sync bug",
        sensitivity_tag=SensitivityTag.yellow,
    )
    assert transform is not None
    assert transform.domain_proxy == "inventory_hub"
