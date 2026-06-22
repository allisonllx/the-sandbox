"""Tests for legacy demo-* spec adapter."""

from __future__ import annotations

from backend.ai_pm import store
from backend.challenge_factory.legacy_spec_adapter import resolve_challenge_spec
from backend.challenge_factory.models import TechnicalArchetype


class TestLegacySpecAdapter:
    def test_demo_003_resolves_data_core_spec(self):
        item = store.get_item("demo-003")
        assert item is not None
        spec = resolve_challenge_spec(item)
        assert spec is not None
        assert spec.classification.archetype == TechnicalArchetype.data_core

    def test_demo_006_resolves_idempotency_spec(self):
        item = store.get_item("demo-006")
        assert item is not None
        spec = resolve_challenge_spec(item)
        assert spec is not None
        assert spec.classification.archetype == TechnicalArchetype.idempotency_engine

    def test_demo_seeds_have_no_persisted_spec(self):
        item = store.get_item("demo-003")
        assert item is not None
        assert item.challenge_spec is None
