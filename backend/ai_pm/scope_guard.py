"""Scope guard — blocks publish when estimated student effort exceeds 8 hours."""

from __future__ import annotations

from dataclasses import dataclass

from ..privacy_proxy.models import SanitizedMetadata
from .models import BacklogItem

_MAX_HOURS = 8

_FULL_APP_PHRASES = (
    "full app",
    "full application",
    "entire platform",
    "complete product",
    "end-to-end app",
    "whole system rebuild",
    "full stack app",
)

_OVERSIZED_SCOPE_IDS = frozenset({"demo-007"})


@dataclass
class ScopeCheckResult:
    allowed: bool
    estimated_hours: float
    reason: str
    suggested_breakdown: list[str]


def _estimate_hours(metadata: SanitizedMetadata, title: str, source_label: str) -> float:
    field_count = len(metadata.fields)
    row_scale = metadata.approximate_row_scale or 0
    event_types = len(metadata.event_type_frequencies)

    hours = 1.5
    hours += field_count * 0.25
    hours += min(row_scale / 15000, 2.5)
    hours += event_types * 0.2

    combined = f"{title} {source_label}".lower()
    if any(p in combined for p in ("checkout", "discovery", "merchant", "ux", "feature")):
        hours += 2.0
    if any(p in combined for p in ("migration", "rewrite", "platform", "multi-module")):
        hours += 3.0

    return round(hours, 1)


def _implies_full_app(title: str, source_label: str) -> bool:
    combined = f"{title} {source_label}".lower()
    return any(p in combined for p in _FULL_APP_PHRASES)


def check_scope(item: BacklogItem) -> ScopeCheckResult:
    """Return whether this backlog item may be published as a student challenge."""
    if item.id in _OVERSIZED_SCOPE_IDS:
        return ScopeCheckResult(
            allowed=False,
            estimated_hours=24.0,
            reason=(
                "This scope exceeds 8 hours of work. The AI PM cannot publish a full application "
                "build as a student challenge."
            ),
            suggested_breakdown=[
                "Split into a modular sub-task (e.g. proximity matching algorithm only).",
                "Publish the merchant list UI as a separate Product Feature sprint.",
                "Defer checkout + payments to a follow-on bounty after MVP validation.",
            ],
        )

    title = item.scores.suggested_title if item.scores else ""
    hours = _estimate_hours(item.metadata, title, item.source_label)

    if _implies_full_app(title, item.source_label):
        return ScopeCheckResult(
            allowed=False,
            estimated_hours=hours,
            reason="Backlog item implies a full-application build, which exceeds student scope limits.",
            suggested_breakdown=[
                "Extract one vertical slice (e.g. discovery list view only).",
                "Cap deliverables to starter files + DESIGN.md reasoning.",
            ],
        )

    if hours > _MAX_HOURS:
        return ScopeCheckResult(
            allowed=False,
            estimated_hours=hours,
            reason=(
                f"Estimated effort is ~{hours}h — exceeds the {_MAX_HOURS}h student scope cap. "
                "Break this into a modular sub-task before publishing."
            ),
            suggested_breakdown=[
                "Identify the smallest shippable slice that still tests real skill.",
                "Remove parallel workstreams (e.g. separate infra from UI prototype).",
            ],
        )

    return ScopeCheckResult(
        allowed=True,
        estimated_hours=hours,
        reason=f"Within scope (~{hours}h estimated).",
        suggested_breakdown=[],
    )
