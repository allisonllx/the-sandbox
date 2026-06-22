# Archetype sample scripts

End-to-end factory smoke tests — one sample per **TechnicalChallengeSpec** archetype.

Requires backend on `http://localhost:8000` and `jq`.

## Quick start

```bash
# Log ingest → auto-classify → publish (full pipeline)
./scripts/samples/run_archetype.sh idempotency_engine

# Founder brief path (same archetype)
./scripts/samples/run_archetype.sh idempotency_engine intake

# Preview only — no publish (fast loop)
PREVIEW_ONLY=1 ./scripts/samples/run_archetype.sh webhook_handler

# All archetypes, preview only
./scripts/samples/run_all_previews.sh
```

## Archetypes and trigger signals

| Script name | Auto-detect signals (in sample log/brief) | Primary module |
|---|---|---|
| `idempotency_engine` | `idempotency_key`, `retry_count`, `gateway_response_code` | `src/idempotency_store.py` |
| `webhook_handler` | `retry_count`, `gateway_response_code` (no idempotency_key) | `src/webhook_engine.py` |
| `data_core` | `query_hash`, `execution_time_ms`, `table_name`, `rows_scanned` | `src/queries.py` (+ SQLite) |
| `data_adapter` | `source_system`, `target_schema`, `connector`, `sync_status` | `src/adapter.py` |
| `cli_instrumentation` | `latency_ms`, `token_count`, `command`, `cli_duration_ms` | `src/cli_metrics.py` |
| `data_masking` | `email`, `user_id`, `pii`, `phone` | `src/masker.py` |
| `circuit_breaker` | `timeout_ms`, `failure_rate`, `circuit_state`, `downstream_status` | `src/circuit_breaker.py` |
| `stream_parser` | `file_size_bytes`, `chunk_count`, `oom`, `memory_mb` | `src/stream_parser.py` |
| `rls_proxy` | `tenant_id`, `org_id`, `account_id` | `src/tenant_proxy.py` |
| `algorithm` | **Founder override only** — forces `ARCHETYPE=algorithm` | `src/solution.py` |

## Sample data

| Path | Contents |
|---|---|
| [`logs/`](logs/) | Structured log lines with `key=value` fields for sanitize → score |
| [`briefs/`](briefs/) | Founder problem statements with embedded telemetry excerpts |

## Overrides

| Env | Effect |
|---|---|
| `ARCHETYPE=auto` | Let ingest signals choose (default for all except `algorithm`) |
| `ARCHETYPE=algorithm` | Force clamp_values scaffold (used by `algorithm` sample) |
| `SOURCE_LABEL=...` | Backlog label |
| `PREVIEW_ONLY=1` | Stop after relax |
| `LOG_CONTENT=...` | Override log text in `factory_pipeline.sh` |
| `PROBLEM=...` | Override brief in `factory_intake.sh` |

See [`../DOCS.md`](../DOCS.md) for the base factory scripts.
