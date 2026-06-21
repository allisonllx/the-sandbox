"""Tests for triage scorer signal validation."""

from __future__ import annotations

from unittest.mock import MagicMock

from backend.ai_pm import scorer as scorer_module
from backend.ai_pm.llm_client import LLMUnavailableError
from backend.ai_pm.prompts.scorer_validation import llm_result_to_scores, validate_scorer_result
from backend.privacy_proxy.models import EventFrequency, FieldMetadata, InputFormat, SanitizedMetadata


def _base_result(**overrides):
    payload = {
        "signals": {
            "severity": {
                "sev_error_dominant": False,
                "sev_error_present": False,
                "sev_production_scale": False,
                "sev_infra_shape": False,
                "sev_data_integrity": False,
            },
            "friction": {
                "fric_high_event_volume": False,
                "fric_warn_or_error_stream": False,
                "fric_multi_event_types": False,
                "fric_user_path": False,
                "fric_repeated_pattern": False,
            },
            "sensitivity": {
                "sens_payment_financial": False,
                "sens_auth_secrets": False,
                "sens_pii_identity": False,
                "sens_health_regulated": False,
                "sens_proprietary_domain": False,
            },
        },
        "severity": 25,
        "friction": 30,
        "sensitivity": 20,
        "sensitivity_reason": "Generic telemetry only.",
        "suggested_title": "Pipeline latency drill",
    }
    payload.update(overrides)
    return payload


def test_valid_signals_accepted():
    assert validate_scorer_result(_base_result()) == []
    scores = llm_result_to_scores(_base_result())
    assert scores is not None
    assert scores.sensitivity == 20


def test_payment_signal_requires_high_sensitivity():
    result = _base_result()
    result["signals"]["sensitivity"]["sens_payment_financial"] = True
    result["sensitivity"] = 45
    assert validate_scorer_result(result)
    assert llm_result_to_scores(result) is None


def test_no_sensitivity_signals_caps_score():
    result = _base_result(sensitivity=55)
    assert validate_scorer_result(result)
    assert llm_result_to_scores(result) is None


def test_missing_signals_block_skips_signal_checks():
    result = {
        "severity": 70,
        "friction": 50,
        "sensitivity": 30,
        "sensitivity_reason": "ok",
        "suggested_title": "Title",
    }
    assert validate_scorer_result(result) == []
    assert llm_result_to_scores(result) is not None


def test_inconsistent_llm_response_falls_back_to_heuristic():
    stub = MagicMock()
    bad = _base_result()
    bad["signals"]["sensitivity"]["sens_auth_secrets"] = True
    bad["sensitivity"] = 25
    stub.chat.return_value = bad

    metadata = SanitizedMetadata(
        format_detected=InputFormat.log,
        fields=[FieldMetadata(name="status", inferred_type="string")],
        approximate_row_scale=100,
        event_type_frequencies=[EventFrequency(event_type="INFO", count=100)],
    )
    scores = scorer_module.score(metadata, client=stub)
    assert 0 <= scores.sensitivity <= 100

    failing = MagicMock()
    failing.chat.side_effect = LLMUnavailableError("no key")
    heuristic = scorer_module.score(metadata, client=failing)
    assert scores.severity == heuristic.severity
