"""
Generates a Micro-PRD from relaxed metadata using the LLM.

The LLM receives ONLY the relaxed (de-risked) structural metadata —
field names are already synthesized/abstracted by the relaxation layer.

Falls back to a template-based Micro-PRD when the LLM is unavailable.
"""

from __future__ import annotations

import json
import logging
import uuid

from ..privacy_proxy.models import SanitizedMetadata
from .llm_client import LLMClientProtocol, LLMUnavailableError, get_default_client
from .models import MicroPRD, RelaxedPreview

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a technical challenge designer for a developer talent platform.

You receive anonymized structural metadata for a real engineering problem from a \
growth-stage startup. Your job is to turn it into a public Micro-PRD that a \
university student can solve.

The Micro-PRD must have exactly four sections:

1. context: 2-3 sentences describing the class of problem (performance, reliability, \
   data quality, etc.) without revealing the company or its domain.

2. definition_of_success: list of 3-5 concrete, measurable outcomes a good solution \
   must achieve.

3. structural_constraints: list of technical constraints (e.g. stack, memory limit, \
   time complexity, no new dependencies).

4. sandbox_instructions: numbered list of steps for the student to set up and run \
   the challenge environment.

Respond with ONLY a JSON object:
{
  "title": "<challenge title, ≤ 10 words>",
  "context": "<paragraph>",
  "definition_of_success": ["<bullet>", ...],
  "structural_constraints": ["<constraint>", ...],
  "sandbox_instructions": ["<step>", ...]
}
"""


def _build_user_message(
    preview: RelaxedPreview,
    metadata: SanitizedMetadata,
) -> str:
    payload = {
        "relaxed_fields": preview.relaxed_fields,
        "approximate_row_scale": preview.relaxed_row_scale,
        "event_type_frequencies": [
            {"event_type": e.event_type, "count": e.count}
            for e in metadata.event_type_frequencies
        ],
        "format": str(metadata.format_detected),
        "nested_paths": metadata.nested_paths,
    }
    return json.dumps(payload, indent=2)


def _fallback_microprd(challenge_id: str, title: str) -> MicroPRD:
    return MicroPRD(
        challenge_id=challenge_id,
        title=title,
        context=(
            "This challenge involves diagnosing and optimising a data pipeline "
            "that exhibits anomalous behaviour under load. The system processes "
            "structured event streams and must maintain low-latency query performance."
        ),
        definition_of_success=[
            "Identify the root cause of the performance degradation in the provided dataset.",
            "Implement a fix that reduces P99 query latency by at least 40%.",
            "Write a short explanation of your diagnosis and the trade-offs of your approach.",
            "All existing schema contracts must be preserved.",
        ],
        structural_constraints=[
            "Python 3.11+ or TypeScript/Node 20+",
            "Maximum memory usage: 512 MB during processing",
            "No new external dependencies without justification",
            "Must process the full synthetic dataset in under 30 seconds on a standard laptop",
        ],
        sandbox_instructions=[
            "Download the provided synthetic dataset archive.",
            "Extract to `./data/` in the challenge directory.",
            "Install dependencies: `pip install -r requirements.txt`",
            "Run the baseline benchmark: `python benchmark.py` — note the P99 latency.",
            "Implement your solution in `solution.py`.",
            "Re-run `python benchmark.py` to measure your improvement.",
            "Submit `solution.py` and a `NOTES.md` explaining your approach.",
        ],
    )


def generate(
    challenge_id: str,
    title: str,
    preview: RelaxedPreview,
    metadata: SanitizedMetadata,
    client: LLMClientProtocol | None = None,
) -> MicroPRD:
    """
    Generate a Micro-PRD for the given challenge.

    Args:
        challenge_id: Stable identifier for this backlog item.
        title:        Suggested challenge title from the scorer.
        preview:      Relaxed metadata preview (uses relaxed field names).
        metadata:     Original sanitized metadata (for event frequencies etc).
        client:       LLM client; defaults to module singleton.

    Returns:
        A fully populated MicroPRD.
    """
    if client is None:
        client = get_default_client()

    user_msg = _build_user_message(preview, metadata)

    try:
        result = client.chat(system=_SYSTEM_PROMPT, user=user_msg, temperature=0.4)
        return MicroPRD(
            challenge_id=challenge_id,
            title=result.get("title", title),
            context=str(result["context"]),
            definition_of_success=list(result["definition_of_success"]),
            structural_constraints=list(result["structural_constraints"]),
            sandbox_instructions=list(result["sandbox_instructions"]),
        )
    except LLMUnavailableError as exc:
        logger.warning("LLM unavailable for Micro-PRD generation: %s", exc)
        return _fallback_microprd(challenge_id, title)
    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("LLM response malformed for Micro-PRD (%s), using fallback.", exc)
        return _fallback_microprd(challenge_id, title)
