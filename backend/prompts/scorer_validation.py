"""Validate LLM triage scorer output: signal checklist vs final 0-100 scores."""

from __future__ import annotations

import logging
from typing import Any

from backend.ai_pm.models import TechScores

logger = logging.getLogger(__name__)

_SEVERITY_KEYS = (
    "sev_error_dominant",
    "sev_error_present",
    "sev_production_scale",
    "sev_infra_shape",
    "sev_data_integrity",
)

_FRICTION_KEYS = (
    "fric_high_event_volume",
    "fric_warn_or_error_stream",
    "fric_multi_event_types",
    "fric_user_path",
    "fric_repeated_pattern",
)

_SENSITIVITY_KEYS = (
    "sens_payment_financial",
    "sens_auth_secrets",
    "sens_pii_identity",
    "sens_health_regulated",
    "sens_proprietary_domain",
)


def _bool_map(raw: Any, keys: tuple[str, ...]) -> dict[str, bool]:
    if not isinstance(raw, dict):
        return {k: False for k in keys}
    return {k: bool(raw.get(k)) for k in keys}


def _min_severity(sev: dict[str, bool]) -> int:
    if sev["sev_error_dominant"] or sev["sev_data_integrity"]:
        return 60
    if sev["sev_error_present"] or sev["sev_production_scale"] or sev["sev_infra_shape"]:
        return 40
    if any(sev.values()):
        return 20
    return 0


def _max_severity_when_no_signals(sev: dict[str, bool]) -> int | None:
    if any(sev.values()):
        return None
    return 39


def _min_friction(fric: dict[str, bool]) -> int:
    true_count = sum(fric.values())
    if true_count >= 3:
        return 60
    if true_count == 2:
        return 40
    if true_count == 1:
        return 20
    return 0


def _max_friction_when_no_signals(fric: dict[str, bool]) -> int | None:
    if any(fric.values()):
        return None
    return 39


def _min_sensitivity(sens: dict[str, bool]) -> int:
    if sens["sens_payment_financial"] or sens["sens_auth_secrets"] or sens["sens_health_regulated"]:
        return 60
    if sens["sens_pii_identity"] or sens["sens_proprietary_domain"]:
        return 40
    if any(sens.values()):
        return 20
    return 0


def _max_sensitivity_when_no_signals(sens: dict[str, bool]) -> int | None:
    if any(sens.values()):
        return None
    return 39


def validate_scorer_result(result: dict[str, Any]) -> list[str]:
    """Return human-readable errors; empty list means acceptable."""
    errors: list[str] = []

    for key in ("severity", "friction", "sensitivity"):
        try:
            val = int(result[key])
        except (KeyError, TypeError, ValueError):
            errors.append(f"missing or non-integer {key}")
            continue
        if not 0 <= val <= 100:
            errors.append(f"{key}={val} out of range 0-100")

    if errors:
        return errors

    signals = result.get("signals")
    if not isinstance(signals, dict):
        return errors

    sev = _bool_map(signals.get("severity"), _SEVERITY_KEYS)
    fric = _bool_map(signals.get("friction"), _FRICTION_KEYS)
    sens = _bool_map(signals.get("sensitivity"), _SENSITIVITY_KEYS)

    severity = int(result["severity"])
    friction = int(result["friction"])
    sensitivity = int(result["sensitivity"])

    sev_floor = _min_severity(sev)
    if severity < sev_floor:
        errors.append(f"severity {severity} below floor {sev_floor} for signals {sev}")

    sev_cap = _max_severity_when_no_signals(sev)
    if sev_cap is not None and severity > sev_cap:
        errors.append(f"severity {severity} above cap {sev_cap} with no severity signals")

    fric_floor = _min_friction(fric)
    if friction < fric_floor:
        errors.append(f"friction {friction} below floor {fric_floor} for signals {fric}")

    fric_cap = _max_friction_when_no_signals(fric)
    if fric_cap is not None and friction > fric_cap:
        errors.append(f"friction {friction} above cap {fric_cap} with no friction signals")

    sens_floor = _min_sensitivity(sens)
    if sensitivity < sens_floor:
        errors.append(f"sensitivity {sensitivity} below floor {sens_floor} for signals {sens}")

    sens_cap = _max_sensitivity_when_no_signals(sens)
    if sens_cap is not None and sensitivity > sens_cap:
        errors.append(f"sensitivity {sensitivity} above cap {sens_cap} with no sensitivity signals")

    return errors


def llm_result_to_scores(result: dict[str, Any]) -> TechScores | None:
    """Parse LLM JSON into TechScores, or None if validation fails."""
    errors = validate_scorer_result(result)
    if errors:
        logger.warning("LLM scorer validation failed: %s", "; ".join(errors))
        return None

    return TechScores(
        severity=int(result["severity"]),
        friction=int(result["friction"]),
        sensitivity=int(result["sensitivity"]),
        sensitivity_reason=str(result.get("sensitivity_reason", "")),
        suggested_title=str(result.get("suggested_title", "Untitled challenge")),
    )
