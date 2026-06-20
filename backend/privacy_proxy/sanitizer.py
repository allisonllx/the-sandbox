"""
Main orchestrator for the Local Privacy Proxy pipeline.

Pipeline stages (all local, no network I/O):

  1. Zero-Leak Guardrail  — hard-block chunks containing prohibited keywords
  2. PII Scrubbing        — regex-based masking of emails, phones, keys, JWTs, etc.
  3. NER Pass             — count named entities (PERSON, ORG, GPE) using local spaCy
  4. Structural Extraction — parse scrubbed text into field/type/frequency metadata

The function `sanitize` is the ONLY export intended for use by API routes
or upstream callers. It accepts raw text and returns a `SanitizedMetadata`
object — which contains zero raw content.
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

from .models import (
    NEREntityCount,
    PIIDetection,
    SanitizedMetadata,
)
from .ner_engine import count_entities
from .pii_patterns import scrub
from .structural_extractor import InputFormat, extract

logger = logging.getLogger(__name__)

# Keywords that cause an entire chunk to be dropped (not just masked).
# These represent patterns so sensitive that even their structural context
# should not leave the local boundary.
_DEFAULT_BLOCK_KEYWORDS: list[re.Pattern[str]] = [
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
    re.compile(r"\bprivate[_\s]key\b", re.IGNORECASE),
    re.compile(r"\bssh[_\s]?key\b", re.IGNORECASE),
    re.compile(r"\bcredential\b", re.IGNORECASE),
    re.compile(r"\bseed[_\s]?phrase\b", re.IGNORECASE),
    re.compile(r"\bmnemonic\b", re.IGNORECASE),
]

_CHUNK_SEPARATOR = re.compile(r"\n{2,}")


def _compile_extra_keywords(keywords: Sequence[str]) -> list[re.Pattern[str]]:
    return [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]


def _apply_guardrail(
    text: str,
    extra_patterns: list[re.Pattern[str]],
) -> tuple[str, int]:
    """
    Split text into chunks (paragraph / blank-line separated) and drop any
    chunk that matches a guardrail keyword.

    Returns (filtered_text, blocked_count).
    """
    all_patterns = _DEFAULT_BLOCK_KEYWORDS + extra_patterns
    chunks = _CHUNK_SEPARATOR.split(text)
    kept: list[str] = []
    blocked = 0

    for chunk in chunks:
        if any(p.search(chunk) for p in all_patterns):
            blocked += 1
            logger.debug("Guardrail blocked a chunk (%d chars).", len(chunk))
        else:
            kept.append(chunk)

    return "\n\n".join(kept), blocked


def sanitize(
    raw_text: str,
    fmt: InputFormat = InputFormat.auto,
    guardrail_keywords: Sequence[str] = (),
) -> SanitizedMetadata:
    """
    Run the full local privacy pipeline on *raw_text*.

    Args:
        raw_text:           Untreated content from the startup's ingest channel.
        fmt:                Hint about the input format; defaults to auto-detect.
        guardrail_keywords: Extra keywords that should trigger the hard-block.

    Returns:
        SanitizedMetadata — structural descriptors only, no raw content.

    This function MUST NOT make any network calls. It MUST NOT return any
    string that was present in raw_text (only structural metadata).
    """
    notes: list[str] = []

    if not raw_text or not raw_text.strip():
        return SanitizedMetadata(
            format_detected=InputFormat.text,
            processing_notes=["Input was empty."],
        )

    # --- Stage 1: Zero-Leak Guardrail ---
    extra_patterns = _compile_extra_keywords(guardrail_keywords)
    filtered_text, blocked_count = _apply_guardrail(raw_text, extra_patterns)

    if blocked_count:
        notes.append(f"{blocked_count} chunk(s) blocked by zero-leak guardrail.")

    if not filtered_text.strip():
        return SanitizedMetadata(
            format_detected=InputFormat.text,
            blocked_chunk_count=blocked_count,
            processing_notes=notes + ["All content was blocked by the guardrail."],
        )

    # --- Stage 2: PII Scrubbing ---
    scrubbed_text, pii_counts = scrub(filtered_text)

    pii_detections = [
        PIIDetection(pii_type=pii_type, count=count)
        for pii_type, count in sorted(pii_counts.items())
    ]

    if pii_detections:
        total = sum(d.count for d in pii_detections)
        notes.append(f"{total} PII token(s) masked across {len(pii_detections)} type(s).")

    # --- Stage 3: NER Pass ---
    entity_counts = count_entities(scrubbed_text)
    ner_entity_counts = [
        NEREntityCount(entity_label=label, count=count)
        for label, count in sorted(entity_counts.items())
    ]

    if not entity_counts:
        notes.append("NER pass skipped or returned no entities (model may not be installed).")

    # --- Stage 4: Structural Extraction ---
    struct = extract(scrubbed_text, fmt)

    if "error" in struct:
        notes.append(f"Structural extraction warning: {struct['error']}")

    return SanitizedMetadata(
        format_detected=struct.get("format", InputFormat.text),
        fields=struct.get("fields", []),
        nested_paths=struct.get("nested_paths", []),
        approximate_row_scale=struct.get("row_scale"),
        event_type_frequencies=struct.get("event_frequencies", []),
        pii_detections=pii_detections,
        ner_entity_counts=ner_entity_counts,
        blocked_chunk_count=blocked_count,
        processing_notes=notes,
    )
