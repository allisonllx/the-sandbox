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
        highlight="Challenge #demo-003 · Anonymous Series B · Technical track",
        challenge_id="demo-003",
    ),
    LeaderboardEntry(
        rank=2,
        display_name="Candidate B3K9",
        track=ChallengeTrack.product_feature,
        execution_points=104,
        highlight="Challenge #demo-005 · Anonymous Series A · Product track",
        challenge_id="demo-005",
    ),
    LeaderboardEntry(
        rank=3,
        display_name="Candidate C1M4",
        track=ChallengeTrack.technical,
        execution_points=96,
        highlight="Challenge #demo-006 · Anonymous Growth-stage · Technical track",
        challenge_id="demo-006",
    ),
]


def get_demo_leaderboard() -> LeaderboardResponse:
    return LeaderboardResponse(entries=list(_DEMO_ENTRIES))
