from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ..privacy_proxy.models import SanitizedMetadata


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
    context: str = Field(description="2-3 sentences explaining the type of problem")
    definition_of_success: list[str] = Field(description="3-5 measurable outcome bullets")
    structural_constraints: list[str] = Field(description="Tech stack, memory limits, complexity requirements")
    sandbox_instructions: list[str] = Field(description="Numbered setup steps for the student")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Backlog item — the central aggregate for the triage dashboard
# ---------------------------------------------------------------------------

class BacklogStatus(str, Enum):
    pending = "pending"       # Scored, not yet reviewed by founder
    reviewing = "reviewing"   # Founder is applying relaxation controls
    approved = "approved"     # Founder approved, ready to publish
    published = "published"   # Live in the public sandbox


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
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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


class RelaxRequest(BaseModel):
    config: RelaxationConfig


class RelaxResponse(BaseModel):
    item_id: str
    preview: RelaxedPreview


class PublishRequest(BaseModel):
    item_id: str
    config: RelaxationConfig


class PublishResponse(BaseModel):
    item_id: str
    microprd: MicroPRD
    status: BacklogStatus
