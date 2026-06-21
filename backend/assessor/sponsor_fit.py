"""
Sponsor Fit assessor — LLM taste/criteria alignment with heuristic fallback.

Receives sanitized public challenge context + student submission files.
Never receives brand_proxy, source_label, or raw corporate metadata.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ..ai_pm.llm_client import LLMClientProtocol, LLMTier, LLMUnavailableError, get_default_client
from ..ai_pm.models import ChallengeTrack
from backend.prompts.sponsor_fit import (
    SPONSOR_FIT_PRODUCT_SYSTEM_PROMPT,
    SPONSOR_FIT_TECHNICAL_SYSTEM_PROMPT,
)
from ..sandbox.models import SubmissionRecord
from .models import ChallengeContext, ScoreLayer

logger = logging.getLogger(__name__)

_MAX_CHARS_PER_FILE = 2500
_MAX_FILES = 10

_TECHNICAL_DIMENSIONS = (
    "criteria_alignment",
    "architectural_taste",
    "edge_case_handling",
    "tradeoff_reasoning",
)

_PRODUCT_DIMENSIONS = (
    "persona_fit",
    "problem_framing",
    "ux_judgment",
    "communication",
)


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def _clamp_score(value: Any) -> int:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, n))


def _normalize_dimensions(raw: dict[str, Any], expected: tuple[str, ...]) -> dict[str, int]:
    dims: dict[str, int] = {}
    for key in expected:
        dims[key] = _clamp_score(raw.get(key, 0))
    return dims


def _build_challenge_payload(context: ChallengeContext) -> dict[str, Any]:
    return {
        "challenge_id": context.challenge_id,
        "track": context.track.value if hasattr(context.track, "value") else str(context.track),
        "title": context.microprd_title,
        "context": context.microprd_context,
        "definition_of_success": context.definition_of_success,
        "evaluation_focus": context.evaluation_focus,
        "structural_constraints": context.structural_constraints,
        "user_persona": context.user_persona,
        "problem_framing": context.problem_framing,
    }


def _build_submission_payload(record: SubmissionRecord) -> dict[str, Any]:
    files_out: dict[str, str] = {}
    for i, (path, content) in enumerate(sorted(record.files.items())):
        if i >= _MAX_FILES:
            break
        files_out[path] = content[:_MAX_CHARS_PER_FILE]
        if len(content) > _MAX_CHARS_PER_FILE:
            files_out[path] += "\n... [truncated]"

    return {
        "file_paths": list(files_out.keys()),
        "files": files_out,
        "links": dict(record.links or {}),
        "language": record.language,
    }


def _heuristic_technical(record: SubmissionRecord, context: ChallengeContext) -> ScoreLayer:
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

    dimensions = {
        "criteria_alignment": criteria_alignment,
        "architectural_taste": min(100, 35 + line_count // 3 + (15 if has_readme else 0)),
        "edge_case_handling": min(
            100, 30 + (20 if "except" in combined_text or "try:" in combined_text else 0)
        ),
        "tradeoff_reasoning": min(
            100, 25 + (25 if has_readme else 0) + (15 if "trade" in combined_text else 0)
        ),
    }
    score = int(round(sum(dimensions.values()) / len(dimensions)))

    for focus in context.evaluation_focus:
        notes.append(f"Evaluated against focus: {focus}")

    return ScoreLayer(
        dimensions=dimensions,
        score=score,
        summary=(
            f"Strong sponsor fit for {context.microprd_title or context.challenge_id}."
            if score >= 70
            else "Submission received — strengthen alignment with challenge success criteria."
        ),
        notes=notes + ["Sponsor fit: heuristic fallback (LLM unavailable)."],
    )


def _heuristic_product(record: SubmissionRecord, context: ChallengeContext) -> ScoreLayer:
    notes: list[str] = []
    files = record.files
    links = record.links or {}
    design = files.get("DESIGN.md", "")
    has_design = bool(design.strip())
    design_words = _word_count(design) if has_design else 0
    design_lower = design.lower()
    js_content = files.get("src/app.js", "")

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
        "ux_judgment": min(100, ux_judgment),
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
        notes=notes + ["Sponsor fit: heuristic fallback (LLM unavailable)."],
    )


def _llm_sponsor_fit(
    record: SubmissionRecord,
    context: ChallengeContext,
    client: LLMClientProtocol,
) -> ScoreLayer:
    is_product = context.track == ChallengeTrack.product_feature
    expected = _PRODUCT_DIMENSIONS if is_product else _TECHNICAL_DIMENSIONS
    system = SPONSOR_FIT_PRODUCT_SYSTEM_PROMPT if is_product else SPONSOR_FIT_TECHNICAL_SYSTEM_PROMPT

    user_payload = {
        "challenge": _build_challenge_payload(context),
        "submission": _build_submission_payload(record),
    }
    user = json.dumps(user_payload, indent=2)

    result = client.chat(system=system, user=user, temperature=0.2, tier=LLMTier.sensitive)
    raw_dims = result.get("dimensions") or {}
    dimensions = _normalize_dimensions(raw_dims, expected)
    score = int(round(sum(dimensions.values()) / len(dimensions)))

    summary = str(result.get("summary") or "Sponsor fit assessed.")
    notes = [str(n) for n in (result.get("notes") or [])]
    notes.append("Sponsor fit: LLM evaluation (blind audition — no sponsor identity).")

    return ScoreLayer(
        dimensions=dimensions,
        score=score,
        summary=summary,
        notes=notes,
    )


def assess_sponsor_fit(
    record: SubmissionRecord,
    context: ChallengeContext,
    *,
    llm_client: LLMClientProtocol | None = None,
) -> ScoreLayer:
    """
    Evaluate challenge-specific sponsor fit.

    Uses LLM when available; falls back to deterministic heuristics offline.
    """
    client = llm_client if llm_client is not None else get_default_client()

    try:
        return _llm_sponsor_fit(record, context, client)
    except (LLMUnavailableError, ValueError) as exc:
        logger.info("Sponsor fit LLM unavailable, using heuristic: %s", exc)
        if context.track == ChallengeTrack.product_feature:
            return _heuristic_product(record, context)
        return _heuristic_technical(record, context)
