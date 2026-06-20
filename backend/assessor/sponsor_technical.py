"""Sponsor Fit — technical track (delegates to sponsor_fit module)."""

from __future__ import annotations

from ..sandbox.models import SubmissionRecord
from .models import ChallengeContext, ScoreLayer
from .sponsor_fit import assess_sponsor_fit


def assess_sponsor_technical(
    record: SubmissionRecord,
    context: ChallengeContext,
) -> ScoreLayer:
    return assess_sponsor_fit(record, context)
