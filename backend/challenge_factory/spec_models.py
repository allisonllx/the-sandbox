"""TechnicalChallengeSpec — canonical challenge definition for the factory pipeline."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .models import DataPlane, TechnicalArchetype


class IngestKind(str, Enum):
    behavioral_log = "behavioral_log"
    founder_brief = "founder_brief"
    schema_upload = "schema_upload"
    issue_intent = "issue_intent"


class SpecClassification(BaseModel):
    archetype: TechnicalArchetype
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    trigger_signals: list[str] = Field(default_factory=list)
    recommended_data_plane: DataPlane = DataPlane.none


class PublicAPIEntry(BaseModel):
    name: str
    signature: str = Field(description="Full Python def line, e.g. def foo(x: int) -> int")


class InterfaceContract(BaseModel):
    primary_module: str = Field(default="src/module.py")
    support_modules: list[str] = Field(default_factory=list)
    entrypoint: str = Field(default="main.py")
    public_api: list[PublicAPIEntry] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)


class StarterLayout(BaseModel):
    required_paths: list[str] = Field(default_factory=list)
    edit_targets: list[str] = Field(default_factory=list)
    student_may_add: list[str] = Field(default_factory=lambda: ["src/helpers/*.py"])


class TechnicalChallengeSpec(BaseModel):
    classification: SpecClassification
    title: str
    startup_pain_point: str
    scenario: str
    ingest_kind: IngestKind = IngestKind.behavioral_log
    interface_contract: InterfaceContract
    definition_of_done: list[str] = Field(default_factory=list)
    assessor_signals: list[str] = Field(default_factory=list)
    data_plane: DataPlane = DataPlane.none
    fixtures: dict[str, str] = Field(default_factory=dict)
    starter_layout: StarterLayout = Field(default_factory=StarterLayout)
    onboarding_budget_minutes: int = Field(default=30, ge=5, le=120)
    stack_guidance: list[str] = Field(default_factory=lambda: ["Python 3.11", "stdlib only"])
