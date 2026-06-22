"""Runtime spec resolution for legacy demo-* backlog items."""

from __future__ import annotations

from ..ai_pm.models import BacklogItem, ChallengeTrack
from .archetype_catalog import build_heuristic_spec
from .legacy_router import use_legacy_factory
from .models import TechnicalArchetype
from .spec_models import IngestKind, TechnicalChallengeSpec


def build_legacy_spec_for_demo(item: BacklogItem) -> TechnicalChallengeSpec | None:
    """Synthesize a minimal spec for demo seeds without mutating store."""
    demo_id = item.id
    title = item.microprd.title if item.microprd else (item.scores.suggested_title if item.scores else "Demo challenge")

    if demo_id == "demo-003" or (item.track is None and "query" in title.lower()):
        return build_heuristic_spec(
            item.metadata,
            source_label=item.source_label,
            suggested_title=title,
            founder_override=TechnicalArchetype.data_core,
        )

    if item.track == ChallengeTrack.product_feature:
        return None

    override: TechnicalArchetype | None = None
    if demo_id in ("demo-001", "demo-002"):
        override = TechnicalArchetype.data_core
    elif demo_id in ("demo-004", "demo-006"):
        override = TechnicalArchetype.idempotency_engine
    elif demo_id == "demo-005":
        return None  # product track handled elsewhere
    elif demo_id == "demo-007":
        override = TechnicalArchetype.algorithm

    return build_heuristic_spec(
        item.metadata,
        source_label=item.source_label,
        suggested_title=title,
        founder_override=override,
    )


def resolve_challenge_spec(item: BacklogItem) -> TechnicalChallengeSpec | None:
    """Return persisted spec or synthesize for legacy demo items."""
    if item.challenge_spec is not None:
        return item.challenge_spec
    if use_legacy_factory(item.id, item.track):
        return build_legacy_spec_for_demo(item)
    return None
