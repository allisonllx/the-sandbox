"""Sponsor-scoped match radar — candidates for ONE published challenge only."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..ai_pm.models import ChallengeTrack
from . import submission_store


class SponsorMatchEntry(BaseModel):
    rank: int
    candidate_id: str
    track: ChallengeTrack
    execution_points: int
    summary: str
    submitted_at: datetime | None = None


class SponsorMatchesResponse(BaseModel):
    ok: bool = True
    challenge_id: str
    challenge_title: str | None = None
    source: str = Field(description="live | demo | empty")
    entries: list[SponsorMatchEntry] = Field(default_factory=list)


# Demo stubs — only shown for the matching challenge_id (never cross-sponsor)
_DEMO_BY_CHALLENGE: dict[str, list[SponsorMatchEntry]] = {
    "demo-003": [
        SponsorMatchEntry(
            rank=1,
            candidate_id="CAND-8K2M",
            track=ChallengeTrack.technical,
            execution_points=92,
            summary="Strong query diagnosis; clear README trade-offs.",
        ),
        SponsorMatchEntry(
            rank=2,
            candidate_id="CAND-3P1L",
            track=ChallengeTrack.technical,
            execution_points=78,
            summary="Fixed index path; partial edge-case handling.",
        ),
    ],
    "demo-004": [
        SponsorMatchEntry(
            rank=1,
            candidate_id="CAND-B3K9",
            track=ChallengeTrack.product_feature,
            execution_points=88,
            summary="Solid DESIGN.md IA reasoning; responsive prototype.",
        ),
    ],
    "demo-005": [
        SponsorMatchEntry(
            rank=1,
            candidate_id="CAND-A7F2",
            track=ChallengeTrack.product_feature,
            execution_points=95,
            summary="Equipment discovery flow; strong mobile IA in DESIGN.md.",
        ),
    ],
    "demo-006": [
        SponsorMatchEntry(
            rank=1,
            candidate_id="CAND-C1M4",
            track=ChallengeTrack.technical,
            execution_points=86,
            summary="Traffic spike root-cause narrative; query improvements.",
        ),
    ],
}


def _anon_candidate_id(workspace_id: str | None, submission_id: str) -> str:
    seed = workspace_id or submission_id
    return f"CAND-{seed.replace('-', '')[:4].upper()}"


def get_sponsor_matches(challenge_id: str, *, challenge_title: str | None = None) -> SponsorMatchesResponse:
    """
    Return ranked candidates for a single sponsor challenge.

    Live submissions take precedence; demo stubs apply only when none exist.
    Never includes submissions from other challenges.
    """
    records = submission_store.list_for_challenge(challenge_id)
    scored = [r for r in records if r.scorecard and r.scorecard.get("execution_points") is not None]
    scored.sort(
        key=lambda r: int(r.scorecard.get("execution_points", 0)),  # type: ignore[union-attr]
        reverse=True,
    )

    if scored:
        entries = [
            SponsorMatchEntry(
                rank=i + 1,
                candidate_id=_anon_candidate_id(r.workspace_id, r.id),
                track=r.track,
                execution_points=int(r.scorecard.get("execution_points", 0)),  # type: ignore[union-attr]
                summary=str(r.scorecard.get("summary", "Submission assessed.")),
                submitted_at=r.submitted_at,
            )
            for i, r in enumerate(scored)
        ]
        return SponsorMatchesResponse(
            challenge_id=challenge_id,
            challenge_title=challenge_title,
            source="live",
            entries=entries,
        )

    demo = _DEMO_BY_CHALLENGE.get(challenge_id, [])
    return SponsorMatchesResponse(
        challenge_id=challenge_id,
        challenge_title=challenge_title,
        source="demo" if demo else "empty",
        entries=demo,
    )
