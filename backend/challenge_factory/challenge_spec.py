"""Single-pass challenge spec generation (LLM + heuristic fallback)."""

from __future__ import annotations

import json
import logging

from ..ai_pm.llm_client import LLMClientProtocol, LLMTier, LLMUnavailableError, get_default_client
from ..privacy_proxy.models import SanitizedMetadata
from backend.prompts.challenge_spec import CHALLENGE_SPEC_SYSTEM_PROMPT
from .archetype_catalog import build_heuristic_spec
from .models import TechnicalArchetype, normalize_archetype
from .spec_models import IngestKind, TechnicalChallengeSpec

logger = logging.getLogger(__name__)


def _parse_spec_result(raw: dict) -> TechnicalChallengeSpec | None:
    try:
        return TechnicalChallengeSpec.model_validate(raw)
    except (ValueError, TypeError) as exc:
        logger.info("Invalid challenge spec JSON: %s", exc)
        return None


def generate_spec(
    metadata: SanitizedMetadata,
    *,
    source_label: str = "",
    suggested_title: str = "",
    ingest_kind: IngestKind = IngestKind.behavioral_log,
    founder_archetype_override: TechnicalArchetype | None = None,
    llm: LLMClientProtocol | None = None,
) -> TechnicalChallengeSpec:
    """Single-pass spec inference with heuristic fallback."""
    heuristic = build_heuristic_spec(
        metadata,
        source_label=source_label,
        suggested_title=suggested_title,
        ingest_kind=ingest_kind,
        founder_override=founder_archetype_override,
    )

    client = llm or get_default_client()
    payload = {
        "source_label": source_label,
        "ingest_kind": ingest_kind.value,
        "suggested_title": suggested_title,
        "field_names": [f.name for f in metadata.fields],
        "approximate_row_scale": metadata.approximate_row_scale,
        "format": str(metadata.format_detected),
        "heuristic_suggestion": heuristic.model_dump(mode="json"),
        "founder_archetype_override": (
            founder_archetype_override.value if founder_archetype_override else None
        ),
    }
    try:
        result = client.chat(
            system=CHALLENGE_SPEC_SYSTEM_PROMPT,
            user=json.dumps(payload, indent=2),
            temperature=0.2,
            tier=LLMTier.sensitive,
        )
        parsed = _parse_spec_result(result)
        if parsed is not None:
            if founder_archetype_override is not None:
                archetype = normalize_archetype(
                    founder_archetype_override,
                    field_names={f.name for f in metadata.fields},
                )
                parsed = parsed.model_copy(
                    update={
                        "classification": parsed.classification.model_copy(
                            update={"archetype": archetype}
                        )
                    }
                )
            return parsed
    except (LLMUnavailableError, KeyError, TypeError, json.JSONDecodeError) as exc:
        logger.info("Challenge spec LLM unavailable — heuristic fallback: %s", exc)

    return heuristic


def infer_spec_heuristic(
    metadata: SanitizedMetadata,
    *,
    source_label: str = "",
    suggested_title: str = "",
    ingest_kind: IngestKind = IngestKind.behavioral_log,
    founder_archetype_override: TechnicalArchetype | None = None,
) -> TechnicalChallengeSpec:
    """Deterministic spec for tests and offline runs."""
    return build_heuristic_spec(
        metadata,
        source_label=source_label,
        suggested_title=suggested_title,
        ingest_kind=ingest_kind,
        founder_override=founder_archetype_override,
    )
