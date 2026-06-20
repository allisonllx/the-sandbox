"""Pluggable assessor registry — dual-layer platform signal + sponsor fit."""

from __future__ import annotations

from ..ai_pm.models import ChallengeReward, ChallengeTrack
from ..sandbox.models import SubmissionRecord
from .models import ChallengeContext, build_dual_layer_scorecard, challenge_context_from_item
from .platform_product import assess_platform_product
from .platform_technical import assess_platform_technical
from .sponsor_product import assess_sponsor_product
from .sponsor_technical import assess_sponsor_technical


def assess_submission(
    record: SubmissionRecord,
    challenge_track: ChallengeTrack,
    reward: ChallengeReward | None = None,
    *,
    challenge_context: ChallengeContext | None = None,
    challenge_item=None,
) -> dict:
    """
    Assess a submission with dual layers:
    - platform: track-standard, feeds Execution Points (global rank)
    - sponsor: challenge-specific, feeds Match Radar only
    """
    if challenge_context is None and challenge_item is not None:
        challenge_context = challenge_context_from_item(challenge_item)
    if challenge_context is None:
        challenge_context = ChallengeContext(
            challenge_id=record.challenge_id,
            track=challenge_track,
        )

    if challenge_track == ChallengeTrack.product_feature:
        platform = assess_platform_product(record)
        sponsor = assess_sponsor_product(record, challenge_context)
        track_label = "product_feature"
    else:
        dataset_path = getattr(challenge_item, "dataset_path", None) if challenge_item else None
        platform = assess_platform_technical(record, dataset_path=dataset_path)
        sponsor = assess_sponsor_technical(record, challenge_context)
        track_label = "technical"

    return build_dual_layer_scorecard(
        track=track_label,
        platform=platform,
        sponsor=sponsor,
        reward=reward,
    )
