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
from .models import BacklogItem, BacklogStatus, ChallengeReward, ChallengeTrack, DeliverableType, RewardType, SensitivityTag, TechScores

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
        sponsor_profile="NovaPay (bounty sponsor)",
        reward=ChallengeReward(
            reward_type=RewardType.cash_bounty,
            amount_usd=500,
            interview_benchmark=75,
            locked=False,
        ),
    )
    return item


def _make_merchant_discovery_item() -> BacklogItem:
    metadata = SanitizedMetadata(
        format_detected=InputFormat.csv,
        fields=[
            FieldMetadata(name="feature_request", inferred_type="string", sample_count=842),
            FieldMetadata(name="screen_name", inferred_type="string", sample_count=842),
            FieldMetadata(name="ux_friction", inferred_type="string", sample_count=842),
            FieldMetadata(name="merchant_id", inferred_type="string", sample_count=842),
            FieldMetadata(name="discovery_query", inferred_type="string", sample_count=842),
            FieldMetadata(name="cart_abandon", inferred_type="boolean", sample_count=842),
        ],
        approximate_row_scale=842,
        event_type_frequencies=[
            EventFrequency(event_type="[product_feedback]", count=842),
            EventFrequency(event_type="[feature_request]", count=312),
            EventFrequency(event_type="[ux_research]", count=180),
        ],
        pii_detections=[PIIDetection(pii_type="email", count=3)],
        processing_notes=["Product feedback export — PII masked."],
    )
    scores = TechScores(
        severity=48,
        friction=72,
        sensitivity=38,
        sensitivity_reason="Feature roadmap hints but no proprietary algorithms exposed.",
        suggested_title="Local merchant discovery hub for mobile users",
    )
    return BacklogItem(
        id="demo-004",
        source_label="Product feedback export — merchant discovery Q2 2024",
        metadata=metadata,
        scores=scores,
        tag=SensitivityTag.yellow,
        status=BacklogStatus.pending,
        suggested_track=ChallengeTrack.product_feature,
        brand_proxy="EatsHub",
        deliverable_types=[
            DeliverableType.frontend_prototype,
            DeliverableType.external_link,
            DeliverableType.mixed,
        ],
        evaluation_focus=[
            "Information architecture",
            "Mobile-first responsive layout",
            "Checkout flow completeness",
            "Design trade-off reasoning",
        ],
    )


def _make_stealth_dine_in_item() -> BacklogItem:
    """StealthCo — Grab dine-in analog; requires domain obfuscation on publish."""
    metadata = SanitizedMetadata(
        format_detected=InputFormat.csv,
        fields=[
            FieldMetadata(name="voucher_code", inferred_type="string", sample_count=1200),
            FieldMetadata(name="restaurant_id", inferred_type="string", sample_count=1200),
            FieldMetadata(name="dine_in_session", inferred_type="string", sample_count=1200),
            FieldMetadata(name="map_pin_lat", inferred_type="float", sample_count=1200),
            FieldMetadata(name="map_pin_lng", inferred_type="float", sample_count=1200),
            FieldMetadata(name="checkout_step", inferred_type="string", sample_count=1200),
            FieldMetadata(name="cart_abandon", inferred_type="boolean", sample_count=1200),
        ],
        approximate_row_scale=1200,
        event_type_frequencies=[
            EventFrequency(event_type="[product_feedback]", count=1200),
            EventFrequency(event_type="[feature_request]", count=480),
        ],
        pii_detections=[PIIDetection(pii_type="email", count=2)],
        processing_notes=["Stealth roadmap export — PII masked."],
    )
    scores = TechScores(
        severity=55,
        friction=68,
        sensitivity=72,
        sensitivity_reason="Reveals unreleased dine-in voucher discovery roadmap.",
        suggested_title="Integrate restaurant dining vouchers into map discovery",
    )
    return BacklogItem(
        id="demo-005",
        source_label="StealthCo — dine-in voucher discovery Q3 roadmap (CONFIDENTIAL)",
        metadata=metadata,
        scores=scores,
        tag=SensitivityTag.red,
        status=BacklogStatus.pending,
        suggested_track=ChallengeTrack.product_feature,
        sponsor_profile="StealthCo (stealth / high sensitivity)",
        brand_proxy="LockerShare",
        deliverable_types=[
            DeliverableType.frontend_prototype,
            DeliverableType.external_link,
            DeliverableType.mixed,
        ],
        evaluation_focus=[
            "Discovery IA",
            "Mobile map vs list trade-offs",
            "Voucher redemption flow",
        ],
    )


def _make_platform_pool_item() -> BacklogItem:
    metadata = SanitizedMetadata(
        format_detected=InputFormat.log,
        fields=[
            FieldMetadata(name="request_id", inferred_type="string", sample_count=890000),
            FieldMetadata(name="latency_ms", inferred_type="float", sample_count=890000),
            FieldMetadata(name="status_code", inferred_type="integer", sample_count=890000),
            FieldMetadata(name="region", inferred_type="string", sample_count=890000),
            FieldMetadata(name="cache_hit", inferred_type="boolean", sample_count=890000),
        ],
        approximate_row_scale=890000,
        event_type_frequencies=[
            EventFrequency(event_type="ERROR", count=42000),
            EventFrequency(event_type="WARN", count=128000),
            EventFrequency(event_type="INFO", count=720000),
            EventFrequency(event_type="[traffic_spike]", count=890000),
        ],
        pii_detections=[],
        processing_notes=["Anonymized legacy scenario — already solved internally."],
    )
    scores = TechScores(
        severity=88,
        friction=95,
        sensitivity=12,
        sensitivity_reason="Historical Black Friday spike — no current roadmap leakage.",
        suggested_title="Replay 2024 Black Friday traffic spike diagnosis",
    )
    return BacklogItem(
        id="demo-006",
        source_label="Platform Pool — anonymized legacy infra scenario",
        metadata=metadata,
        scores=scores,
        tag=SensitivityTag.green,
        status=BacklogStatus.pending,
        sponsor_profile="Platform Pool (open sandbox)",
        pool_label="Anonymized legacy scenario — already solved internally",
        reward=ChallengeReward(
            reward_type=RewardType.interview_pass,
            interview_benchmark=70,
            locked=True,
        ),
    )


def _make_oversized_scope_item() -> BacklogItem:
    metadata = SanitizedMetadata(
        format_detected=InputFormat.csv,
        fields=[
            FieldMetadata(name=f"module_{i}", inferred_type="string", sample_count=50000)
            for i in range(18)
        ],
        approximate_row_scale=50000,
        event_type_frequencies=[
            EventFrequency(event_type="[feature_request]", count=50000),
            EventFrequency(event_type="[ux_research]", count=12000),
            EventFrequency(event_type="[platform]", count=8000),
        ],
        pii_detections=[],
        processing_notes=["Full product rebuild request."],
    )
    scores = TechScores(
        severity=60,
        friction=80,
        sensitivity=45,
        sensitivity_reason="Broad product scope — not a single modular task.",
        suggested_title="Build complete end-to-end full stack app for marketplace",
    )
    return BacklogItem(
        id="demo-007",
        source_label="Founder request — entire platform rebuild (full application)",
        metadata=metadata,
        scores=scores,
        tag=SensitivityTag.yellow,
        status=BacklogStatus.pending,
        sponsor_profile="Demo — scope cap rejection",
    )


# ---------------------------------------------------------------------------
# Store implementation
# ---------------------------------------------------------------------------

_store: dict[str, BacklogItem] = {}


def _init_store() -> None:
    for item in [
        _make_db_timeout_item(),
        _make_payment_retry_item(),
        _make_cache_miss_item(),
        _make_merchant_discovery_item(),
        _make_stealth_dine_in_item(),
        _make_platform_pool_item(),
        _make_oversized_scope_item(),
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


def list_published() -> list[BacklogItem]:
    """Return published challenges for the public sandbox."""
    items = [i for i in _store.values() if i.status == BacklogStatus.published]
    return sorted(items, key=lambda i: i.published_at or i.created_at, reverse=True)


def delete_item(item_id: str) -> bool:
    return _store.pop(item_id, None) is not None
