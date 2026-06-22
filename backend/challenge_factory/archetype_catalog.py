"""Default interface contracts and reference bodies per archetype."""

from __future__ import annotations

from dataclasses import dataclass

from ..privacy_proxy.models import SanitizedMetadata
from .models import DataPlane, TechnicalArchetype, normalize_archetype
from .spec_models import (
    IngestKind,
    InterfaceContract,
    PublicAPIEntry,
    SpecClassification,
    StarterLayout,
    TechnicalChallengeSpec,
)

_DB_FIELD_HINTS = frozenset(
    {"query_hash", "execution_time_ms", "table_name", "rows_scanned", "index_hit"}
)
_RETRY_FIELD_HINTS = frozenset({"retry_count", "idempotency_key", "gateway_response_code"})
_TENANT_HINTS = frozenset({"tenant_id", "org_id", "account_id"})
_PII_HINTS = frozenset({"email", "phone", "ssn", "pii", "user_id"})
_STREAM_HINTS = frozenset({"file_size_bytes", "chunk_count", "oom", "memory_mb"})
_CLI_HINTS = frozenset({"latency_ms", "token_count", "command", "cli_duration_ms"})
_ADAPTER_HINTS = frozenset({"source_system", "target_schema", "connector", "sync_status"})
_CIRCUIT_HINTS = frozenset({"timeout_ms", "failure_rate", "circuit_state", "downstream_status"})


@dataclass(frozen=True)
class ArchetypeDefaults:
    primary_module: str
    public_api: list[PublicAPIEntry]
    invariants: list[str]
    pain_point: str
    scenario_template: str
    definition_of_done: list[str]
    assessor_signals: list[str]
    stub_body: str
    reference_body: str
    test_body: str
    support_modules: list[str] | None = None


def _field_names(metadata: SanitizedMetadata) -> set[str]:
    return {f.name for f in metadata.fields}


def infer_archetype_from_metadata(
    metadata: SanitizedMetadata,
    *,
    founder_override: TechnicalArchetype | None = None,
) -> TechnicalArchetype:
    if founder_override is not None and founder_override == TechnicalArchetype.algorithm:
        return TechnicalArchetype.algorithm
    if founder_override is not None:
        return normalize_archetype(founder_override, field_names=_field_names(metadata))

    names = _field_names(metadata)
    if names & _DB_FIELD_HINTS:
        return TechnicalArchetype.data_core
    if names & _RETRY_FIELD_HINTS:
        if "idempotency_key" in names:
            return TechnicalArchetype.idempotency_engine
        return TechnicalArchetype.webhook_handler
    if names & _TENANT_HINTS:
        return TechnicalArchetype.rls_proxy
    if names & _PII_HINTS:
        return TechnicalArchetype.data_masking
    if names & _STREAM_HINTS:
        return TechnicalArchetype.stream_parser
    if names & _CLI_HINTS:
        return TechnicalArchetype.cli_instrumentation
    if names & _ADAPTER_HINTS:
        return TechnicalArchetype.data_adapter
    if names & _CIRCUIT_HINTS:
        return TechnicalArchetype.circuit_breaker
    return TechnicalArchetype.webhook_handler


def _trigger_signals(archetype: TechnicalArchetype, names: set[str]) -> list[str]:
    hints = {
        TechnicalArchetype.idempotency_engine: _RETRY_FIELD_HINTS,
        TechnicalArchetype.webhook_handler: _RETRY_FIELD_HINTS,
        TechnicalArchetype.data_core: _DB_FIELD_HINTS,
        TechnicalArchetype.rls_proxy: _TENANT_HINTS,
        TechnicalArchetype.data_masking: _PII_HINTS,
        TechnicalArchetype.stream_parser: _STREAM_HINTS,
        TechnicalArchetype.cli_instrumentation: _CLI_HINTS,
        TechnicalArchetype.data_adapter: _ADAPTER_HINTS,
        TechnicalArchetype.circuit_breaker: _CIRCUIT_HINTS,
    }
    matched = sorted(names & hints.get(archetype, set()))
    return matched or [archetype.value]


def _defaults_for(archetype: TechnicalArchetype) -> ArchetypeDefaults:
    archetype = normalize_archetype(archetype)
    catalog: dict[TechnicalArchetype, ArchetypeDefaults] = {
        TechnicalArchetype.idempotency_engine: ArchetypeDefaults(
            primary_module="src/idempotency_store.py",
            public_api=[
                PublicAPIEntry(
                    name="process_once",
                    signature="def process_once(idempotency_key: str, payload: dict) -> dict",
                ),
            ],
            invariants=["Same idempotency_key processed exactly once"],
            pain_point="Duplicate webhook retries double-charge customers when the gateway returns 502.",
            scenario_template=(
                "Payment webhooks retry on gateway failures. Your job is to build an idempotency store "
                "so duplicate deliveries with the same idempotency_key are processed exactly once. "
                "The repo ships stubs, public tests, and docs/SPEC.md — implement the primary module."
            ),
            definition_of_done=[
                "Duplicate idempotency_key returns cached result without side effects",
                "First-seen keys persist outcome for replay",
                "Public tests pass in the browser workspace",
            ],
            assessor_signals=["zero double-writes on concurrent retries"],
            stub_body='''"""Idempotency store — students implement process_once."""

from __future__ import annotations


def process_once(idempotency_key: str, payload: dict) -> dict:
    """
    Process payload exactly once per idempotency_key.

    TODO: always processes — add deduplication.
    """
    return {"status": "processed", "key": idempotency_key, "payload": payload}
''',
            reference_body='''"""Idempotency store — reference implementation."""

from __future__ import annotations

_store: dict[str, dict] = {}


def process_once(idempotency_key: str, payload: dict) -> dict:
    if idempotency_key in _store:
        return _store[idempotency_key]
    result = {"status": "processed", "key": idempotency_key, "amount": payload.get("amount_cents", 0)}
    _store[idempotency_key] = result
    return result
''',
            test_body='''"""Public tests for process_once."""

from src.idempotency_store import process_once


def test_first_process():
    result = process_once("key-1", {"amount_cents": 100})
    assert result["status"] == "processed"
    assert result["amount"] == 100


def test_idempotent_replay():
    first = process_once("key-2", {"amount_cents": 200})
    second = process_once("key-2", {"amount_cents": 999})
    assert second == first
    assert second["amount"] == 200
''',
        ),
        TechnicalArchetype.webhook_handler: ArchetypeDefaults(
            primary_module="src/webhook_engine.py",
            public_api=[
                PublicAPIEntry(
                    name="process_event",
                    signature="def process_event(payload: dict, headers: dict) -> dict",
                ),
            ],
            invariants=["Invalid signatures rejected", "Transient 502 responses retried safely"],
            pain_point="Webhook ingestion fails under gateway 502 storms without safe retries.",
            scenario_template=(
                "Your startup receives payment webhooks that intermittently fail with HTTP 502. "
                "Build a fail-safe webhook engine that validates events and retries transient failures. "
                "Use the provided SPEC.md and public tests — focus on src/webhook_engine.py."
            ),
            definition_of_done=[
                "Valid events return success status",
                "Transient failures retry up to configured limit",
                "Public tests pass without external network calls",
            ],
            assessor_signals=["safe retry without duplicate side effects"],
            stub_body='''"""Webhook engine — students implement process_event."""

from __future__ import annotations

MAX_RETRIES = 3


def process_event(payload: dict, headers: dict) -> dict:
    """
    Validate and process a webhook event.

    TODO: no retry logic — add safe retries for transient failures.
    """
    if not payload:
        raise ValueError("empty payload")
    return {"status": "ok", "attempts": 1}
''',
            reference_body='''"""Webhook engine — reference implementation."""

from __future__ import annotations

MAX_RETRIES = 3


def process_event(payload: dict, headers: dict) -> dict:
    if not payload:
        raise ValueError("empty payload")
    transient = headers.get("X-Simulate-502") == "1"
    attempts = 0
    while attempts < MAX_RETRIES:
        attempts += 1
        if transient and attempts < MAX_RETRIES:
            continue
        return {"status": "ok", "attempts": attempts}
    return {"status": "failed", "attempts": attempts}
''',
            test_body='''"""Public tests for process_event."""

import pytest

from src.webhook_engine import process_event


def test_valid_event():
    result = process_event({"type": "payment"}, {})
    assert result["status"] == "ok"


def test_empty_payload_rejected():
    with pytest.raises(ValueError):
        process_event({}, {})


def test_retries_transient():
    result = process_event({"type": "payment"}, {"X-Simulate-502": "1"})
    assert result["status"] == "ok"
    assert result["attempts"] >= 2
''',
        ),
        TechnicalArchetype.data_core: ArchetypeDefaults(
            primary_module="src/queries.py",
            public_api=[
                PublicAPIEntry(
                    name="batch_session_lookup",
                    signature="def batch_session_lookup(conn, event_ids: list[int]) -> list",
                ),
            ],
            invariants=["Preserve schema contracts", "Reduce P99 lookup latency"],
            pain_point="Session lookup queries degrade under load against the SQLite dataset.",
            scenario_template=(
                "Analytics queries against the provided SQLite dataset are too slow. "
                "Optimize batch_session_lookup in src/queries.py. Read docs/DATA.md for schema context."
            ),
            definition_of_done=[
                "batch_session_lookup returns correct rows for event_ids",
                "Public tests pass against sandbox.sqlite",
            ],
            assessor_signals=["correct results with improved query pattern"],
            stub_body="",  # filled by legacy data_core scaffold
            reference_body="",
            test_body="",
        ),
        TechnicalArchetype.algorithm: ArchetypeDefaults(
            primary_module="src/solution.py",
            public_api=[
                PublicAPIEntry(
                    name="clamp_values",
                    signature="def clamp_values(values: list[float], low: float, high: float) -> list[float]",
                ),
            ],
            invariants=["Pure in-memory logic", "No I/O"],
            pain_point="Batch numeric processing returns incorrect bounds.",
            scenario_template=(
                "Fix clamp_values in src/solution.py so each value is bounded to [low, high]. "
                "The starter implementation is intentionally wrong — public tests define correctness."
            ),
            definition_of_done=["clamp_values passes all public tests"],
            assessor_signals=["correct edge cases for empty input"],
            stub_body='''"""Core algorithm — fix clamp_values."""

from __future__ import annotations


def clamp_values(values: list[float], low: float, high: float) -> list[float]:
    """TODO: returns inputs unchanged — clamp each value."""
    return list(values)
''',
            reference_body='''"""Core algorithm — reference."""

from __future__ import annotations


def clamp_values(values: list[float], low: float, high: float) -> list[float]:
    return [max(low, min(high, v)) for v in values]
''',
            test_body='''"""Public tests for clamp_values."""

from src.solution import clamp_values


def test_clamp_basic():
    assert clamp_values([0.5, 1.5, -1.0], 0.0, 1.0) == [0.5, 1.0, 0.0]


def test_clamp_empty():
    assert clamp_values([], 0.0, 1.0) == []
''',
        ),
        TechnicalArchetype.circuit_breaker: ArchetypeDefaults(
            primary_module="src/circuit_breaker.py",
            public_api=[
                PublicAPIEntry(name="call", signature="def call(fn) -> object"),
            ],
            invariants=["Open circuit rejects calls", "Half-open allows probe"],
            pain_point="Downstream timeouts cascade through every request.",
            scenario_template="Implement a circuit breaker in src/circuit_breaker.py with open/half-open/closed states.",
            definition_of_done=["Opens after failure threshold", "Recovers after cooldown"],
            assessor_signals=["fail-fast when circuit open"],
            stub_body='''"""Circuit breaker stub."""

from __future__ import annotations


def call(fn):
    """TODO: always calls fn — add circuit breaker."""
    return fn()
''',
            reference_body='''"""Circuit breaker reference."""

from __future__ import annotations

_failures = 0
_open = False
_THRESHOLD = 2


def call(fn):
    global _failures, _open
    if _open:
        raise RuntimeError("circuit open")
    try:
        return fn()
    except Exception:
        _failures += 1
        if _failures >= _THRESHOLD:
            _open = True
        raise
''',
            test_body='''"""Public tests for circuit breaker."""

import pytest

from src.circuit_breaker import call


def test_success():
    assert call(lambda: 42) == 42


def test_opens_after_failures():
    for _ in range(2):
        with pytest.raises(ValueError):
            call(lambda: (_ for _ in ()).throw(ValueError("fail")))
    with pytest.raises(RuntimeError):
        call(lambda: 1)
''',
        ),
        TechnicalArchetype.data_adapter: ArchetypeDefaults(
            primary_module="src/adapter.py",
            public_api=[
                PublicAPIEntry(name="map_record", signature="def map_record(source: dict) -> dict"),
            ],
            invariants=["Schema mapping is deterministic"],
            pain_point="Multi-source records need normalized schema mapping.",
            scenario_template="Build map_record in src/adapter.py to normalize external records to internal schema.",
            definition_of_done=["All required fields mapped", "Unknown fields preserved in extras"],
            assessor_signals=["handles missing optional fields"],
            stub_body='''"""Data adapter stub."""

from __future__ import annotations


def map_record(source: dict) -> dict:
    """TODO: returns source unchanged — map to internal schema."""
    return source
''',
            reference_body='''"""Data adapter reference."""

from __future__ import annotations


def map_record(source: dict) -> dict:
    return {
        "id": source.get("external_id") or source.get("id"),
        "name": source.get("name", ""),
        "extras": {k: v for k, v in source.items() if k not in ("external_id", "id", "name")},
    }
''',
            test_body='''"""Public tests for map_record."""

from src.adapter import map_record


def test_maps_external_id():
    assert map_record({"external_id": "x1", "name": "Acme"})["id"] == "x1"
''',
        ),
        TechnicalArchetype.cli_instrumentation: ArchetypeDefaults(
            primary_module="src/cli_metrics.py",
            public_api=[
                PublicAPIEntry(name="record", signature="def record(command: str, duration_ms: float) -> None"),
                PublicAPIEntry(name="summary", signature="def summary() -> dict"),
            ],
            invariants=["Metrics are in-memory only"],
            pain_point="CLI tools lack latency visibility for developers.",
            scenario_template="Implement record/summary in src/cli_metrics.py for dev CLI observability.",
            definition_of_done=["record accumulates durations", "summary returns count and avg"],
            assessor_signals=["correct average calculation"],
            stub_body='''"""CLI metrics stub."""

from __future__ import annotations

_events: list[tuple[str, float]] = []


def record(command: str, duration_ms: float) -> None:
    """TODO: does not record — implement."""
    pass


def summary() -> dict:
    """TODO: returns empty — implement."""
    return {"count": 0, "avg_ms": 0.0}
''',
            reference_body='''"""CLI metrics reference."""

from __future__ import annotations

_events: list[tuple[str, float]] = []


def record(command: str, duration_ms: float) -> None:
    _events.append((command, duration_ms))


def summary() -> dict:
    if not _events:
        return {"count": 0, "avg_ms": 0.0}
    total = sum(d for _, d in _events)
    return {"count": len(_events), "avg_ms": total / len(_events)}
''',
            test_body='''"""Public tests for cli_metrics."""

from src.cli_metrics import record, summary


def test_record_and_summary():
    record("lint", 100.0)
    record("test", 200.0)
    s = summary()
    assert s["count"] == 2
    assert s["avg_ms"] == 150.0
''',
        ),
        TechnicalArchetype.data_masking: ArchetypeDefaults(
            primary_module="src/masker.py",
            public_api=[
                PublicAPIEntry(name="mask_record", signature="def mask_record(record: dict) -> dict"),
            ],
            invariants=["PII fields redacted", "Referential keys stable"],
            pain_point="Analytics exports leak PII without referential masking.",
            scenario_template="Implement mask_record in src/masker.py to redact PII while preserving join keys.",
            definition_of_done=["email/phone redacted", "stable surrogate for user_id"],
            assessor_signals=["same user_id maps to same surrogate"],
            stub_body='''"""PII masker stub."""

from __future__ import annotations


def mask_record(record: dict) -> dict:
    """TODO: returns record unchanged — redact PII."""
    return record
''',
            reference_body='''"""PII masker reference."""

from __future__ import annotations

import hashlib


def mask_record(record: dict) -> dict:
    out = dict(record)
    if "email" in out:
        out["email"] = "***@redacted"
    if "phone" in out:
        out["phone"] = "***"
    if "user_id" in out:
        uid = str(out["user_id"])
        out["user_id"] = hashlib.sha256(uid.encode()).hexdigest()[:12]
    return out
''',
            test_body='''"""Public tests for mask_record."""

from src.masker import mask_record


def test_masks_email():
    result = mask_record({"email": "a@b.com", "user_id": "u1"})
    assert result["email"] == "***@redacted"
    assert result["user_id"] != "u1"
''',
        ),
        TechnicalArchetype.stream_parser: ArchetypeDefaults(
            primary_module="src/stream_parser.py",
            public_api=[
                PublicAPIEntry(name="parse_lines", signature="def parse_lines(lines) -> list[dict]"),
            ],
            invariants=["Memory bounded — no full materialization"],
            pain_point="Large log uploads OOM the parser.",
            scenario_template="Implement memory-bounded parse_lines in src/stream_parser.py for streaming JSONL.",
            definition_of_done=["Parses valid lines", "Skips malformed lines"],
            assessor_signals=["handles empty iterator"],
            stub_body='''"""Stream parser stub."""

from __future__ import annotations

import json


def parse_lines(lines) -> list[dict]:
    """TODO: loads all at once — stream safely."""
    return [json.loads(line) for line in lines]
''',
            reference_body='''"""Stream parser reference."""

from __future__ import annotations

import json


def parse_lines(lines) -> list[dict]:
    out: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
''',
            test_body='''"""Public tests for stream_parser."""

from src.stream_parser import parse_lines


def test_parse_valid():
    lines = ['{"a": 1}', '{"b": 2}']
    assert parse_lines(lines) == [{"a": 1}, {"b": 2}]


def test_skips_bad_lines():
    lines = ['{"a": 1}', "not-json", '{"b": 2}']
    assert len(parse_lines(lines)) == 2
''',
        ),
        TechnicalArchetype.rls_proxy: ArchetypeDefaults(
            primary_module="src/tenant_proxy.py",
            public_api=[
                PublicAPIEntry(
                    name="filter_rows",
                    signature="def filter_rows(rows: list[dict], tenant_id: str) -> list[dict]",
                ),
            ],
            invariants=["Rows from other tenants never returned"],
            pain_point="Multi-tenant queries leak cross-tenant rows.",
            scenario_template="Implement filter_rows in src/tenant_proxy.py for row-level tenant isolation.",
            definition_of_done=["Only matching tenant_id rows returned"],
            assessor_signals=["empty tenant returns empty list"],
            stub_body='''"""Tenant RLS proxy stub."""

from __future__ import annotations


def filter_rows(rows: list[dict], tenant_id: str) -> list[dict]:
    """TODO: returns all rows — filter by tenant_id."""
    return rows
''',
            reference_body='''"""Tenant RLS proxy reference."""

from __future__ import annotations


def filter_rows(rows: list[dict], tenant_id: str) -> list[dict]:
    return [r for r in rows if r.get("tenant_id") == tenant_id]
''',
            test_body='''"""Public tests for tenant_proxy."""

from src.tenant_proxy import filter_rows


def test_filters_tenant():
    rows = [{"tenant_id": "a", "v": 1}, {"tenant_id": "b", "v": 2}]
    assert filter_rows(rows, "a") == [{"tenant_id": "a", "v": 1}]
''',
        ),
    }
    if archetype not in catalog:
        return catalog[TechnicalArchetype.webhook_handler]
    return catalog[archetype]


def build_heuristic_spec(
    metadata: SanitizedMetadata,
    *,
    source_label: str = "",
    suggested_title: str = "",
    ingest_kind: IngestKind = IngestKind.behavioral_log,
    founder_override: TechnicalArchetype | None = None,
) -> TechnicalChallengeSpec:
    archetype = infer_archetype_from_metadata(metadata, founder_override=founder_override)
    names = _field_names(metadata)
    defaults = _defaults_for(archetype)
    title = suggested_title or defaults.pain_point[:60]
    data_plane = DataPlane.sqlite if archetype == TechnicalArchetype.data_core else DataPlane.none

    contract = InterfaceContract(
        primary_module=defaults.primary_module,
        support_modules=list(defaults.support_modules or []),
        entrypoint="main.py",
        public_api=list(defaults.public_api),
        invariants=list(defaults.invariants),
    )
    edit_targets = [defaults.primary_module]
    layout = StarterLayout(
        required_paths=["README.md", "docs/SPEC.md", "main.py", "tests/test_public.py"],
        edit_targets=edit_targets,
        student_may_add=["src/helpers/*.py"],
    )

    return TechnicalChallengeSpec(
        classification=SpecClassification(
            archetype=archetype,
            confidence=0.88 if names else 0.6,
            trigger_signals=_trigger_signals(archetype, names),
            recommended_data_plane=data_plane,
        ),
        title=title,
        startup_pain_point=defaults.pain_point,
        scenario=defaults.scenario_template,
        ingest_kind=ingest_kind,
        interface_contract=contract,
        definition_of_done=list(defaults.definition_of_done),
        assessor_signals=list(defaults.assessor_signals),
        data_plane=data_plane,
        fixtures={},
        starter_layout=layout,
        stack_guidance=["Python 3.11", "stdlib only"],
    )


def get_archetype_defaults(archetype: TechnicalArchetype) -> ArchetypeDefaults:
    return _defaults_for(normalize_archetype(archetype))
