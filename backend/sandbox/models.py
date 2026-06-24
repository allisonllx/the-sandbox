from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..ai_pm.models import ChallengeTrack, DeliverableType, MicroPRD, ChallengeReward, CompanyTechProfile


class SubmissionStatus(str, Enum):
    received = "received"
    queued_for_assessment = "queued_for_assessment"
    assessed = "assessed"


class PublishedChallenge(BaseModel):
    """Public-facing challenge card — no startup metadata or sensitivity scores."""

    id: str
    title: str
    status: str
    track: ChallengeTrack = ChallengeTrack.technical
    company_profile: CompanyTechProfile
    deliverable_types: list[DeliverableType] = Field(default_factory=list)
    evaluation_focus: list[str] = Field(default_factory=list)
    microprd: MicroPRD
    dataset_ready: bool
    uses_dataset: bool = False
    starter_ready: bool = False
    dataset_anomalies: list[str] = Field(default_factory=list)
    reward: ChallengeReward | None = None
    reward_escrow_label: str | None = None
    published_at: datetime | None = None


class StarterResponse(BaseModel):
    ok: bool = True
    challenge_id: str
    files: dict[str, str]


class DraftSaveRequest(BaseModel):
    files: dict[str, str]
    client_revision: int = Field(ge=0)
    updated_at: datetime | None = None


class DraftSaveResponse(BaseModel):
    ok: bool = True
    saved_at: datetime
    revision: int


class DraftPayload(BaseModel):
    files: dict[str, str]
    client_revision: int
    updated_at: datetime
    server_updated_at: datetime | None = None


class WorkspaceBootstrapResponse(BaseModel):
    ok: bool = True
    workspace_id: str
    draft: DraftPayload | None = None


class Diagnostic(BaseModel):
    line: int
    column: int
    message: str
    severity: str = "error"


class ValidateRequest(BaseModel):
    path: str
    content: str


class ValidateResponse(BaseModel):
    ok: bool = True
    diagnostics: list[Diagnostic] = Field(default_factory=list)


class SubmitRequest(BaseModel):
    mode: Literal["inline", "legacy"] = "inline"
    code: str | None = Field(default=None, description="Legacy single-file submit")
    files: dict[str, str] | None = Field(default=None, description="Multi-file inline submit")
    links: dict[str, str] | None = Field(
        default=None,
        description="Optional external links: figma, deployment, github",
    )
    language: str = Field(default="python", description="Language identifier")

    @model_validator(mode="after")
    def _require_payload(self) -> SubmitRequest:
        if self.files:
            self.mode = "inline"
            return self
        if self.code and self.code.strip():
            self.mode = "legacy"
            return self
        raise ValueError("Submit requires code or files")


class SubmitResponse(BaseModel):
    ok: bool = True
    submission_id: str
    challenge_id: str
    status: SubmissionStatus
    message: str
    scorecard: dict | None = None


class SubmissionRecord(BaseModel):
    id: str
    challenge_id: str
    workspace_id: str | None = None
    track: ChallengeTrack = ChallengeTrack.technical
    files: dict[str, str]
    links: dict[str, str] = Field(default_factory=dict)
    language: str
    status: SubmissionStatus
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: str = "inline"
    scorecard: dict | None = None

    @property
    def code(self) -> str:
        if "solution.py" in self.files:
            return self.files["solution.py"]
        first = next(iter(self.files.values()), "")
        return first


class RunJobRequest(BaseModel):
    files: dict[str, str]


class RunJobResponse(BaseModel):
    ok: bool = True
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    ok: bool = True
    job_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ScoreLayerResponse(BaseModel):
    dimensions: dict[str, int] = Field(default_factory=dict)
    score: int = 0
    summary: str = ""
    notes: list[str] = Field(default_factory=list)


class ScorecardResponse(BaseModel):
    ok: bool = True
    submission_id: str
    track: ChallengeTrack
    dimensions: dict[str, int]
    summary: str
    notes: list[str] = Field(default_factory=list)
    platform: ScoreLayerResponse | None = None
    sponsor: ScoreLayerResponse | None = None
    execution_points: int | None = None
    sponsor_fit_score: int | None = None
    platform_score: int | None = None


class SponsorSubmissionDetail(BaseModel):
    """CTO-only submission snapshot for Match Radar drill-down."""

    ok: bool = True
    submission_id: str
    challenge_id: str
    candidate_id: str
    track: ChallengeTrack
    submitted_at: datetime
    files: dict[str, str]
    links: dict[str, str] = Field(default_factory=dict)
    scorecard: dict | None = None
