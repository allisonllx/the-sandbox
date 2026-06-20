from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from ..ai_pm.models import MicroPRD


class SubmissionStatus(str, Enum):
    received = "received"
    queued_for_assessment = "queued_for_assessment"


class PublishedChallenge(BaseModel):
    """Public-facing challenge card — no startup metadata or sensitivity scores."""

    id: str
    title: str
    status: str
    microprd: MicroPRD
    dataset_ready: bool
    dataset_anomalies: list[str] = Field(default_factory=list)
    published_at: datetime | None = None


class SubmitRequest(BaseModel):
    code: str = Field(min_length=1, description="Student solution source code")
    language: str = Field(default="python", description="Language identifier")


class SubmitResponse(BaseModel):
    ok: bool = True
    submission_id: str
    challenge_id: str
    status: SubmissionStatus
    message: str


class SubmissionRecord(BaseModel):
    id: str
    challenge_id: str
    code: str
    language: str
    status: SubmissionStatus
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
