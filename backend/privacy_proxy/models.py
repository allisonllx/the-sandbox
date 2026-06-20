from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InputFormat(str, Enum):
    auto = "auto"
    json = "json"
    csv = "csv"
    log = "log"
    text = "text"


class PIIDetection(BaseModel):
    pii_type: str = Field(description="Category of PII found, e.g. 'email', 'phone', 'jwt', 'api_key'")
    count: int = Field(description="Number of occurrences stripped")


class NEREntityCount(BaseModel):
    entity_label: str = Field(description="spaCy entity label, e.g. PERSON, ORG, GPE")
    count: int


class NERStatus(str, Enum):
    not_run = "not_run"
    skipped = "skipped"
    completed_empty = "completed_empty"
    completed = "completed"


class NERSummary(BaseModel):
    """Structured outcome of the local NER pass — check this before reading processing_notes."""

    status: NERStatus = Field(
        description=(
            "not_run: NER stage not reached; "
            "skipped: spaCy model unavailable; "
            "completed_empty: model ran, no entities found; "
            "completed: model ran, entities found"
        )
    )
    model_available: bool = Field(
        description="Whether the spaCy en_core_web_sm model loaded successfully"
    )
    entity_counts: list[NEREntityCount] = Field(
        default_factory=list,
        description="Named-entity types and counts detected in scrubbed text",
    )


class FieldMetadata(BaseModel):
    name: str
    inferred_type: str = Field(
        description="One of: string, integer, float, boolean, datetime, array, object, unknown"
    )
    nullable: bool = False
    sample_count: int = Field(default=0, description="Number of non-null values observed")


class EventFrequency(BaseModel):
    event_type: str
    count: int


class SanitizedMetadata(BaseModel):
    """
    The only artifact that crosses the local trust boundary.
    Contains structural information only — no raw content, no PII.
    """

    format_detected: InputFormat
    fields: list[FieldMetadata] = Field(default_factory=list)
    nested_paths: list[str] = Field(
        default_factory=list,
        description="Dot-notation paths to nested JSON keys, e.g. 'user.address.zip'",
    )
    approximate_row_scale: int | None = Field(
        default=None, description="Estimated number of records or log lines"
    )
    event_type_frequencies: list[EventFrequency] = Field(
        default_factory=list,
        description="For log inputs: detected event-type (level/component) counts",
    )
    pii_detections: list[PIIDetection] = Field(
        default_factory=list,
        description="Types and counts of PII stripped — never the values themselves",
    )
    ner: NERSummary = Field(
        default_factory=lambda: NERSummary(
            status=NERStatus.not_run,
            model_available=False,
        ),
        description="Structured NER outcome — prefer this over inferring from ner_entity_counts",
    )
    ner_entity_counts: list[NEREntityCount] = Field(
        default_factory=list,
        description="Deprecated mirror of ner.entity_counts — use metadata.ner instead",
    )
    blocked_chunk_count: int = Field(
        default=0,
        description="Number of text segments blocked entirely by the zero-leak guardrail",
    )
    processing_notes: list[str] = Field(
        default_factory=list,
        description="Non-sensitive diagnostics about the sanitization run",
    )


class SanitizeRequest(BaseModel):
    content: str = Field(description="Raw text to sanitize (log lines, JSON string, CSV text)")
    format: InputFormat = Field(default=InputFormat.auto)
    guardrail_keywords: list[str] = Field(
        default_factory=list,
        description="Additional keywords that trigger the zero-leak block on a chunk",
    )


class SanitizeResponse(BaseModel):
    ok: bool
    metadata: SanitizedMetadata
    error: str | None = None
