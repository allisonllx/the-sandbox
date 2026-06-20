"""Dual-layer scorecard models — platform signal vs sponsor fit."""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from ..ai_pm.models import ChallengeTrack, MicroPRD


class ScoreLayer(BaseModel):
    """One scoring layer (platform or sponsor)."""

    dimensions: dict[str, int] = Field(default_factory=dict)
    score: int = Field(ge=0, le=100, description="Weighted aggregate 0–100")
    summary: str = ""
    notes: list[str] = Field(default_factory=list)


@dataclass
class ChallengeContext:
    """Sanitized challenge context for sponsor-fit assessment."""

    challenge_id: str
    track: ChallengeTrack
    evaluation_focus: list[str] = field(default_factory=list)
    definition_of_success: list[str] = field(default_factory=list)
    microprd_title: str | None = None


def challenge_context_from_item(item) -> ChallengeContext:
    """Build assessor context from a backlog item (no brand_proxy)."""
    microprd: MicroPRD | None = getattr(item, "microprd", None)
    draft = getattr(item, "publish_draft", None)
    success = (
        list(draft.definition_of_success)
        if draft and draft.definition_of_success
        else list(microprd.definition_of_success)
        if microprd
        else []
    )
    focus = (
        list(draft.evaluation_focus)
        if draft and draft.evaluation_focus
        else list(getattr(item, "evaluation_focus", []) or [])
    )
    title = draft.title if draft else (microprd.title if microprd else None)
    return ChallengeContext(
        challenge_id=item.id,
        track=item.track or ChallengeTrack.technical,
        evaluation_focus=focus,
        definition_of_success=success,
        microprd_title=title,
    )


def platform_execution_points(platform_score: int) -> int:
    """Execution Points derive only from platform signal."""
    return int(round(platform_score * 1.2))


def build_dual_layer_scorecard(
    *,
    track: str,
    platform: ScoreLayer,
    sponsor: ScoreLayer,
    reward=None,
) -> dict:
    """Assemble the nested scorecard with backward-compatible top-level aliases."""
    execution_points = platform_execution_points(platform.score)
    scorecard: dict = {
        "track": track,
        "platform": platform.model_dump(),
        "sponsor": sponsor.model_dump(),
        "execution_points": execution_points,
        "sponsor_fit_score": sponsor.score,
        "platform_score": platform.score,
        # Backward-compatible aliases — platform dimensions only
        "dimensions": dict(platform.dimensions),
        "summary": platform.summary or sponsor.summary,
        "notes": list(platform.notes) + list(sponsor.notes),
    }

    if reward and getattr(reward, "reward_type", None):
        from ..ai_pm.models import RewardType

        if reward.reward_type == RewardType.interview_pass:
            benchmark = reward.interview_benchmark
            platform_ok = platform.score >= benchmark
            sponsor_ok = sponsor.score >= benchmark
            earned = platform_ok and sponsor_ok
            scorecard["interview_pass_earned"] = earned
            scorecard["interview_benchmark"] = benchmark
            if earned:
                scorecard["notes"] = list(scorecard["notes"]) + [
                    f"Interview Pass earned (demo) — platform {platform.score} "
                    f"and sponsor fit {sponsor.score} ≥ benchmark {benchmark}."
                ]

    return scorecard
