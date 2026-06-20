"""Heuristic track router — suggests innovation track from sanitized metadata."""

from __future__ import annotations

from dataclasses import dataclass

from ..privacy_proxy.models import SanitizedMetadata
from .models import ChallengeTrack, DeliverableType

_PRODUCT_FIELD_HINTS = frozenset(
    {
        "feature_request",
        "ux_friction",
        "screen_name",
        "user_journey",
        "checkout_step",
        "merchant_id",
        "discovery_query",
        "cart_abandon",
        "nps_score",
        "ui_component",
    }
)

_PRODUCT_EVENT_HINTS = frozenset(
    {
        "[product_feedback]",
        "[feature_request]",
        "[ux_research]",
        "[user_research]",
    }
)

_TECH_FIELD_HINTS = frozenset(
    {
        "execution_time_ms",
        "query_hash",
        "rows_scanned",
        "index_hit",
        "cache_status",
        "retry_count",
        "gateway_response_code",
        "error_code",
        "latency_ms",
    }
)


@dataclass
class TrackSuggestion:
    track: ChallengeTrack
    confidence: float
    rationale: str
    brand_proxy: str
    evaluation_focus: list[str]
    deliverable_types: list[DeliverableType]


def suggest_track(
    metadata: SanitizedMetadata,
    source_label: str = "",
    title: str = "",
) -> TrackSuggestion:
    """Classify metadata into an innovation track using deterministic heuristics."""
    field_names = {f.name.lower() for f in metadata.fields}
    events = {e.event_type.lower() for e in metadata.event_type_frequencies}
    label_lower = source_label.lower()
    title_lower = title.lower()

    product_score = len(field_names & _PRODUCT_FIELD_HINTS)
    product_score += sum(1 for e in events if e in _PRODUCT_EVENT_HINTS)
    product_score += sum(
        1
        for token in ("feature", "ux", "product", "merchant", "checkout", "discovery")
        if token in label_lower or token in title_lower
    )

    tech_score = len(field_names & _TECH_FIELD_HINTS)
    tech_score += sum(
        1
        for token in ("log", "apm", "datadog", "error", "timeout", "db", "cdn", "cache")
        if token in label_lower or token in title_lower
    )

    if product_score > tech_score:
        return TrackSuggestion(
            track=ChallengeTrack.product_feature,
            confidence=min(0.95, 0.55 + product_score * 0.1),
            rationale=(
                "Metadata resembles product/UX feedback (feature requests, user journeys, "
                "or merchant-facing flows) rather than infra debugging."
            ),
            brand_proxy="EatsHub",
            evaluation_focus=[
                "Information architecture",
                "Mobile-first responsive layout",
                "Checkout flow completeness",
                "Design trade-off reasoning",
            ],
            deliverable_types=[
                DeliverableType.frontend_prototype,
                DeliverableType.external_link,
                DeliverableType.mixed,
            ],
        )

    return TrackSuggestion(
        track=ChallengeTrack.technical,
        confidence=min(0.95, 0.55 + tech_score * 0.1),
        rationale=(
            "Metadata resembles engineering telemetry (performance, reliability, or data-layer signals)."
        ),
        brand_proxy="DataStream",
        evaluation_focus=[
            "Correctness",
            "Performance",
            "Error handling",
            "Code structure",
        ],
        deliverable_types=[DeliverableType.code_repo],
    )
