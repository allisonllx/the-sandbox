"""Tests for dynamic scaffold interpolation from spec."""

from __future__ import annotations

import pytest

from backend.challenge_factory.archetype_catalog import build_heuristic_spec
from backend.challenge_factory.models import TechnicalArchetype
from backend.challenge_factory.scaffold_interpolate import (
    generate_scaffold_from_spec,
    validate_contract_alignment,
)
from backend.challenge_factory.spec_models import InterfaceContract, PublicAPIEntry
from backend.challenge_factory.validator import validate_package
from backend.challenge_factory.spec_projection import spec_to_blueprint
from backend.tests.test_triage import _make_metadata


class TestScaffoldInterpolate:
    def test_idempotency_scaffold_passes_validation(self):
        metadata = _make_metadata(["idempotency_key", "retry_count"], row_scale=100)
        spec = build_heuristic_spec(metadata, suggested_title="Dedup payments")
        starter, reference = generate_scaffold_from_spec("spec-1", spec)
        assert "docs/SPEC.md" in starter
        assert "src/idempotency_store.py" in starter
        assert validate_contract_alignment(spec, starter) == []
        report = validate_package(starter, reference, spec_to_blueprint(spec))
        assert report.passed, report.errors

    def test_signature_drift_regenerates_tests(self):
        metadata = _make_metadata(["tenant_id"], row_scale=50)
        spec = build_heuristic_spec(metadata)
        spec = spec.model_copy(
            update={
                "interface_contract": InterfaceContract(
                    primary_module="src/tenant_proxy.py",
                    public_api=[
                        PublicAPIEntry(
                            name="filter_tenant_rows",
                            signature="def filter_tenant_rows(rows: list[dict], tenant_id: str) -> list[dict]",
                        ),
                    ],
                    invariants=["Tenant isolation"],
                ),
            }
        )
        starter, _ = generate_scaffold_from_spec("spec-2", spec)
        assert "filter_tenant_rows" in starter["tests/test_public.py"]
        assert "filter_tenant_rows" in starter["src/tenant_proxy.py"]
        errors = validate_contract_alignment(spec, starter)
        assert errors == []


@pytest.mark.parametrize(
    "field_names,expected_archetype",
    [
        (["latency_ms", "command"], TechnicalArchetype.cli_instrumentation),
        (["source_system", "target_schema"], TechnicalArchetype.data_adapter),
        (["timeout_ms", "failure_rate"], TechnicalArchetype.circuit_breaker),
        (["file_size_bytes", "chunk_count"], TechnicalArchetype.stream_parser),
        (["email", "user_id"], TechnicalArchetype.data_masking),
        (["tenant_id"], TechnicalArchetype.rls_proxy),
    ],
)
class TestArchetypeSmokes:
    def test_archetype_generates_and_validates(self, field_names, expected_archetype):
        metadata = _make_metadata(field_names, row_scale=100)
        spec = build_heuristic_spec(metadata)
        assert spec.classification.archetype == expected_archetype
        starter, reference = generate_scaffold_from_spec(f"smoke-{expected_archetype.value}", spec)
        report = validate_package(starter, reference, spec_to_blueprint(spec))
        assert report.passed, report.errors
