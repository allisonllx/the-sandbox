"""Sponsor Fit — product track (challenge-specific persona and problem framing)."""

from __future__ import annotations

import re

from ..sandbox.models import SubmissionRecord
from .models import ChallengeContext, ScoreLayer

_VALID_LINK_KEYS = frozenset({"figma", "deployment", "github"})


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def assess_sponsor_product(
    record: SubmissionRecord,
    context: ChallengeContext,
) -> ScoreLayer:
    """Challenge-scoped product judgment — keyword and narrative fit per Micro-PRD."""
    notes: list[str] = []
    files = record.files
    links = record.links or {}

    design = files.get("DESIGN.md", "")
    has_design = bool(design.strip())
    design_words = _word_count(design) if has_design else 0
    design_lower = design.lower()
    js_content = files.get("src/app.js", "")

    for key in links:
        if key not in _VALID_LINK_KEYS:
            notes.append(f"Ignored unknown link key: {key}")

    persona_fit = 30
    if has_design:
        persona_fit += min(30, design_words // 4)
        if "persona" in design_lower:
            persona_fit += 15
    if "merchant" in design_lower or "merchant" in js_content.lower():
        persona_fit += 15

    problem_framing = 25
    if "trade-off" in design_lower or "trade off" in design_lower:
        problem_framing += 25
    for criterion in context.definition_of_success:
        if any(t in design_lower for t in criterion.lower().split()[:2] if len(t) > 3):
            problem_framing += 10
    problem_framing = min(100, problem_framing)

    ux_judgment = 25
    if "cart" in js_content.lower():
        ux_judgment += 20
    if "responsive" in design_lower or "@media" in files.get("src/styles.css", ""):
        ux_judgment += 20
    ux_judgment = min(100, ux_judgment)

    communication = min(100, 20 + design_words // 2) if has_design else 15

    if links.get("figma"):
        notes.append("Figma link recorded for sponsor review.")
    if links.get("deployment"):
        notes.append("Deployment link recorded for sponsor review.")

    dimensions = {
        "persona_fit": min(100, persona_fit),
        "problem_framing": problem_framing,
        "ux_judgment": ux_judgment,
        "communication": communication,
    }
    score = int(round(sum(dimensions.values()) / len(dimensions)))

    return ScoreLayer(
        dimensions=dimensions,
        score=score,
        summary=(
            "Strong product sponsor fit."
            if min(dimensions.values()) >= 60
            else "Submission received — strengthen DESIGN.md trade-offs and prototype narrative."
        ),
        notes=notes,
    )
