#!/usr/bin/env bash
# Run factory pipeline for a specific archetype sample.
#
# Usage:
#   ./scripts/samples/run_archetype.sh <archetype> [mode] [base_url]
#
# Archetypes:
#   idempotency_engine, webhook_handler, data_core, data_adapter,
#   cli_instrumentation, data_masking, circuit_breaker, stream_parser,
#   rls_proxy, algorithm
#
# Modes:
#   log     — sanitize log → score → relax → publish (default)
#   intake  — founder brief → intake → relax → publish
#   preview — relax only (no publish); set via PREVIEW_ONLY=1 or mode=preview
#
# Examples:
#   ./scripts/samples/run_archetype.sh idempotency_engine
#   ./scripts/samples/run_archetype.sh data_core intake
#   PREVIEW_ONLY=1 ./scripts/samples/run_archetype.sh webhook_handler log
#   ./scripts/samples/run_archetype.sh algorithm log http://localhost:8000
#
# Env overrides: SOURCE_LABEL, ARCHETYPE (default auto; algorithm sample forces algorithm)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

ARCHETYPE_NAME="${1:?Usage: $0 <archetype> [log|intake|preview] [base_url]}"
MODE="${2:-log}"
BASE_URL="${3:-http://localhost:8000}"

if [[ "$MODE" == "http://"* ]] || [[ "$MODE" == "https://"* ]]; then
  BASE_URL="$MODE"
  MODE="log"
fi

case "$ARCHETYPE_NAME" in
  idempotency_engine|webhook_handler|data_core|data_adapter|cli_instrumentation|data_masking|circuit_breaker|stream_parser|rls_proxy|algorithm)
    ;;
  preview|log|intake)
    echo "ERROR: first argument must be an archetype name, not '$ARCHETYPE_NAME'" >&2
    exit 1
    ;;
  *)
    echo "ERROR: unknown archetype '$ARCHETYPE_NAME'" >&2
    echo "Valid: idempotency_engine webhook_handler data_core data_adapter cli_instrumentation data_masking circuit_breaker stream_parser rls_proxy algorithm" >&2
    exit 1
    ;;
esac

if [[ "$MODE" == "preview" ]]; then
  export PREVIEW_ONLY=1
  MODE="log"
fi

LOG_FILE="$SCRIPT_DIR/logs/${ARCHETYPE_NAME}.log"
BRIEF_FILE="$SCRIPT_DIR/briefs/${ARCHETYPE_NAME}.txt"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "ERROR: missing sample log: $LOG_FILE" >&2
  exit 1
fi
if [[ ! -f "$BRIEF_FILE" ]]; then
  echo "ERROR: missing sample brief: $BRIEF_FILE" >&2
  exit 1
fi

export SOURCE_LABEL="${SOURCE_LABEL:-Sample — $ARCHETYPE_NAME ($MODE)}"

if [[ "$ARCHETYPE_NAME" == "algorithm" ]]; then
  export ARCHETYPE="${ARCHETYPE:-algorithm}"
else
  export ARCHETYPE="${ARCHETYPE:-auto}"
fi

if [[ "$MODE" == "intake" ]]; then
  export PROBLEM="$(cat "$BRIEF_FILE")"
  exec "$ROOT_DIR/scripts/factory_intake.sh" "$BASE_URL"
fi

export LOG_CONTENT="$(cat "$LOG_FILE")"
exec "$ROOT_DIR/scripts/factory_pipeline.sh" "$BASE_URL"
