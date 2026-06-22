#!/usr/bin/env bash
# End-to-end dynamic challenge factory: sanitize → score → preview → publish → verify.
#
# Usage:
#   ./scripts/factory_pipeline.sh [base_url]
#
# Env overrides:
#   LOG_CONTENT="raw log text"     — default: payment-retry sample
#   ARCHETYPE=auto|webhook_handler|idempotency_engine|...
#   SOURCE_LABEL="My ingest label"
#   PREVIEW_ONLY=1               — stop after relax (no publish)
#
# Archetype samples: ./scripts/samples/run_archetype.sh <name> [log|intake]
#
# Requires: curl, jq. Backend at base_url (default http://localhost:8000).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=factory_common.sh
source "$SCRIPT_DIR/factory_common.sh"

BASE_URL="${1:-http://localhost:8000}"
ARCHETYPE="${ARCHETYPE:-auto}"
SOURCE_LABEL="${SOURCE_LABEL:-Factory pipeline smoke test}"
PREVIEW_ONLY="${PREVIEW_ONLY:-0}"

DEFAULT_LOG='2024-03-12 ERROR payment retry_count=3 idempotency_key=abc-123 gateway_response_code=502 amount_cents=499 processor_name=stripe'
LOG_CONTENT="${LOG_CONTENT:-$DEFAULT_LOG}"

pretty_json() { factory_pretty_json; }
stage() { factory_stage "$@"; }
require_cmd() { factory_require_cmd "$@"; }

require_cmd curl
require_cmd jq

stage "0/7 Health check — $BASE_URL"
curl -sf "$BASE_URL/" | pretty_json

stage "1/7 Sanitize raw log (privacy proxy)"
SANITIZE_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/proxy/sanitize" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg content "$LOG_CONTENT" '{content: $content, format: "log"}')"
)
echo "$SANITIZE_RESP" | pretty_json

stage "2/7 Score — add to backlog"
SCORE_BODY=$(
  echo "$SANITIZE_RESP" | jq -c '{metadata: .metadata, source_label: $label}' --arg label "$SOURCE_LABEL"
)
SCORE_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/triage/score" \
    -H "Content-Type: application/json" \
    -d "$SCORE_BODY"
)
echo "$SCORE_RESP" | pretty_json

ITEM_ID=$(echo "$SCORE_RESP" | jq -r '.item_id')
echo ""
echo "ITEM_ID=$ITEM_ID"

stage "3/7 Scope check"
curl -sf "$BASE_URL/api/v1/triage/backlog/$ITEM_ID/scope" | pretty_json

stage "4/7 Preview (relax) — generate Micro-PRD + starter files"
RELAX_BODY="$(factory_build_relax_body)"
RELAX_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/triage/relax/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -d "$RELAX_BODY"
)
echo "$RELAX_RESP" | pretty_json

factory_print_summary "$RELAX_RESP"
factory_assert_validation "$RELAX_RESP"

if [[ "$PREVIEW_ONLY" == "1" ]]; then
  stage "Done (preview only)"
  echo "ITEM_ID=$ITEM_ID"
  echo "Set PREVIEW_ONLY=0 to publish, or: curl -X POST $BASE_URL/api/v1/triage/publish/$ITEM_ID ..."
  exit 0
fi

stage "5/7 Publish"
PUBLISH_BODY="$(factory_build_publish_body)"
PUBLISH_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/triage/publish/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -d "$PUBLISH_BODY"
)
echo "$PUBLISH_RESP" | pretty_json

stage "6/7 Verify — public challenge + starter (student API)"
echo "--- Challenge card ---"
curl -sf "$BASE_URL/api/v1/sandbox/challenges/$ITEM_ID" | jq '{
  id,
  title,
  track,
  starter_ready,
  dataset_ready,
  microprd_title: .microprd.title
}'

echo ""
echo "--- Starter file tree ---"
curl -sf "$BASE_URL/api/v1/sandbox/challenges/$ITEM_ID/starter" | jq '{
  ok,
  challenge_id,
  files: (.files | keys)
}'

echo ""
echo "--- README.md (first 40 lines) ---"
curl -sf "$BASE_URL/api/v1/sandbox/challenges/$ITEM_ID/starter" | jq -r '.files["README.md"] // "(no README.md)"' | head -40

stage "Done"
echo "Challenge published: $ITEM_ID"
echo "Student workspace: http://localhost:3000/student/challenges/$ITEM_ID  (if frontend is running)"
echo "OpenAPI: $BASE_URL/docs"
