"""Pluggable assessor registry — one plugin per innovation track."""

from __future__ import annotations

from ..ai_pm.models import ChallengeReward, ChallengeTrack, RewardType
from ..sandbox.models import SubmissionRecord
from .product_assessor import assess_product_submission
from .technical_assessor import assess_technical_submission


def _execution_points(scorecard: dict) -> int:
    dims = scorecard.get("dimensions", {})
    if not dims:
        return 0
    avg = sum(dims.values()) / len(dims)
    return int(round(avg * 1.2))


def assess_submission(
    record: SubmissionRecord,
    challenge_track: ChallengeTrack,
    reward: ChallengeReward | None = None,
) -> dict:
    if challenge_track == ChallengeTrack.product_feature:
        scorecard = assess_product_submission(record)
    else:
        scorecard = assess_technical_submission(record)

    scorecard["execution_points"] = _execution_points(scorecard)

    if reward and reward.reward_type == RewardType.interview_pass:
        dims = scorecard.get("dimensions", {})
        avg = sum(dims.values()) / len(dims) if dims else 0
        benchmark = reward.interview_benchmark
        earned = avg >= benchmark
        scorecard["interview_pass_earned"] = earned
        scorecard["interview_benchmark"] = benchmark
        if earned:
            scorecard["notes"] = list(scorecard.get("notes", [])) + [
                f"Interview Pass earned (demo) — score {avg:.0f} ≥ benchmark {benchmark}."
            ]

    return scorecard
