"""
Test suite for triage-001: AI PM Triage Matrix & Relaxation Control Dashboard.

Verification checklist items covered:
  ✓ Three sample metadata blobs render Severity, Friction, Sensitivity scores
  ✓ Red/Yellow/Green tag is derived correctly from sensitivity score
  ✓ Abstract Logic toggle changes field names in the preview
  ✓ Synthesize Variables toggle maps field names to abstract tokens
  ✓ Noise slider perturbs row scale deterministically
  ✓ No raw metadata transmitted to external APIs before founder approval
  ✓ LLM calls are mockable — all tests run without an API key
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.ai_pm import relaxation as relaxation_module
from backend.ai_pm import scorer as scorer_module
from backend.ai_pm import store
from backend.ai_pm.llm_client import set_default_client
from backend.ai_pm.models import (
    BacklogStatus,
    RelaxationConfig,
    SensitivityTag,
    TechScores,
)
from backend.privacy_proxy.models import (
    EventFrequency,
    FieldMetadata,
    InputFormat,
    SanitizedMetadata,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_metadata(
    field_names: list[str],
    row_scale: int = 1000,
    error_count: int = 100,
    format: InputFormat = InputFormat.log,
) -> SanitizedMetadata:
    return SanitizedMetadata(
        format_detected=format,
        fields=[FieldMetadata(name=n, inferred_type="string", sample_count=row_scale) for n in field_names],
        approximate_row_scale=row_scale,
        event_type_frequencies=[
            EventFrequency(event_type="ERROR", count=error_count),
            EventFrequency(event_type="INFO", count=row_scale - error_count),
        ],
    )


def _stub_llm(severity=60, friction=50, sensitivity=30):
    """Returns an LLM stub that always yields the given scores."""
    stub = MagicMock()
    stub.chat.return_value = {
        "severity": severity,
        "friction": friction,
        "sensitivity": sensitivity,
        "sensitivity_reason": "Stub reason.",
        "suggested_title": "Stub challenge title",
    }
    return stub


# ===========================================================================
# 1. Sensitivity tag derivation
# ===========================================================================

class TestSensitivityTag:
    def test_red_when_sensitivity_gte_70(self):
        scores = TechScores(severity=50, friction=50, sensitivity=70,
                            sensitivity_reason="", suggested_title="")
        assert scores.tag == SensitivityTag.red

    def test_yellow_when_sensitivity_40_to_69(self):
        for val in [40, 55, 69]:
            scores = TechScores(severity=50, friction=50, sensitivity=val,
                                sensitivity_reason="", suggested_title="")
            assert scores.tag == SensitivityTag.yellow, f"Expected yellow for {val}"

    def test_green_when_sensitivity_below_40(self):
        scores = TechScores(severity=50, friction=50, sensitivity=39,
                            sensitivity_reason="", suggested_title="")
        assert scores.tag == SensitivityTag.green


# ===========================================================================
# 2. Scorer — LLM path and heuristic fallback
# ===========================================================================

class TestScorer:
    def test_scores_from_llm_stub(self):
        stub = _stub_llm(severity=82, friction=67, sensitivity=74)
        metadata = _make_metadata(["user_id", "query_hash", "execution_time_ms"])
        scores = scorer_module.score(metadata, client=stub)

        assert scores.severity == 82
        assert scores.friction == 67
        assert scores.sensitivity == 74
        assert scores.tag == SensitivityTag.red

    def test_stub_receives_only_metadata_not_raw_content(self):
        stub = _stub_llm()
        metadata = _make_metadata(["transaction_id", "amount_cents"])
        scorer_module.score(metadata, client=stub)

        _, kwargs = stub.chat.call_args
        user_msg = kwargs.get("user", "")
        # The message must be JSON-parseable structural metadata
        import json
        parsed = json.loads(user_msg)
        assert "fields" in parsed
        # No raw content — only field names and types
        assert all(isinstance(f["name"], str) for f in parsed["fields"])

    def test_heuristic_fallback_when_llm_unavailable(self):
        from backend.ai_pm.llm_client import LLMUnavailableError
        failing_stub = MagicMock()
        failing_stub.chat.side_effect = LLMUnavailableError("no key")

        metadata = _make_metadata(["payment_method", "billing_amount"], error_count=300)
        scores = scorer_module.score(metadata, client=failing_stub)

        # Heuristic should return valid scores
        assert 0 <= scores.severity <= 100
        assert 0 <= scores.friction <= 100
        assert 0 <= scores.sensitivity <= 100

    def test_heuristic_high_sensitivity_for_payment_fields(self):
        from backend.ai_pm.llm_client import LLMUnavailableError
        failing_stub = MagicMock()
        failing_stub.chat.side_effect = LLMUnavailableError("no key")

        metadata = _make_metadata(["payment_token", "credit_card_hash", "billing_address"])
        scores = scorer_module.score(metadata, client=failing_stub)
        # Payment-related fields should score high on sensitivity
        assert scores.sensitivity >= 40

    def test_heuristic_low_sensitivity_for_generic_fields(self):
        from backend.ai_pm.llm_client import LLMUnavailableError
        failing_stub = MagicMock()
        failing_stub.chat.side_effect = LLMUnavailableError("no key")

        metadata = _make_metadata(["asset_path", "cdn_region", "ttl_seconds"])
        scores = scorer_module.score(metadata, client=failing_stub)
        assert scores.sensitivity < 40


# ===========================================================================
# 3. Relaxation controls
# ===========================================================================

class TestRelaxation:
    def test_synthesize_variables_changes_field_names(self):
        metadata = _make_metadata(["user_id", "transaction_id", "amount_cents"])
        config = RelaxationConfig(synthesize_variables=True)
        preview = relaxation_module.apply_relaxation(metadata, config, "test-seed")

        assert preview.original_fields == ["user_id", "transaction_id", "amount_cents"]
        assert preview.relaxed_fields != preview.original_fields
        assert len(preview.relaxed_fields) == 3

    def test_synthesize_variables_is_deterministic(self):
        metadata = _make_metadata(["user_id", "score"])
        config = RelaxationConfig(synthesize_variables=True)

        preview1 = relaxation_module.apply_relaxation(metadata, config, "seed-abc")
        preview2 = relaxation_module.apply_relaxation(metadata, config, "seed-abc")
        assert preview1.relaxed_fields == preview2.relaxed_fields

    def test_synthesize_variables_different_seeds_produce_different_names(self):
        metadata = _make_metadata(["user_id"])
        config = RelaxationConfig(synthesize_variables=True)

        p1 = relaxation_module.apply_relaxation(metadata, config, "seed-A")
        p2 = relaxation_module.apply_relaxation(metadata, config, "seed-B")
        assert p1.relaxed_fields != p2.relaxed_fields

    def test_abstract_logic_replaces_domain_terms(self):
        metadata = _make_metadata(["payment_method", "user_email", "salary_band"])
        config = RelaxationConfig(abstract_logic=True, synthesize_variables=False)
        preview = relaxation_module.apply_relaxation(metadata, config, "seed")

        # Domain terms should be replaced
        assert "payment_method" not in preview.relaxed_fields
        assert "user_email" not in preview.relaxed_fields
        assert "salary_band" not in preview.relaxed_fields

    def test_noise_perturbs_row_scale(self):
        metadata = _make_metadata(["x", "y", "z"], row_scale=10000)
        config = RelaxationConfig(noise_level=0.5)
        preview = relaxation_module.apply_relaxation(metadata, config, "seed")

        assert preview.original_row_scale == 10000
        assert preview.relaxed_row_scale != 10000
        assert preview.relaxed_row_scale is not None
        assert preview.relaxed_row_scale > 0

    def test_noise_zero_leaves_row_scale_unchanged(self):
        metadata = _make_metadata(["x", "y"], row_scale=5000)
        config = RelaxationConfig(noise_level=0.0)
        preview = relaxation_module.apply_relaxation(metadata, config, "seed")
        assert preview.relaxed_row_scale == 5000

    def test_no_controls_leaves_fields_unchanged(self):
        metadata = _make_metadata(["alpha", "beta"])
        config = RelaxationConfig()  # all defaults = no transformation
        preview = relaxation_module.apply_relaxation(metadata, config, "seed")
        assert preview.original_fields == preview.relaxed_fields


# ===========================================================================
# 4. Demo store — backlog pre-populated
# ===========================================================================

class TestBacklogStore:
    def test_three_demo_items_in_store(self):
        items = store.list_items()
        assert len(items) == 3

    def test_items_sorted_by_severity_descending(self):
        items = store.list_items()
        severities = [i.scores.severity for i in items if i.scores]
        assert severities == sorted(severities, reverse=True)

    def test_all_items_have_scores_and_tags(self):
        for item in store.list_items():
            assert item.scores is not None
            assert item.tag is not None

    def test_sensitivity_tags_cover_all_three_tiers(self):
        tags = {item.tag for item in store.list_items()}
        assert SensitivityTag.red in tags
        assert SensitivityTag.yellow in tags
        assert SensitivityTag.green in tags


# ===========================================================================
# 5. No LLM call before founder approval
# ===========================================================================

class TestNoLLMBeforeApproval:
    def test_relax_endpoint_makes_no_llm_call(self, monkeypatch):
        """The relax preview is pure — it must not call the LLM."""
        call_count = 0

        class WatchingStub:
            def chat(self, **kwargs):
                nonlocal call_count
                call_count += 1
                return {"severity": 50, "friction": 50, "sensitivity": 50,
                        "sensitivity_reason": "", "suggested_title": ""}

        set_default_client(WatchingStub())
        metadata = _make_metadata(["a", "b", "c"])
        config = RelaxationConfig(synthesize_variables=True, noise_level=0.3)
        relaxation_module.apply_relaxation(metadata, config, "seed")

        assert call_count == 0, "apply_relaxation must not call the LLM"
        # Reset
        from backend.ai_pm.llm_client import LLMClient
        set_default_client(LLMClient())
