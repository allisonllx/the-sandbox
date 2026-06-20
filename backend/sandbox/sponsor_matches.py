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
    sponsor_fit_score: int
    platform_score: int | None = None
    execution_points: int = Field(
        description="Platform Execution Points — shown for context, not primary sort key",
    )
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
            sponsor_fit_score=92,
            platform_score=78,
            execution_points=94,
            summary="Strong query diagnosis; clear README trade-offs.",
        ),
        SponsorMatchEntry(
            rank=2,
            candidate_id="CAND-3P1L",
            track=ChallengeTrack.technical,
            sponsor_fit_score=78,
            platform_score=65,
            execution_points=78,
            summary="Fixed index path; partial edge-case handling.",
        ),
    ],
    "demo-004": [
        SponsorMatchEntry(
            rank=1,
            candidate_id="CAND-B3K9",
            track=ChallengeTrack.product_feature,
            sponsor_fit_score=88,
            platform_score=72,
            execution_points=86,
            summary="Solid DESIGN.md IA reasoning; responsive prototype.",
        ),
    ],
    "demo-005": [
        SponsorMatchEntry(
            rank=1,
            candidate_id="CAND-A7F2",
            track=ChallengeTrack.product_feature,
            sponsor_fit_score=95,
            platform_score=80,
            execution_points=96,
            summary="Equipment discovery flow; strong mobile IA in DESIGN.md.",
        ),
    ],
    "demo-006": [
        SponsorMatchEntry(
            rank=1,
            candidate_id="CAND-C1M4",
            track=ChallengeTrack.technical,
            sponsor_fit_score=86,
            platform_score=74,
            execution_points=89,
            summary="Traffic spike root-cause narrative; query improvements.",
        ),
    ],
}


def _anon_candidate_id(workspace_id: str | None, submission_id: str) -> str:
    seed = workspace_id or submission_id
    return f"CAND-{seed.replace('-', '')[:4].upper()}"


def _scorecard_sponsor_fit(scorecard: dict) -> int:
    if scorecard.get("sponsor_fit_score") is not None:
        return int(scorecard["sponsor_fit_score"])
    sponsor = scorecard.get("sponsor") or {}
    if sponsor.get("score") is not None:
        return int(sponsor["score"])
    return int(scorecard.get("execution_points", 0))


def _scorecard_platform(scorecard: dict) -> int:
    if scorecard.get("platform_score") is not None:
        return int(scorecard["platform_score"])
    platform = scorecard.get("platform") or {}
    if platform.get("score") is not None:
        return int(platform["score"])
    return int(scorecard.get("execution_points", 0))


def get_sponsor_matches(challenge_id: str, *, challenge_title: str | None = None) -> SponsorMatchesResponse:
    """
    Return ranked candidates for a single sponsor challenge.

    Sorted by sponsor_fit_score (challenge-specific fit). Live submissions take
    precedence; demo stubs apply only when none exist.
    """
    records = submission_store.list_for_challenge(challenge_id)
    scored = [r for r in records if r.scorecard]
    scored.sort(
        key=lambda r: _scorecard_sponsor_fit(r.scorecard),  # type: ignore[arg-type]
        reverse=True,
    )

    if scored:
        entries = [
            SponsorMatchEntry(
                rank=i + 1,
                candidate_id=_anon_candidate_id(r.workspace_id, r.id),
                track=r.track,
                sponsor_fit_score=_scorecard_sponsor_fit(r.scorecard),  # type: ignore[arg-type]
                platform_score=_scorecard_platform(r.scorecard),  # type: ignore[arg-type]
                execution_points=int(r.scorecard.get("execution_points", 0)),  # type: ignore[union-attr]
                summary=str(
                    (r.scorecard.get("sponsor") or {}).get("summary")
                    or r.scorecard.get("summary", "Submission assessed.")
                ),
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
