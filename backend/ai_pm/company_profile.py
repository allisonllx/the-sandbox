"""Generate standardized Company Tech Profiles for blind-audition student surfaces."""

from __future__ import annotations

from typing import Literal

from .models import BacklogItem, ChallengeReward, ChallengeTrack, CompanyTechProfile, SensitivityTag

# Pre-seeded profiles for deterministic judge demos
_DEMO_PROFILES: dict[str, CompanyTechProfile] = {
    "demo-003": CompanyTechProfile(
        stage="Series B",
        team_size_range="51-200",
        tech_stack=["Go", "React", "AWS", "Postgres"],
        industry_broad="Fintech Infrastructure",
        verification_status="verified",
        verification_label="Platform-verified sponsor",
    ),
    "demo-004": CompanyTechProfile(
        stage="Series A",
        team_size_range="11-50",
        tech_stack=["TypeScript", "React Native", "Node.js", "PostgreSQL"],
        industry_broad="Consumer Marketplace",
        verification_status="pending",
        verification_label="Platform-verified sponsor",
    ),
    "demo-005": CompanyTechProfile(
        stage="Series A",
        team_size_range="11-50",
        tech_stack=["Go", "React", "AWS", "Postgres"],
        industry_broad=None,
        verification_status="verified",
        verification_label="Platform-verified sponsor",
    ),
    "demo-006": CompanyTechProfile(
        stage="Growth",
        team_size_range="201-500",
        tech_stack=["Java", "Kotlin", "GCP", "Spanner"],
        industry_broad="Platform Engineering",
        verification_status="verified",
        verification_label="Platform-verified sponsor",
    ),
    "demo-001": CompanyTechProfile(
        stage="Series B",
        team_size_range="51-200",
        tech_stack=["Python", "PostgreSQL", "Datadog", "Kubernetes"],
        industry_broad="Data Infrastructure",
        verification_status="pending",
        verification_label="Platform-verified sponsor",
    ),
    "demo-002": CompanyTechProfile(
        stage="Series A",
        team_size_range="11-50",
        tech_stack=["Ruby", "Sidekiq", "Stripe API", "Redis"],
        industry_broad="Fintech Infrastructure",
        verification_status="pending",
        verification_label="Platform-verified sponsor",
    ),
}

_FINTECH_FIELDS = frozenset(
    {"transaction_id", "retry_count", "gateway_response_code", "amount_cents", "processor_name"}
)
_PRODUCT_FIELDS = frozenset(
    {"feature_request", "merchant_id", "discovery_query", "screen_name", "ux_friction"}
)


def _infer_industry(item: BacklogItem) -> str | None:
    if item.tag == SensitivityTag.red:
        return None

    field_names = {f.name for f in item.metadata.fields}
    track = item.track or item.suggested_track

    if field_names & _FINTECH_FIELDS:
        return "Fintech Infrastructure"
    if field_names & _PRODUCT_FIELDS or track == ChallengeTrack.product_feature:
        return "Consumer Marketplace"
    if any("cache" in f.name or "cdn" in f.name for f in item.metadata.fields):
        return "Platform Engineering"
    if any("query" in f.name or "execution_time" in f.name for f in item.metadata.fields):
        return "Data Infrastructure"

    return "B2B SaaS"


def _infer_stage(tag: SensitivityTag | None) -> str:
    if tag == SensitivityTag.red:
        return "Series A"
    if tag == SensitivityTag.yellow:
        return "Series A"
    return "Series B"


def _infer_team_size(tag: SensitivityTag | None) -> str:
    if tag == SensitivityTag.green:
        return "51-200"
    return "11-50"


def _default_stack(item: BacklogItem) -> list[str]:
    track = item.track or item.suggested_track
    if track == ChallengeTrack.product_feature:
        return ["TypeScript", "React", "Node.js", "PostgreSQL"]
    field_names = {f.name for f in item.metadata.fields}
    if field_names & _FINTECH_FIELDS:
        return ["Go", "PostgreSQL", "Redis", "AWS"]
    return ["Python", "PostgreSQL", "Docker", "AWS"]


def generate_profile(
    item: BacklogItem,
    *,
    reward: ChallengeReward | None = None,
) -> CompanyTechProfile:
    """
    Build a student-facing Company Tech Profile from backlog metadata.

    Red-sensitivity items omit industry_broad to prevent roadmap inference.
    """
    if item.id in _DEMO_PROFILES:
        base = _DEMO_PROFILES[item.id].model_copy()
    else:
        base = CompanyTechProfile(
            stage=_infer_stage(item.tag),
            team_size_range=_infer_team_size(item.tag),
            tech_stack=_default_stack(item),
            industry_broad=_infer_industry(item),
            verification_status="pending",
            verification_label="Platform-verified sponsor",
        )

    effective_reward = reward or item.reward
    if isinstance(effective_reward, dict):
        effective_reward = ChallengeReward.model_validate(effective_reward)
    if effective_reward and effective_reward.locked:
        base = base.model_copy(update={"verification_status": "verified"})

    return base
