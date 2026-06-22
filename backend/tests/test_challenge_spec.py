"""Tests for single-pass challenge spec generation."""

from __future__ import annotations

from backend.challenge_factory.archetype_catalog import infer_archetype_from_metadata
from backend.challenge_factory.challenge_spec import infer_spec_heuristic
from backend.challenge_factory.models import TechnicalArchetype
from backend.tests.test_triage import _make_metadata


class TestChallengeSpecHeuristic:
    def test_payment_retry_log_maps_to_idempotency_engine(self):
        metadata = _make_metadata(
            ["retry_count", "idempotency_key", "gateway_response_code"],
            row_scale=900,
        )
        archetype = infer_archetype_from_metadata(metadata)
        assert archetype == TechnicalArchetype.idempotency_engine

        spec = infer_spec_heuristic(metadata, suggested_title="Payment retries")
        assert spec.classification.archetype == TechnicalArchetype.idempotency_engine
        assert spec.interface_contract.primary_module == "src/idempotency_store.py"
        assert "process_once" in spec.interface_contract.public_api[0].name

    def test_db_fields_map_to_data_core(self):
        metadata = _make_metadata(
            ["query_hash", "execution_time_ms", "table_name"],
            row_scale=5000,
        )
        spec = infer_spec_heuristic(metadata)
        assert spec.classification.archetype == TechnicalArchetype.data_core
        assert spec.data_plane.value == "sqlite"

    def test_founder_algorithm_override(self):
        metadata = _make_metadata(
            ["retry_count", "idempotency_key"],
            row_scale=100,
        )
        spec = infer_spec_heuristic(
            metadata,
            founder_archetype_override=TechnicalArchetype.algorithm,
        )
        assert spec.classification.archetype == TechnicalArchetype.algorithm
        assert spec.interface_contract.primary_module == "src/solution.py"
