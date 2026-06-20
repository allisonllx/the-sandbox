"""Product Feature track assessor — preflight + DESIGN.md rubric (MVP, mostly deterministic)."""

from __future__ import annotations

import re

from ..sandbox.models import SubmissionRecord

_VALID_LINK_KEYS = frozenset({"figma", "deployment", "github"})


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def assess_product_submission(record: SubmissionRecord) -> dict:
    notes: list[str] = []
    files = record.files
    links = record.links or {}

    design = files.get("DESIGN.md", "")
    has_design = bool(design.strip())
    design_words = _word_count(design) if has_design else 0

    has_html = any(p.endswith(".html") for p in files)
    has_js = any(p.endswith(".js") for p in files)
    has_css = any(p.endswith(".css") for p in files)

    for key in links:
        if key not in _VALID_LINK_KEYS:
            notes.append(f"Ignored unknown link key: {key}")

    product_thinking = 30
    if has_design:
        product_thinking += min(40, design_words // 3)
        if "persona" in design.lower():
            product_thinking += 10
        if "trade-off" in design.lower() or "trade off" in design.lower():
            product_thinking += 10
    else:
        notes.append("DESIGN.md missing or empty — required for Product Feature track.")

    ux_ia = 25
    if has_html and has_js:
        ux_ia += 25
    if has_css:
        ux_ia += 15
    if "responsive" in design.lower() or "@media" in files.get("src/styles.css", ""):
        ux_ia += 15

    implementation = 20
    if has_html and has_js:
        implementation += 30
    js_content = files.get("src/app.js", "")
    if "cart" in js_content.lower() and "merchant" in js_content.lower():
        implementation += 20

    communication = min(100, 20 + design_words // 2) if has_design else 15

    dimensions = {
        "Product Thinking": min(100, product_thinking),
        "UX & IA": min(100, ux_ia),
        "Implementation Quality": min(100, implementation),
        "Communication": min(100, communication),
    }

    if links.get("figma"):
        notes.append("Figma link recorded for reviewer.")
    if links.get("deployment"):
        notes.append("Deployment link recorded for reviewer.")

    summary = (
        "Strong product submission."
        if min(dimensions.values()) >= 60
        else "Submission received — strengthen DESIGN.md trade-offs and prototype completeness."
    )

    return {
        "track": "product_feature",
        "dimensions": dimensions,
        "summary": summary,
        "notes": notes,
    }
