#!/usr/bin/env bash
# Preview-only smoke: run relax for every archetype sample (no publish).
# Useful for quick validation after factory changes.
#
# Usage: ./scripts/samples/run_all_previews.sh [base_url]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_URL="${1:-http://localhost:8000}"

ARCHETYPES=(
  idempotency_engine
  webhook_handler
  data_core
  data_adapter
  cli_instrumentation
  data_masking
  circuit_breaker
  stream_parser
  rls_proxy
  algorithm
)

FAIL=0
for archetype in "${ARCHETYPES[@]}"; do
  echo ""
  echo "############################################"
  echo "# PREVIEW: $archetype"
  echo "############################################"
  if ! PREVIEW_ONLY=1 "$SCRIPT_DIR/run_archetype.sh" "$archetype" log "$BASE_URL"; then
    echo "FAILED: $archetype" >&2
    FAIL=$((FAIL + 1))
  fi
done

echo ""
if [[ "$FAIL" -eq 0 ]]; then
  echo "All ${#ARCHETYPES[@]} archetype previews passed."
else
  echo "$FAIL / ${#ARCHETYPES[@]} archetype previews failed." >&2
  exit 1
fi
