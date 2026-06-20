"""Sponsor Fit — technical track (challenge-specific criteria and taste)."""

from __future__ import annotations

from ..sandbox.models import SubmissionRecord
from .models import ChallengeContext, ScoreLayer


def assess_sponsor_technical(
    record: SubmissionRecord,
    context: ChallengeContext,
) -> ScoreLayer:
    """
    Subjective fit to this challenge's success criteria.

    LLM taste evaluation lands in assessor-001 Phase B; heuristic fallback for MVP.
    """
    notes: list[str] = []
    line_count = sum(len(c.splitlines()) for c in record.files.values())
    has_readme = any(p.lower().endswith("readme.md") for p in record.files)
    combined_text = "\n".join(record.files.values()).lower()

    criteria_alignment = 40
    for criterion in context.definition_of_success:
        tokens = [t for t in criterion.lower().split() if len(t) > 4]
        if any(t in combined_text for t in tokens[:3]):
            criteria_alignment += 8
    criteria_alignment = min(100, criteria_alignment)

    architectural_taste = min(100, 35 + line_count // 3 + (15 if has_readme else 0))
    edge_case_handling = min(100, 30 + (20 if "except" in combined_text or "try:" in combined_text else 0))
    tradeoff_reasoning = min(100, 25 + (25 if has_readme else 0) + (15 if "trade" in combined_text else 0))

    for focus in context.evaluation_focus:
        notes.append(f"Evaluated against focus: {focus}")

    dimensions = {
        "criteria_alignment": criteria_alignment,
        "architectural_taste": architectural_taste,
        "edge_case_handling": edge_case_handling,
        "tradeoff_reasoning": tradeoff_reasoning,
    }
    score = int(round(sum(dimensions.values()) / len(dimensions)))

    return ScoreLayer(
        dimensions=dimensions,
        score=score,
        summary=(
            f"Strong sponsor fit for {context.microprd_title or context.challenge_id}."
            if score >= 70
            else "Submission received — strengthen alignment with challenge success criteria."
        ),
        notes=notes or ["Sponsor fit uses challenge-specific success criteria (heuristic MVP)."],
    )
