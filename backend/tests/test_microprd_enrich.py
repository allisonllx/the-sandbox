"""Tests for blueprint-aware Micro-PRD enrichment."""

from __future__ import annotations

from backend.ai_pm.microprd_enrich import enrich_from_blueprint
from backend.ai_pm.models import MicroPRD
from backend.challenge_factory.models import ChallengeBlueprint, DataPlane, TechnicalArchetype
from backend.privacy_proxy.models import EventFrequency, FieldMetadata, InputFormat, SanitizedMetadata


def _metadata(*names: str) -> SanitizedMetadata:
    return SanitizedMetadata(
        format_detected=InputFormat.text,
        fields=[FieldMetadata(name=n, inferred_type="string", sample_count=100) for n in names],
        approximate_row_scale=1000,
        event_type_frequencies=[EventFrequency(event_type="INFO", count=900)],
    )


class TestMicroPRDEnrich:
    def test_algorithm_brief_matches_starter_not_sqlite(self):
        prd = MicroPRD(
            challenge_id="x",
            title="Optimise data pipeline performance",
            context="generic pipeline",
            definition_of_success=["old"],
            structural_constraints=["old"],
        )
        blueprint = ChallengeBlueprint(
            archetype=TechnicalArchetype.algorithm,
            primary_focus="Fix clamp_values so values respect low/high bounds",
            data_plane=DataPlane.none,
            edit_targets=["src/solution.py"],
        )
        enriched = enrich_from_blueprint(
            prd,
            blueprint,
            _metadata("retry_count"),
            source_label="Founder brief — payment retries",
        )
        assert "clamp_values" in enriched.context.lower() or "pure-python" in enriched.context.lower()
        assert "sqlite" not in enriched.context.lower()
        assert "src/solution.py" in " ".join(enriched.structural_constraints)
        assert enriched.title != "Optimise data pipeline performance"

    def test_data_core_includes_schema_and_anomalies(self):
        prd = MicroPRD(
            challenge_id="x",
            title="Generic",
            context="generic",
            definition_of_success=["old"],
            structural_constraints=["old"],
        )
        blueprint = ChallengeBlueprint(
            archetype=TechnicalArchetype.data_core,
            primary_focus="Optimize batch session lookups",
            data_plane=DataPlane.sqlite,
            edit_targets=["src/queries.py"],
        )
        anomalies = ["Missing index on execution_time_ms"]
        enriched = enrich_from_blueprint(
            prd,
            blueprint,
            _metadata("execution_time_ms", "query_hash"),
            source_label="Log triage — slow queries",
            dataset_anomalies=anomalies,
        )
        joined = enriched.context + " ".join(enriched.definition_of_success)
        assert "docs/DATA.md" in enriched.context or "SQLite" in enriched.context
        assert "Missing index" in enriched.context
        assert "execution_time_ms" in enriched.context
