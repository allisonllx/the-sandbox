"""
Scores a SanitizedMetadata blob with three indices:
  - Severity    (0-100): impact on system performance / stability
  - Friction    (0-100): volume / frequency of user-facing incidents
  - Sensitivity (0-100): IP or security exposure risk if published

Derives a Red / Yellow / Green sensitivity tag from the sensitivity score.

Primary path: calls the LLM with the anonymized metadata (ONLY structural
descriptors — never raw content).

Fallback path: if no LLM backend is configured (no LLM_BASE_URL / OPENAI_API_KEY),
the scorer uses a fast heuristic so the rest of the pipeline still works.
"""

from __future__ import annotations

import json
import logging

from ..privacy_proxy.models import SanitizedMetadata
from .llm_client import LLMClientProtocol, LLMTier, LLMUnavailableError, get_default_client
from .models import SensitivityTag, TechScores
from backend.prompts.scorer import SCORER_SYSTEM_PROMPT
from backend.prompts.scorer_validation import llm_result_to_scores

logger = logging.getLogger(__name__)


def _build_user_message(metadata: SanitizedMetadata) -> str:
    """Serialize the sanitized metadata into a compact JSON string for the LLM."""
    payload = {
        "format": metadata.format_detected,
        "fields": [
            {"name": f.name, "type": f.inferred_type, "nullable": f.nullable}
            for f in metadata.fields
        ],
        "nested_paths": metadata.nested_paths,
        "approximate_row_scale": metadata.approximate_row_scale,
        "event_type_frequencies": [
            {"event_type": e.event_type, "count": e.count}
            for e in metadata.event_type_frequencies
        ],
        "pii_types_detected": [d.pii_type for d in metadata.pii_detections],
    }
    return json.dumps(payload, indent=2)


def _heuristic_score(metadata: SanitizedMetadata) -> TechScores:
    """
    Rule-based fallback scorer — runs when no LLM is available.

    Heuristics:
      severity    ~ error-event proportion × scale
      friction    ~ total event volume (capped) + warning proportion
      sensitivity ~ presence of payment/auth/user field names
    """
    field_names = {f.name.lower() for f in metadata.fields}
    scale = metadata.approximate_row_scale or 0

    # --- Severity ---
    total_events = sum(e.count for e in metadata.event_type_frequencies)
    error_events = sum(
        e.count
        for e in metadata.event_type_frequencies
        if e.event_type in {"ERROR", "CRITICAL", "FATAL", "ERR"}
    )
    sev = min(100, int((error_events / max(total_events, 1)) * 100) + min(30, scale // 1000))

    # --- Friction ---
    warn_events = sum(
        e.count
        for e in metadata.event_type_frequencies
        if "WARN" in e.event_type
    )
    fric = min(100, int((warn_events + error_events) / max(total_events, 1) * 80) + 20)

    # --- Sensitivity ---
    HIGH_SENSITIVITY_TERMS = {
        "password", "secret", "token", "key", "auth", "credential",
        "payment", "card", "billing", "ssn", "credit", "debit",
        "salary", "income", "net_worth", "balance", "account",
        "health", "medical", "diagnosis", "prescription",
    }
    MEDIUM_SENSITIVITY_TERMS = {
        "user", "email", "phone", "address", "dob", "birth",
        "location", "ip", "device", "session", "cookie",
    }
    high_hits = sum(1 for t in HIGH_SENSITIVITY_TERMS if any(t in n for n in field_names))
    med_hits = sum(1 for t in MEDIUM_SENSITIVITY_TERMS if any(t in n for n in field_names))
    raw_sens = min(100, high_hits * 20 + med_hits * 8)

    sensitivity_reason = (
        "Contains field names associated with financial or auth data."
        if high_hits
        else "Contains user-identifying field name patterns."
        if med_hits
        else "No high-sensitivity field patterns detected."
    )

    db_hints = {"query_hash", "execution_time_ms", "table_name", "rows_scanned", "index_hit"}
    retry_hints = {"retry_count", "idempotency_key", "gateway_response_code"}
    if field_names & retry_hints or any("retry" in n for n in field_names):
        suggested_title = "Harden idempotent payment webhook retries"
    elif field_names & db_hints:
        suggested_title = "Optimise SQLite session lookup latency"
    elif any("payment" in n or "charge" in n for n in field_names):
        suggested_title = "Fix duplicate payment retry side effects"
    elif scale > 5000:
        suggested_title = "Improve batch event processing throughput"
    else:
        suggested_title = "Resolve production incident in core service"

    return TechScores(
        severity=sev,
        friction=fric,
        sensitivity=raw_sens,
        sensitivity_reason=sensitivity_reason,
        suggested_title=suggested_title,
    )


def score(
    metadata: SanitizedMetadata,
    client: LLMClientProtocol | None = None,
) -> TechScores:
    """
    Score *metadata* and return a TechScores object.

    Args:
        metadata: Output of the privacy proxy — structural descriptors only.
        client:   LLM client to use; defaults to the module-level singleton.
                  Pass a stub here in tests.

    The LLM receives ONLY the anonymized metadata, never raw content.
    Falls back to heuristic scoring if the LLM is unavailable.
    """
    if client is None:
        client = get_default_client()

    user_msg = _build_user_message(metadata)

    try:
        result = client.chat(system=SCORER_SYSTEM_PROMPT, user=user_msg, tier=LLMTier.sensitive)
        scores = llm_result_to_scores(result)
        if scores is None:
            logger.warning("LLM scorer signals inconsistent with scores, using heuristic scorer.")
            return _heuristic_score(metadata)
        return scores
    except LLMUnavailableError as exc:
        logger.warning("LLM unavailable, using heuristic scorer: %s", exc)
        return _heuristic_score(metadata)
    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("LLM response malformed (%s), using heuristic scorer.", exc)
        return _heuristic_score(metadata)
