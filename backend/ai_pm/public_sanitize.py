"""Sanitize internal backlog data for the public student boundary."""

from __future__ import annotations

import re

from ..sandbox.models import PublishedChallenge
from .domain_obfuscator import public_text_is_safe
from .models import ChallengeReward, CompanyTechProfile, MicroPRD, SensitivityTag

_FOCUS_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bvoucher\b", "credit redemption"),
    (r"\bmerchant\b", "inventory"),
    (r"\bdine[- ]?in\b", "reservation"),
    (r"\brestaurant\b", "location"),
    (r"\bfood\b", "catalog"),
    (r"\bcheckout\b", "redemption"),
    (r"\bdelivery\b", "fulfillment"),
    (r"\bgrab\b", "platform"),
)

_REDACTED_FOCUS = [
    "Discovery information architecture",
    "Mobile-first responsive layout",
    "End-to-end user flow completeness",
    "Design trade-off reasoning",
]


def sanitize_evaluation_focus(
    focus: list[str],
    tag: SensitivityTag | None,
) -> list[str]:
    """Map domain-specific evaluation bullets to generic equivalents."""
    if not focus:
        return []

    if tag == SensitivityTag.red:
        return list(_REDACTED_FOCUS[: min(len(focus), len(_REDACTED_FOCUS))])

    sanitized: list[str] = []
    for bullet in focus:
        result = bullet
        for pattern, replacement in _FOCUS_REPLACEMENTS:
            result = re.sub(pattern, replacement, result, flags=re.I)
        sanitized.append(result)
    return sanitized


def _scrub_text(text: str) -> str:
    result = text
    for pattern, replacement in _FOCUS_REPLACEMENTS:
        result = re.sub(pattern, replacement, result, flags=re.I)
    return result


def _strip_internal_brand(text: str, internal_brand: str | None) -> str:
    if not internal_brand or not text:
        return text
    return re.sub(rf"\b{re.escape(internal_brand)}\b", "the platform", text, flags=re.I)


def sanitize_microprd_for_public(
    microprd: MicroPRD,
    *,
    internal_brand: str | None = None,
) -> MicroPRD:
    """Strip internal brand and scrub forbidden tokens from student-visible Micro-PRD."""
    scrub = lambda t: _scrub_text(_strip_internal_brand(t, internal_brand))
    return microprd.model_copy(
        update={
            "brand_proxy": None,
            "title": scrub(microprd.title),
            "context": scrub(microprd.context),
            "definition_of_success": [scrub(s) for s in microprd.definition_of_success],
            "structural_constraints": [scrub(s) for s in microprd.structural_constraints],
            "sandbox_instructions": [scrub(s) for s in microprd.sandbox_instructions],
            "user_persona": scrub(microprd.user_persona) if microprd.user_persona else None,
            "problem_framing": scrub(microprd.problem_framing) if microprd.problem_framing else None,
            "design_considerations": [scrub(s) for s in microprd.design_considerations],
            "stack_guidance": [scrub(s) for s in microprd.stack_guidance],
            "deliverable_requirements": [scrub(s) for s in microprd.deliverable_requirements],
        }
    )


def reward_escrow_label(reward: ChallengeReward | None) -> str | None:
    if not reward or not reward.locked:
        return None
    if reward.reward_type.value == "cash_bounty":
        return "Funds verified & locked by platform (demo)"
    return "Interview pass guaranteed by platform (demo)"


def build_public_challenge(
    *,
    item_id: str,
    title: str,
    status: str,
    track,
    company_profile: CompanyTechProfile,
    deliverable_types,
    evaluation_focus: list[str],
    microprd: MicroPRD,
    dataset_ready: bool,
    uses_dataset: bool,
    starter_ready: bool,
    dataset_anomalies: list[str],
    reward: ChallengeReward | None,
    published_at,
    tag: SensitivityTag | None,
    internal_brand: str | None = None,
) -> PublishedChallenge:
    """Assemble a student-safe PublishedChallenge from internal backlog state."""
    public_microprd = sanitize_microprd_for_public(microprd, internal_brand=internal_brand)
    public_focus = sanitize_evaluation_focus(evaluation_focus, tag)

    return PublishedChallenge(
        id=item_id,
        title=public_microprd.title,
        status=status,
        track=track,
        company_profile=company_profile,
        deliverable_types=deliverable_types,
        evaluation_focus=public_focus,
        microprd=public_microprd,
        dataset_ready=dataset_ready,
        uses_dataset=uses_dataset,
        starter_ready=starter_ready,
        dataset_anomalies=dataset_anomalies,
        reward=reward,
        reward_escrow_label=reward_escrow_label(reward),
        published_at=published_at,
    )


def assert_public_challenge_safe(challenge: PublishedChallenge) -> None:
    """Test helper — raise AssertionError if public payload leaks forbidden tokens."""
    blob_parts = [
        challenge.title,
        challenge.microprd.context,
        " ".join(challenge.evaluation_focus),
        " ".join(challenge.microprd.definition_of_success),
    ]
    if challenge.microprd.user_persona:
        blob_parts.append(challenge.microprd.user_persona)
    if challenge.microprd.problem_framing:
        blob_parts.append(challenge.microprd.problem_framing)

    blob = " ".join(blob_parts)
    if not public_text_is_safe(blob):
        raise AssertionError(f"Public challenge contains forbidden tokens: {blob[:200]}")

    if challenge.microprd.brand_proxy:
        raise AssertionError("microprd.brand_proxy must be stripped for public API")
