"""Platform Signal — product track (structural rubric, no challenge-specific narrative)."""

from __future__ import annotations

import re

from ..sandbox.models import SubmissionRecord
from .models import ScoreLayer


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def assess_platform_product(record: SubmissionRecord) -> ScoreLayer:
    """Track-standard deliverable checks — comparable across product challenges."""
    notes: list[str] = []
    files = record.files

    design = files.get("DESIGN.md", "")
    has_design = bool(design.strip())
    design_words = _word_count(design) if has_design else 0

    has_html = any(p.endswith(".html") for p in files)
    has_js = any(p.endswith(".js") for p in files)
    has_css = any(p.endswith(".css") for p in files)

    deliverable_completeness = 25
    if has_html:
        deliverable_completeness += 25
    if has_js:
        deliverable_completeness += 25
    if has_css:
        deliverable_completeness += 15

    design_doc_structure = 20
    if has_design:
        design_doc_structure += min(40, design_words // 4)
        lower = design.lower()
        if any(h in lower for h in ("# ", "## ", "### ")):
            design_doc_structure += 10
    else:
        notes.append("DESIGN.md missing — limits platform product signal.")

    prototype_runnable = 30
    if has_html and has_js:
        prototype_runnable += 40
    elif has_html:
        prototype_runnable += 20

    css_content = files.get("src/styles.css", "")
    accessibility_baseline = 25
    if "@media" in css_content or "responsive" in design.lower():
        accessibility_baseline += 25
    if has_css:
        accessibility_baseline += 15

    dimensions = {
        "deliverable_completeness": min(100, deliverable_completeness),
        "design_doc_structure": min(100, design_doc_structure),
        "prototype_runnable": min(100, prototype_runnable),
        "accessibility_baseline": min(100, accessibility_baseline),
    }
    score = int(round(sum(dimensions.values()) / len(dimensions)))

    return ScoreLayer(
        dimensions=dimensions,
        score=score,
        summary="Platform product signal — structural deliverable rubric.",
        notes=notes,
    )
