"""
LLM-powered domain obfuscation for novel industries.

Runs on the local vLLM tier by default (sensitive — column names stay on-prem).
Falls back to rule-based obfuscator when LLM is unavailable or output fails validation.
"""

from __future__ import annotations

import json
import logging
import os

from ..privacy_proxy.models import SanitizedMetadata
from .domain_obfuscator import DomainTransform, public_text_is_safe
from .llm_client import LLMClientProtocol, LLMTier, LLMUnavailableError, get_default_client
from .models import SensitivityTag
from backend.prompts.domain_obfuscator import DOMAIN_OBFUSCATOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _build_user_payload(
    metadata: SanitizedMetadata,
    source_label: str,
    title: str,
    brand_proxy: str,
) -> str:
    return json.dumps(
        {
            "title": title,
            "source_label": source_label,
            "brand_proxy_hint": brand_proxy,
            "field_names": [f.name for f in metadata.fields],
            "field_types": [
                {"name": f.name, "type": f.inferred_type, "nullable": f.nullable}
                for f in metadata.fields
            ],
            "format": str(metadata.format_detected),
            "approximate_row_scale": metadata.approximate_row_scale,
        },
        indent=2,
    )


def _validate_llm_transform(
    result: dict,
    field_names: list[str],
    *,
    title: str,
    source_label: str,
) -> DomainTransform | None:
    required = (
        "domain_proxy",
        "public_title",
        "public_narrative",
        "transform_rationale",
        "brand_proxy",
        "field_map",
    )
    if not all(k in result for k in required):
        logger.warning("LLM domain transform missing required keys.")
        return None

    field_map = {str(k): str(v) for k, v in (result.get("field_map") or {}).items()}
    if not field_map:
        return None

    for name in field_names:
        if name not in field_map:
            field_map[name] = f"field_{name.split('_')[-1][:8]}"

    public_blob = f"{result['public_title']} {result['public_narrative']}"
    if not public_text_is_safe(public_blob):
        logger.warning("LLM domain transform failed public_text_is_safe check.")
        return None

    for masked in field_map.values():
        if not public_text_is_safe(masked):
            logger.warning("LLM field_map value failed safety check: %s", masked)
            return None

    return DomainTransform(
        domain_proxy=str(result["domain_proxy"]),
        public_title=str(result["public_title"]),
        public_narrative=str(result["public_narrative"]),
        internal_intent=f"Internal (CTO only): {title} — {source_label}",
        transform_rationale=str(result["transform_rationale"])
        + " [LLM domain obfuscation]",
        brand_proxy=str(result["brand_proxy"]),
        field_map=field_map,
    )


def suggest_domain_transform(
    metadata: SanitizedMetadata,
    source_label: str,
    title: str,
    *,
    brand_proxy: str = "StealthCo",
    sensitivity_tag: SensitivityTag | None = None,
    client: LLMClientProtocol | None = None,
) -> DomainTransform | None:
    """
    Ask the local LLM to propose a domain mask for unknown industries.

    Returns None when LLM is unavailable or output fails validation.
    """
    if os.getenv("LLM_DOMAIN_OBFUSCATE", "1").lower() in ("0", "false", "no"):
        return None

    if client is None:
        client = get_default_client()

    field_names = [f.name for f in metadata.fields]
    user_msg = _build_user_payload(metadata, source_label, title, brand_proxy)

    try:
        result = client.chat(
            system=DOMAIN_OBFUSCATOR_SYSTEM_PROMPT,
            user=user_msg,
            temperature=0.2,
            tier=LLMTier.sensitive,
        )
    except (LLMUnavailableError, ValueError) as exc:
        logger.info("LLM domain obfuscation skipped: %s", exc)
        return None

    transform = _validate_llm_transform(
        result,
        field_names,
        title=title,
        source_label=source_label,
    )
    if transform:
        del sensitivity_tag  # reserved for future sensitivity-aware prompts
    return transform
