"""
In-memory backlog store.

For the MVP/hackathon, this is a module-level dict keyed by item ID.
It is pre-populated with three realistic demo items so the dashboard
works immediately without running the full pipeline.

Replace with a proper database persistence layer for production.
"""

from __future__ import annotations

from ..privacy_proxy.models import (
    EventFrequency,
    FieldMetadata,
    InputFormat,
    PIIDetection,
    SanitizedMetadata,
)
from .models import BacklogItem, BacklogStatus, SensitivityTag, TechScores

# ---------------------------------------------------------------------------
# Demo seed data — three pre-scored backlog items
# ---------------------------------------------------------------------------

def _make_db_timeout_item() -> BacklogItem:
    metadata = SanitizedMetadata(
        format_detected=InputFormat.log,
        fields=[
            FieldMetadata(name="user_id", inferred_type="integer", sample_count=1204),
            FieldMetadata(name="query_hash", inferred_type="string", sample_count=1204),
            FieldMetadata(name="execution_time_ms", inferred_type="float", sample_count=1204),
            FieldMetadata(name="table_name", inferred_type="string", sample_count=1204),
            FieldMetadata(name="index_hit", inferred_type="boolean", sample_count=1204, nullable=True),
            FieldMetadata(name="rows_scanned", inferred_type="integer", sample_count=1204),
        ],
        approximate_row_scale=1204,
        event_type_frequencies=[
            EventFrequency(event_type="ERROR", count=312),
            EventFrequency(event_type="WARN", count=678),
            EventFrequency(event_type="INFO", count=214),
            EventFrequency(event_type="[db_pool]", count=1204),
        ],
        pii_detections=[PIIDetection(pii_type="email", count=2)],
        processing_notes=["2 PII token(s) masked."],
    )
    scores = TechScores(
        severity=82,
        friction=67,
        sensitivity=74,
        sensitivity_reason="Exposes internal DB schema and query patterns.",
        suggested_title="Diagnose cascading query timeout in data layer",
    )
    item = BacklogItem(
        id="demo-001",
        source_label="Datadog APM alerts — week of 2024-03-11",
        metadata=metadata,
        scores=scores,
        tag=SensitivityTag.red,
        status=BacklogStatus.pending,
    )
    return item


def _make_payment_retry_item() -> BacklogItem:
    metadata = SanitizedMetadata(
        format_detected=InputFormat.log,
        fields=[
            FieldMetadata(name="transaction_id", inferred_type="string", sample_count=8821),
            FieldMetadata(name="retry_count", inferred_type="integer", sample_count=8821),
            FieldMetadata(name="gateway_response_code", inferred_type="integer", sample_count=8821),
            FieldMetadata(name="amount_cents", inferred_type="integer", sample_count=8821),
            FieldMetadata(name="processor_name", inferred_type="string", sample_count=8821),
            FieldMetadata(name="idempotency_key", inferred_type="string", sample_count=8821),
        ],
        approximate_row_scale=8821,
        event_type_frequencies=[
            EventFrequency(event_type="ERROR", count=1643),
            EventFrequency(event_type="INFO", count=7178),
            EventFrequency(event_type="[payment_processor]", count=8821),
        ],
        pii_detections=[
            PIIDetection(pii_type="api_key", count=1),
            PIIDetection(pii_type="email", count=5),
        ],
        processing_notes=["6 PII token(s) masked."],
    )
    scores = TechScores(
        severity=75,
        friction=89,
        sensitivity=55,
        sensitivity_reason="Payment field names hint at financial processing logic.",
        suggested_title="Resolve retry storm in async event processor",
    )
    item = BacklogItem(
        id="demo-002",
        source_label="Intercom support tickets — payment failures Q1 2024",
        metadata=metadata,
        scores=scores,
        tag=SensitivityTag.yellow,
        status=BacklogStatus.pending,
    )
    return item


def _make_cache_miss_item() -> BacklogItem:
    metadata = SanitizedMetadata(
        format_detected=InputFormat.log,
        fields=[
            FieldMetadata(name="asset_path", inferred_type="string", sample_count=44200),
            FieldMetadata(name="cache_status", inferred_type="string", sample_count=44200),
            FieldMetadata(name="cdn_region", inferred_type="string", sample_count=44200),
            FieldMetadata(name="ttl_seconds", inferred_type="integer", sample_count=44200),
            FieldMetadata(name="response_time_ms", inferred_type="float", sample_count=44200),
        ],
        approximate_row_scale=44200,
        event_type_frequencies=[
            EventFrequency(event_type="WARN", count=9840),
            EventFrequency(event_type="INFO", count=34360),
            EventFrequency(event_type="DEBUG", count=6700),
            EventFrequency(event_type="[cdn_proxy]", count=44200),
        ],
        pii_detections=[],
        processing_notes=["No PII detected."],
    )
    scores = TechScores(
        severity=23,
        friction=45,
        sensitivity=18,
        sensitivity_reason="CDN/cache field names reveal no sensitive business logic.",
        suggested_title="Optimise CDN cache-hit ratio for static assets",
    )
    item = BacklogItem(
        id="demo-003",
        source_label="CloudFront access logs — March 2024",
        metadata=metadata,
        scores=scores,
        tag=SensitivityTag.green,
        status=BacklogStatus.pending,
    )
    return item


# ---------------------------------------------------------------------------
# Store implementation
# ---------------------------------------------------------------------------

_store: dict[str, BacklogItem] = {}


def _init_store() -> None:
    for item in [
        _make_db_timeout_item(),
        _make_payment_retry_item(),
        _make_cache_miss_item(),
    ]:
        _store[item.id] = item


_init_store()


def list_items() -> list[BacklogItem]:
    """Return all backlog items sorted by severity descending."""
    return sorted(
        _store.values(),
        key=lambda i: (i.scores.severity if i.scores else 0),
        reverse=True,
    )


def get_item(item_id: str) -> BacklogItem | None:
    return _store.get(item_id)


def upsert_item(item: BacklogItem) -> BacklogItem:
    _store[item.id] = item
    return item


def delete_item(item_id: str) -> bool:
    return _store.pop(item_id, None) is not None
