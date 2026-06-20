"""Pluggable assessor registry — one plugin per innovation track."""

from __future__ import annotations

from ..ai_pm.models import ChallengeTrack
from ..sandbox.models import SubmissionRecord
from .product_assessor import assess_product_submission
from .technical_assessor import assess_technical_submission


def assess_submission(record: SubmissionRecord, challenge_track: ChallengeTrack) -> dict:
    if challenge_track == ChallengeTrack.product_feature:
        return assess_product_submission(record)
    return assess_technical_submission(record)
