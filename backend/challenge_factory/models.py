"""Challenge artifact models for the dynamic factory pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class TechnicalArchetype(str, Enum):
    data_adjacent = "data_adjacent"
    data_core = "data_core"
    service_module = "service_module"
    algorithm = "algorithm"
    integration = "integration"


class DataPlane(str, Enum):
    none = "none"
    sqlite = "sqlite"
    csv_fixtures = "csv_fixtures"
    json_fixtures = "json_fixtures"


class ChallengeBlueprint(BaseModel):
    """Founder-influenced shape of a technical challenge before artifact generation."""

    archetype: TechnicalArchetype = TechnicalArchetype.service_module
    primary_focus: str = Field(
        default="Implement the core module described in the Micro-PRD",
        min_length=1,
        max_length=500,
    )
    data_plane: DataPlane = DataPlane.none
    languages: list[str] = Field(default_factory=lambda: ["python"])
    stack_guidance: list[str] = Field(default_factory=list)
    starter_hints: str | None = None
    example_files: dict[str, str] | None = None
    edit_targets: list[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    passed: bool
    test_count: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    security_score: int = Field(default=100, ge=0, le=100)
    security_violations: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


class ChallengePackage(BaseModel):
    """Generated artifact bundle — reference_solution is internal only."""

    blueprint: ChallengeBlueprint
    starter_files: dict[str, str]
    reference_solution: dict[str, str] = Field(
        default_factory=dict,
        description="Full working tree for validator/secret tests — never student-facing",
    )
    schema_spec: dict | None = None
    dataset_path: str | None = None
    fixture_files: dict[str, str] = Field(default_factory=dict)
    dataset_anomalies: list[str] = Field(default_factory=list)
    secret_tests_path: str | None = None
    validation: ValidationReport
    generation_source: Literal["legacy", "dynamic"] = "dynamic"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_config_hash: str = Field(
        default="",
        description="Hash of publish draft + blueprint at generation time",
    )

    @property
    def file_paths(self) -> list[str]:
        return sorted(self.starter_files.keys())


class ChallengePackagePreview(BaseModel):
    """Founder-facing package view — omits reference_solution."""

    blueprint: ChallengeBlueprint
    starter_files: dict[str, str]
    validation: ValidationReport
    generation_source: Literal["legacy", "dynamic"]
    generated_at: datetime
    stale: bool = False
    dataset_path: str | None = None
    dataset_anomalies: list[str] = Field(default_factory=list)
    fixture_files: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_package(cls, package: ChallengePackage, *, stale: bool = False) -> ChallengePackagePreview:
        return cls(
            blueprint=package.blueprint,
            starter_files=package.starter_files,
            validation=package.validation,
            generation_source=package.generation_source,
            generated_at=package.generated_at,
            stale=stale,
            dataset_path=package.dataset_path,
            dataset_anomalies=package.dataset_anomalies,
            fixture_files=package.fixture_files,
        )
