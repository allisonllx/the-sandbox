"""Demo leaderboard seed data for hackathon stub."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..ai_pm.models import ChallengeTrack


class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    track: ChallengeTrack
    execution_points: int
    highlight: str
    challenge_id: str | None = None


class LeaderboardResponse(BaseModel):
    ok: bool = True
    entries: list[LeaderboardEntry] = Field(default_factory=list)


_DEMO_ENTRIES = [
    LeaderboardEntry(
        rank=1,
        display_name="Candidate A7F2",
        track=ChallengeTrack.technical,
        execution_points=118,
        highlight="Technical track · Blind-audition sprint",
        challenge_id=None,
    ),
    LeaderboardEntry(
        rank=2,
        display_name="Candidate B3K9",
        track=ChallengeTrack.product_feature,
        execution_points=104,
        highlight="Product track · Prototype + DESIGN.md",
        challenge_id=None,
    ),
    LeaderboardEntry(
        rank=3,
        display_name="Candidate C1M4",
        track=ChallengeTrack.technical,
        execution_points=96,
        highlight="Technical track · Debugging + optimization",
        challenge_id=None,
    ),
]


def get_demo_leaderboard() -> LeaderboardResponse:
    return LeaderboardResponse(entries=list(_DEMO_ENTRIES))
