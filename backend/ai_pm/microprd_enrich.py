"""Blueprint-aware Micro-PRD enrichment — specific briefs that match starter files."""

from __future__ import annotations

from ..challenge_factory.models import ChallengeBlueprint, DataPlane, TechnicalArchetype
from ..privacy_proxy.models import SanitizedMetadata
from .models import MicroPRD

_GENERIC_TITLES = frozenset(
    {
        "optimise data pipeline performance",
        "optimize data pipeline performance",
        "innovation challenge",
        "untitled challenge",
        "stub challenge title",
    }
)


def _field_summary(metadata: SanitizedMetadata | None, limit: int = 6) -> str:
    if not metadata or not metadata.fields:
        return ""
    return ", ".join(f"`{f.name}`" for f in metadata.fields[:limit])


def _title_from_blueprint(blueprint: ChallengeBlueprint, prd: MicroPRD) -> str:
    if prd.title.strip().lower() not in _GENERIC_TITLES:
        return prd.title
    focus = blueprint.primary_focus.strip()
    if focus and focus != "Implement the core module described in the Micro-PRD":
        words = focus.split()
        return " ".join(words[:10]).rstrip(".,;:")
    mapping = {
        TechnicalArchetype.data_core: "Optimise SQLite session lookup latency",
        TechnicalArchetype.integration: "Harden idempotent webhook retries",
        TechnicalArchetype.service_module: "Implement core service module",
        TechnicalArchetype.algorithm: "Fix batch processing logic",
        TechnicalArchetype.data_adjacent: "Extend service with data helpers",
    }
    return mapping.get(blueprint.archetype, prd.title)


def _context_for_blueprint(
    blueprint: ChallengeBlueprint,
    metadata: SanitizedMetadata | None,
    *,
    source_label: str | None,
    dataset_anomalies: list[str] | None,
) -> str:
    label = source_label or "An internal production review surfaced this issue."
    fields = _field_summary(metadata)
    anomalies = dataset_anomalies or []
    anomaly_text = "; ".join(anomalies[:3]) if anomalies else "documented in docs/DATA.md"

    if blueprint.archetype == TechnicalArchetype.data_core:
        return (
            f"**Scenario:** {label}\n\n"
            "The platform ships a synthetic SQLite workload (`events` + `sessions` tables). "
            "Lookup code in the starter is intentionally slow (per-id queries, missing indexes).\n\n"
            f"**Schema hints:** {fields or 'see docs/DATA.md for columns and relationships'}.\n\n"
            f"**Known dataset issues:** {anomaly_text}.\n\n"
            f"**Your task:** {blueprint.primary_focus}"
        )

    if blueprint.archetype == TechnicalArchetype.integration:
        return (
            f"**Scenario:** {label}\n\n"
            "Downstream gateway calls can return transient 502 responses. Without idempotency, "
            "retries duplicate side effects (e.g. double charges).\n\n"
            f"**Metadata hints:** {fields or 'retry and gateway response fields in logs'}.\n\n"
            f"**Your task:** {blueprint.primary_focus}. Wire the handler and idempotency modules "
            "so retries are safe."
        )

    if blueprint.archetype == TechnicalArchetype.algorithm:
        return (
            f"**Scenario:** {label}\n\n"
            "You are given a pure-Python module with a buggy implementation and public unit tests. "
            "No database or external services are required — everything runs in the browser workspace.\n\n"
            f"**Your task:** {blueprint.primary_focus}"
        )

    if blueprint.archetype == TechnicalArchetype.service_module:
        return (
            f"**Scenario:** {label}\n\n"
            "Implement or fix the core service module in the starter project. "
            "Public tests describe the expected behaviour.\n\n"
            f"**Your task:** {blueprint.primary_focus}"
        )

    return (
        f"**Scenario:** {label}\n\n"
        f"**Your task:** {blueprint.primary_focus}"
    )


def _success_criteria(blueprint: ChallengeBlueprint) -> list[str]:
    targets = ", ".join(blueprint.edit_targets) if blueprint.edit_targets else "starter edit targets"
    common = [
        f"Implement the required behaviour in {targets}.",
        "All public tests pass via Run Public Tests in the browser workspace.",
        "Preserve existing function signatures unless the starter explicitly marks TODO sections.",
    ]
    if blueprint.archetype == TechnicalArchetype.data_core:
        return [
            "Reduce redundant SQLite round-trips in the query layer (measurable via public tests).",
            "Preserve row shapes returned by batch_session_lookup and threshold count helpers.",
            *common[:2],
            "Document trade-offs (index vs scan, batch size) in README or code comments.",
        ]
    if blueprint.archetype == TechnicalArchetype.integration:
        return [
            "Duplicate webhook deliveries must not double-charge or double-apply side effects.",
            "Retries respect a bounded attempt count and surface a clear exhaustion error.",
            *common[:2],
        ]
    if blueprint.archetype == TechnicalArchetype.algorithm:
        return [
            "Fix the buggy logic so all public unit tests pass.",
            "Handle edge cases covered in tests/test_public.py (empty input, boundary values).",
            *common[:1],
        ]
    return common


def enrich_from_blueprint(
    prd: MicroPRD,
    blueprint: ChallengeBlueprint,
    metadata: SanitizedMetadata | None = None,
    *,
    source_label: str | None = None,
    dataset_anomalies: list[str] | None = None,
) -> MicroPRD:
    """Replace generic fallback copy with a brief aligned to blueprint + starter."""
    from . import microprd as microprd_module

    title = _title_from_blueprint(blueprint, prd)
    context = _context_for_blueprint(
        blueprint,
        metadata,
        source_label=source_label,
        dataset_anomalies=dataset_anomalies,
    )
    enriched = prd.model_copy(
        update={
            "title": title,
            "context": context,
            "definition_of_success": _success_criteria(blueprint),
        }
    )
    return microprd_module.sync_with_blueprint(enriched, blueprint)
