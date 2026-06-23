from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer

from ..challenge_factory.models import ChallengeBlueprint, ChallengePackage, ChallengePackagePreview
from ..challenge_factory.spec_models import TechnicalChallengeSpec
from ..privacy_proxy.models import SanitizedMetadata


# ---------------------------------------------------------------------------
# Innovation tracks
# ---------------------------------------------------------------------------

class ChallengeTrack(str, Enum):
    technical = "technical"
    product_feature = "product_feature"
    automation = "automation"
    ai_governance = "ai_governance"
    strategy = "strategy"


class DeliverableType(str, Enum):
    code_repo = "code_repo"
    frontend_prototype = "frontend_prototype"
    external_link = "external_link"
    mixed = "mixed"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

class SensitivityTag(str, Enum):
    red = "red"       # Sensitivity >= 70 — high IP/security risk
    yellow = "yellow" # Sensitivity 40-69 — moderate risk
    green = "green"   # Sensitivity < 40  — safe to publish


class TechScores(BaseModel):
    severity: int = Field(ge=0, le=100, description="Impact on system performance/stability")
    friction: int = Field(ge=0, le=100, description="Volume/frequency of user-facing impact")
    sensitivity: int = Field(ge=0, le=100, description="IP or security exposure risk")
    sensitivity_reason: str = Field(description="Brief rationale for the sensitivity score")
    suggested_title: str = Field(description="Public-facing challenge title, ≤10 words")

    @property
    def tag(self) -> SensitivityTag:
        if self.sensitivity >= 70:
            return SensitivityTag.red
        if self.sensitivity >= 40:
            return SensitivityTag.yellow
        return SensitivityTag.green


# ---------------------------------------------------------------------------
# Relaxation
# ---------------------------------------------------------------------------

class RelaxationConfig(BaseModel):
    abstract_logic: bool = Field(
        default=False,
        description="Replace any field names that suggest proprietary logic with generic equivalents",
    )
    synthesize_variables: bool = Field(
        default=False,
        description="Map all field names to deterministic abstract tokens (e.g. node_alpha)",
    )
    noise_level: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="0.0 = no noise; 1.0 = maximum statistical perturbation of numeric metadata",
    )
    abstract_brand: bool = Field(
        default=True,
        description="Replace company-specific branding with the public brand_proxy name",
    )
    obfuscate_domain: bool = Field(
        default=False,
        description="Mask industry domain (e.g. food delivery → equipment sharing) for stealth",
    )


class DomainObfuscationPreview(BaseModel):
    domain_proxy: str
    public_title: str
    public_narrative: str
    internal_intent: str
    transform_rationale: str
    brand_proxy: str
    field_map: dict[str, str] = Field(default_factory=dict)
    public_fields: list[str] = Field(default_factory=list)


class RewardType(str, Enum):
    cash_bounty = "cash_bounty"
    interview_pass = "interview_pass"


class ChallengeReward(BaseModel):
    reward_type: RewardType = RewardType.cash_bounty
    amount_usd: int | None = Field(default=500, description="Demo bounty amount")
    interview_benchmark: int = Field(default=75, ge=0, le=100)
    locked: bool = False


class CompanyTechProfile(BaseModel):
    stage: str = Field(description="Funding stage, e.g. Series A")
    team_size_range: str = Field(description="LinkedIn-style range, e.g. 11-50")
    tech_stack: list[str] = Field(default_factory=list)
    industry_broad: str | None = Field(
        default=None,
        description="Broad industry category — omitted for red-sensitivity stealth items",
    )
    verification_status: Literal["verified", "pending"] = "pending"
    verification_label: str = "Platform-verified sponsor"


class PublishDraft(BaseModel):
    """Founder-editable student-facing challenge copy before publish."""

    title: str = Field(min_length=1, max_length=200)
    context: str = Field(min_length=1, max_length=4000)
    definition_of_success: list[str] = Field(min_length=1)
    structural_constraints: list[str] = Field(default_factory=list)
    evaluation_focus: list[str] = Field(default_factory=list)
    company_profile: CompanyTechProfile
    user_persona: str | None = None
    problem_framing: str | None = None
    design_considerations: list[str] = Field(default_factory=list)
    stack_guidance: list[str] = Field(default_factory=list)
    deliverable_requirements: list[str] = Field(default_factory=list)


class RelaxedPreview(BaseModel):
    original_fields: list[str]
    relaxed_fields: list[str]
    original_row_scale: int | None
    relaxed_row_scale: int | None
    noise_applied: float
    variable_map: dict[str, str] = Field(
        default_factory=dict,
        description="Maps original field name → synthesized token (populated when synthesize_variables=True)",
    )


# ---------------------------------------------------------------------------
# Micro-PRD
# ---------------------------------------------------------------------------

class MicroPRD(BaseModel):
    challenge_id: str
    title: str
    track: ChallengeTrack = ChallengeTrack.technical
    brand_proxy: str | None = None
    context: str = Field(description="2-3 sentences explaining the type of problem")
    definition_of_success: list[str] = Field(description="3-5 measurable outcome bullets")
    structural_constraints: list[str] = Field(description="Tech stack, memory limits, complexity requirements")
    sandbox_instructions: list[str] = Field(default_factory=list, description="Setup steps for the student")
    user_persona: str | None = Field(default=None, description="Product track: target user persona")
    problem_framing: str | None = Field(default=None, description="Product track: interview-style problem framing")
    design_considerations: list[str] = Field(default_factory=list)
    stack_guidance: list[str] = Field(default_factory=list)
    deliverable_requirements: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Backlog item — the central aggregate for the triage dashboard
# ---------------------------------------------------------------------------

class BacklogStatus(str, Enum):
    pending = "pending"       # Scored, not yet reviewed by founder
    reviewing = "reviewing"   # Founder is applying relaxation controls
    approved = "approved"     # Founder approved, ready to publish
    published = "published"   # Live in the public sandbox (submissions open)
    closed = "closed"         # Was live; submissions closed, hidden from student hub


class BacklogItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_label: str = Field(description="Human-readable label for the source (e.g. 'Slack #bugs 2024-03')")
    metadata: SanitizedMetadata
    scores: TechScores | None = None
    tag: SensitivityTag | None = None
    status: BacklogStatus = BacklogStatus.pending
    relaxation_config: RelaxationConfig = Field(default_factory=RelaxationConfig)
    relaxed_preview: RelaxedPreview | None = None
    microprd: MicroPRD | None = None
    dataset_path: str | None = Field(
        default=None,
        description="Filesystem path to generated SQLite dataset (set on publish)",
    )
    dataset_anomalies: list[str] = Field(
        default_factory=list,
        description="Human-readable list of injected dataset anomalies",
    )
    starter_files: dict[str, str] | None = Field(
        default=None,
        description="Multi-file starter scaffold generated on publish",
    )
    track: ChallengeTrack | None = Field(default=None, description="Innovation track for this challenge")
    suggested_track: ChallengeTrack | None = Field(
        default=None, description="AI PM track router suggestion",
    )
    brand_proxy: str | None = Field(default=None, description="Internal fictional brand — CTO-only, never public")
    company_profile: CompanyTechProfile | None = Field(
        default=None,
        description="Student-facing blind-audition company profile",
    )
    publish_draft: PublishDraft | None = Field(
        default=None,
        description="Founder-editable challenge copy before publish",
    )
    deliverable_types: list[DeliverableType] = Field(default_factory=list)
    evaluation_focus: list[str] = Field(default_factory=list)
    sponsor_profile: str | None = Field(
        default=None,
        description="Demo sponsor persona label (CTO dashboard only)",
    )
    domain_proxy: str | None = Field(default=None, description="Obfuscated industry domain key")
    domain_preview: DomainObfuscationPreview | None = Field(
        default=None,
        description="CTO-only before/after domain transform preview",
    )
    reward: ChallengeReward | None = Field(default=None, description="Guaranteed student reward")
    challenge_blueprint: ChallengeBlueprint | None = Field(
        default=None,
        description="Founder-editable technical challenge shape for factory generation",
    )
    challenge_spec: TechnicalChallengeSpec | None = Field(
        default=None,
        description="Canonical technical challenge spec from single-pass inference",
    )
    challenge_package: ChallengePackage | None = Field(
        default=None,
        description="Generated starter package from Preview — required for dynamic publish",
    )
    pool_label: str | None = Field(
        default=None,
        description="Open sandbox pool label for legacy anonymized scenarios",
    )
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("challenge_package")
    def _strip_reference_solution(self, package: ChallengePackage | None):
        if package is None:
            return None
        data = package.model_dump(mode="json")
        data.pop("reference_solution", None)
        return data


# ---------------------------------------------------------------------------
# API request / response shapes
# ---------------------------------------------------------------------------

class ScoreRequest(BaseModel):
    metadata: SanitizedMetadata
    source_label: str = "unlabelled"


class ScoreResponse(BaseModel):
    item_id: str
    scores: TechScores
    tag: SensitivityTag


class IntakeRequest(BaseModel):
    """Founder-authored problem brief — sanitized locally before scoring."""

    problem_statement: str = Field(min_length=1, max_length=20000)
    source_label: str = Field(default="Founder brief", min_length=1, max_length=200)
    format: str = Field(
        default="text",
        description="Input format hint for the privacy proxy: text, log, auto, etc.",
    )


class IntakeResponse(BaseModel):
    item_id: str
    scores: TechScores
    tag: SensitivityTag
    suggested_track: ChallengeTrack
    metadata: SanitizedMetadata
    pii_types_stripped: list[str] = Field(default_factory=list)
    processing_notes: list[str] = Field(default_factory=list)


class RelaxRequest(BaseModel):
    config: RelaxationConfig
    track: ChallengeTrack | None = Field(
        default=None,
        description="Founder override for innovation track at publish time",
    )
    reward: ChallengeReward | None = Field(
        default=None,
        description="Guaranteed bounty or interview pass — must be locked to publish",
    )
    draft: PublishDraft | None = Field(
        default=None,
        description="Founder-edited challenge copy — applied on publish (or returned as preview baseline)",
    )
    blueprint: ChallengeBlueprint | None = Field(
        default=None,
        description="Founder override for technical challenge archetype, stack, and starter hints",
    )


class ScopeCheckResponse(BaseModel):
    allowed: bool
    estimated_hours: float
    reason: str
    suggested_breakdown: list[str] = Field(default_factory=list)


class RelaxResponse(BaseModel):
    item_id: str
    preview: RelaxedPreview
    domain_preview: DomainObfuscationPreview | None = None
    company_profile: CompanyTechProfile | None = None
    challenge_draft: PublishDraft | None = None
    scope_check: ScopeCheckResponse | None = None
    challenge_blueprint: ChallengeBlueprint | None = None
    challenge_spec: TechnicalChallengeSpec | None = None
    challenge_package: ChallengePackagePreview | None = None


class PublishRequest(BaseModel):
    item_id: str
    config: RelaxationConfig


class PublishResponse(BaseModel):
    item_id: str
    microprd: MicroPRD
    status: BacklogStatus
    track: ChallengeTrack
    brand_proxy: str | None = None
    domain_proxy: str | None = None
    reward: ChallengeReward | None = None


class CloseResponse(BaseModel):
    item_id: str
    status: BacklogStatus
