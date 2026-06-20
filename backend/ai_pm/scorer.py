"""
Scores a SanitizedMetadata blob with three indices:
  - Severity    (0-100): impact on system performance / stability
  - Friction    (0-100): volume / frequency of user-facing incidents
  - Sensitivity (0-100): IP or security exposure risk if published

Derives a Red / Yellow / Green sensitivity tag from the sensitivity score.

Primary path: calls the LLM with the anonymized metadata (ONLY structural
descriptors — never raw content).

Fallback path: if OPENAI_API_KEY is absent or openai is not installed, the
scorer uses a fast heuristic so the rest of the pipeline still works.
"""

from __future__ import annotations

import json
import logging

from ..privacy_proxy.models import SanitizedMetadata
from .llm_client import LLMUnavailableError, LLMClientProtocol, get_default_client
from .models import SensitivityTag, TechScores

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an AI Product Manager performing backlog triage for a growth-stage startup.

You receive ONLY anonymized structural metadata — field names, inferred types, \
event-type frequencies, and row scale. There is NO raw content, NO PII, and NO \
business-specific values in the input.

Score the issue on three axes (0-100 integer each):
  - severity:    How severely does this affect system performance or stability?
  - friction:    How frequently or broadly are users impacted?
  - sensitivity: How risky is it to publish the structural shape of this problem publicly?
                 (Higher = more likely to reveal IP, internal architecture, or exploitable patterns)

Also provide:
  - sensitivity_reason: one sentence (≤ 20 words) explaining the sensitivity score
  - suggested_title:    a public-facing challenge title (≤ 10 words, no internal names)

Respond with ONLY a JSON object matching this exact schema:
{
  "severity": <integer 0-100>,
  "friction": <integer 0-100>,
  "sensitivity": <integer 0-100>,
  "sensitivity_reason": "<string>",
  "suggested_title": "<string>"
}
"""


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

    return TechScores(
        severity=sev,
        friction=fric,
        sensitivity=raw_sens,
        sensitivity_reason=sensitivity_reason,
        suggested_title="Optimise data pipeline performance",
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
        result = client.chat(system=_SYSTEM_PROMPT, user=user_msg)
        return TechScores(
            severity=int(result["severity"]),
            friction=int(result["friction"]),
            sensitivity=int(result["sensitivity"]),
            sensitivity_reason=str(result.get("sensitivity_reason", "")),
            suggested_title=str(result.get("suggested_title", "Untitled challenge")),
        )
    except LLMUnavailableError as exc:
        logger.warning("LLM unavailable, using heuristic scorer: %s", exc)
        return _heuristic_score(metadata)
    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("LLM response malformed (%s), using heuristic scorer.", exc)
        return _heuristic_score(metadata)
