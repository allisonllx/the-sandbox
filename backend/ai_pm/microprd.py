"""
Generates track-aware Micro-PRDs from relaxed metadata using the LLM or fallbacks.
"""

from __future__ import annotations

import json
import logging
from .domain_obfuscator import DomainTransform
from .llm_client import LLMClientProtocol, LLMTier, LLMUnavailableError, get_default_client
from .models import ChallengeTrack, MicroPRD, RelaxedPreview
from .prompts.microprd import PRODUCT_SYSTEM_PROMPT, TECH_SYSTEM_PROMPT
from .relaxation import abstract_brand_text

logger = logging.getLogger(__name__)


def _build_user_message(
    preview: RelaxedPreview,
    metadata: SanitizedMetadata,
    brand_proxy: str,
    track: ChallengeTrack,
) -> str:
    payload = {
        "track": track.value,
        "brand_proxy": brand_proxy,
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


def _apply_brand(text: str, brand_proxy: str, *, enabled: bool = True) -> str:
    return abstract_brand_text(text, brand_proxy, enabled=enabled)


def _fallback_technical(challenge_id: str, title: str, brand_proxy: str) -> MicroPRD:
    from ..sandbox.starter_scaffold import platform_sandbox_instructions

    return MicroPRD(
        challenge_id=challenge_id,
        title=_apply_brand(title, brand_proxy),
        track=ChallengeTrack.technical,
        brand_proxy=brand_proxy,
        context=_apply_brand(
            "This challenge involves diagnosing and optimising a data pipeline "
            "that exhibits anomalous behaviour under load.",
            brand_proxy,
        ),
        definition_of_success=[
            "Identify the root cause of the performance degradation in the provided dataset.",
            "Implement a fix that reduces P99 query latency by at least 40%.",
            "Explain your diagnosis and trade-offs in code comments or README.md.",
            "All existing schema contracts must be preserved.",
        ],
        structural_constraints=[
            "Python 3.11+",
            "Edit the provided starter files only (main target: `src/queries.py`)",
            "Maximum memory usage: 512 MB during processing",
            "No new external dependencies without justification",
        ],
        sandbox_instructions=platform_sandbox_instructions(),
    )


def _fallback_product(
    challenge_id: str,
    title: str,
    brand_proxy: str,
    domain_transform: DomainTransform | None = None,
) -> MicroPRD:
    from ..sandbox.product_starter_scaffold import product_platform_instructions

    brand = brand_proxy or "EatsHub"
    if domain_transform and domain_transform.domain_proxy == "hyperlocal_equipment":
        return MicroPRD(
            challenge_id=challenge_id,
            title=domain_transform.public_title,
            track=ChallengeTrack.product_feature,
            brand_proxy=domain_transform.brand_proxy,
            context=domain_transform.public_narrative,
            definition_of_success=[
                "Responsive equipment locker discovery UI works from 375px to 1280px viewports.",
                "User can browse nearby inventory and add rentals to a cart with clear feedback.",
                "DESIGN.md explains persona, IA trade-offs, and stack choices without industry leak tokens.",
                "Credit redemption flow is stubbed with sensible empty/error states.",
            ],
            structural_constraints=[
                "Use the provided starter HTML/CSS/JS scaffold only — no backend required.",
                "Mock data from mock/inventory.json — do not call external APIs.",
                "DESIGN.md is required at submit time.",
            ],
            user_persona=(
                "Urban DIY enthusiast, 28–40, needs to rent power tools between meetings — "
                "mobile-first discovery with minimal checkout friction."
            ),
            problem_framing=(
                "How would you structure equipment locker discovery for mobile-first users? "
                "What trade-offs between map vs list view, and how would you justify them in DESIGN.md?"
            ),
            design_considerations=[
                "Mobile-first layout and touch targets",
                "Clear hierarchy: discovery → locker detail → cart → credit redeem",
                "Loading and empty states for inventory list",
                "Accessibility basics (labels, contrast, keyboard focus)",
            ],
            stack_guidance=[
                "Vanilla HTML/CSS/JS starter — extend in place",
                "Optional: explain in DESIGN.md if you would choose React/Next for production",
            ],
            deliverable_requirements=[
                "Completed DESIGN.md with persona and trade-offs",
                "Working prototype in starter files",
                "Optional Figma or deployed preview link at submit",
            ],
            sandbox_instructions=product_platform_instructions(equipment_mode=True),
        )

    return MicroPRD(
        challenge_id=challenge_id,
        title="Local Inventory Discovery Hub",
        track=ChallengeTrack.product_feature,
        brand_proxy=brand,
        context=(
            "A growth-stage marketplace startup needs to help users discover nearby inventory "
            "and complete checkout without leaving the app. The core team is focused on stability — "
            "this feature needs a thoughtful prototype and clear product reasoning."
        ),
        definition_of_success=[
            "Responsive merchant discovery UI works from 375px to 1280px viewports.",
            "User can browse merchants and add items to a cart with clear feedback.",
            "DESIGN.md explains persona, IA trade-offs, and stack choices.",
            "Checkout flow is stubbed or implemented with sensible empty/error states.",
        ],
        structural_constraints=[
            "Use the provided starter HTML/CSS/JS scaffold only — no backend required.",
            "Mock data from mock/merchants.json — do not call external APIs.",
            "DESIGN.md is required at submit time.",
        ],
        user_persona=(
            "Urban professional, 25–35, ordering lunch between meetings on mobile — "
            "needs fast discovery and minimal checkout friction."
        ),
        problem_framing=(
            "How would you structure the merchant discovery experience for mobile-first users? "
            "What trade-offs between map vs list view, and how would you justify them in DESIGN.md?"
        ),
        design_considerations=[
            "Mobile-first layout and touch targets",
            "Clear hierarchy: discovery → detail → cart → checkout",
            "Loading and empty states for merchant list",
            "Accessibility basics (labels, contrast, keyboard focus)",
        ],
        stack_guidance=[
            "Vanilla HTML/CSS/JS starter — extend in place",
            "Optional: explain in DESIGN.md if you would choose React/Next for production",
        ],
        deliverable_requirements=[
            "Completed DESIGN.md with persona and trade-offs",
            "Working prototype in starter files",
            "Optional Figma or deployed preview link at submit",
        ],
        sandbox_instructions=product_platform_instructions(),
    )


def generate(
    challenge_id: str,
    title: str,
    preview: RelaxedPreview,
    metadata: SanitizedMetadata,
    track: ChallengeTrack = ChallengeTrack.technical,
    brand_proxy: str = "DataStream",
    abstract_brand: bool = True,
    domain_transform: "DomainTransform | None" = None,
    client: LLMClientProtocol | None = None,
) -> MicroPRD:
    if track == ChallengeTrack.product_feature:
        fallback = lambda: _fallback_product(challenge_id, title, brand_proxy, domain_transform)
        system = PRODUCT_SYSTEM_PROMPT
    else:
        fallback = lambda: _fallback_technical(challenge_id, title, brand_proxy)
        system = TECH_SYSTEM_PROMPT

    if domain_transform and track == ChallengeTrack.product_feature:
        return _finalize_platform_instructions(
            _fallback_product(challenge_id, title, brand_proxy, domain_transform)
        )

    if client is None:
        client = get_default_client()

    user_msg = _build_user_message(preview, metadata, brand_proxy, track)

    try:
        result = client.chat(system=system, user=user_msg, temperature=0.4, tier=LLMTier.sensitive)
        base = {
            "challenge_id": challenge_id,
            "title": _apply_brand(str(result.get("title", title)), brand_proxy, enabled=abstract_brand),
            "track": track,
            "brand_proxy": brand_proxy,
            "context": _apply_brand(str(result["context"]), brand_proxy, enabled=abstract_brand),
            "definition_of_success": list(result["definition_of_success"]),
            "structural_constraints": list(result["structural_constraints"]),
            "sandbox_instructions": list(result.get("sandbox_instructions", [])),
        }
        if track == ChallengeTrack.product_feature:
            base.update(
                {
                    "user_persona": str(result.get("user_persona", "")),
                    "problem_framing": str(result.get("problem_framing", "")),
                    "design_considerations": list(result.get("design_considerations", [])),
                    "stack_guidance": list(result.get("stack_guidance", [])),
                    "deliverable_requirements": list(result.get("deliverable_requirements", [])),
                }
            )
        prd = MicroPRD(**base)
    except LLMUnavailableError as exc:
        logger.warning("LLM unavailable for Micro-PRD: %s", exc)
        prd = fallback()
    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("LLM Micro-PRD malformed (%s), using fallback.", exc)
        prd = fallback()

    return _finalize_platform_instructions(prd)


def _finalize_platform_instructions(prd: MicroPRD) -> MicroPRD:
    if prd.track == ChallengeTrack.product_feature:
        from ..sandbox.product_starter_scaffold import product_platform_instructions

        equipment = "equipment" in prd.context.lower() or "locker" in prd.title.lower()
        return prd.model_copy(
            update={"sandbox_instructions": product_platform_instructions(equipment_mode=equipment)}
        )
    from ..sandbox.starter_scaffold import platform_sandbox_instructions

    return prd.model_copy(update={"sandbox_instructions": platform_sandbox_instructions()})
