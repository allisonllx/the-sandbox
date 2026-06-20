"""Enterprise reverse-sourcing radar — platform-wide top tier (not sponsor-scoped)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..ai_pm.models import ChallengeTrack


class EnterpriseRadarEntry(BaseModel):
    rank_label: str
    candidate_id: str
    track: ChallengeTrack
    execution_points: int
    platform_signal: str


class EnterpriseRadarResponse(BaseModel):
    ok: bool = True
    tier: str = "Top 1% platform-wide"
    entries: list[EnterpriseRadarEntry] = Field(default_factory=list)


_DEMO_ENTERPRISE = [
    EnterpriseRadarEntry(
        rank_label="Top 1%",
        candidate_id="A7F2",
        track=ChallengeTrack.technical,
        execution_points=118,
        platform_signal="Verified high performer · Technical track · Multiple blind-audition wins",
    ),
    EnterpriseRadarEntry(
        rank_label="Top 2%",
        candidate_id="B3K9",
        track=ChallengeTrack.product_feature,
        execution_points=104,
        platform_signal="Verified high performer · Product track · Strong DESIGN.md scores",
    ),
    EnterpriseRadarEntry(
        rank_label="Top 3%",
        candidate_id="C1M4",
        track=ChallengeTrack.technical,
        execution_points=96,
        platform_signal="Verified high performer · Technical track · Performance + resilience",
    ),
]


def get_enterprise_radar() -> EnterpriseRadarResponse:
    return EnterpriseRadarResponse(entries=list(_DEMO_ENTERPRISE))
