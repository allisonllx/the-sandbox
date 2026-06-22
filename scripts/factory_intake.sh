#!/usr/bin/env bash
# Founder intake pipeline: problem brief → intake API → preview → publish → verify.
#
# Usage:
#   ./scripts/factory_intake.sh [base_url]
#
# Env:
#   PROBLEM="Your internal problem statement..."
#   SOURCE_LABEL="Founder brief label"
#   ARCHETYPE=auto|algorithm|webhook_handler|...
#   PREVIEW_ONLY=1               — stop after relax (no publish)
#
# Archetype samples: ./scripts/samples/run_archetype.sh <name> intake
#
# Requires: curl, jq. Backend at base_url (default http://localhost:8000).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=factory_common.sh
source "$SCRIPT_DIR/factory_common.sh"

BASE_URL="${1:-http://localhost:8000}"
ARCHETYPE="${ARCHETYPE:-auto}"
SOURCE_LABEL="${SOURCE_LABEL:-Founder brief — payment retries}"
PREVIEW_ONLY="${PREVIEW_ONLY:-0}"
PROBLEM="${PROBLEM:-Our payment webhook retries duplicate charges when Stripe returns 502. We need idempotent retry handling. Sample: retry_count=3 idempotency_key=abc-123 gateway_response_code=502. Internal codename: NovaPay checkout v2.}"

pretty_json() { factory_pretty_json; }
stage() { factory_stage "$@"; }

require_cmd() { factory_require_cmd "$@"; }
require_cmd curl
require_cmd jq

stage "0/6 Health check — $BASE_URL"
curl -sf "$BASE_URL/" | pretty_json

stage "1/6 Founder intake (local sanitize + sensitivity score)"
INTAKE_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/triage/intake" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
      --arg problem "$PROBLEM" \
      --arg label "$SOURCE_LABEL" \
      '{problem_statement: $problem, source_label: $label, format: "text"}')"
)
echo "$INTAKE_RESP" | pretty_json

ITEM_ID=$(echo "$INTAKE_RESP" | jq -r '.item_id')
echo ""
echo "ITEM_ID=$ITEM_ID"
echo "--- Sensitivity ---"
echo "$INTAKE_RESP" | jq '{tag, scores: {severity, friction, sensitivity}, suggested_track, pii_types_stripped}'

stage "2/6 Scope check"
curl -sf "$BASE_URL/api/v1/triage/backlog/$ITEM_ID/scope" | pretty_json

stage "3/6 Preview (Micro-PRD + starter factory)"
RELAX_JSON="$(factory_build_relax_body)"
RELAX_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/triage/relax/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -d "$RELAX_JSON"
)
echo "$RELAX_RESP" | pretty_json

factory_print_summary "$RELAX_RESP"
factory_assert_validation "$RELAX_RESP"

if [[ "$PREVIEW_ONLY" == "1" ]]; then
  stage "Done (preview only)"
  echo "ITEM_ID=$ITEM_ID"
  exit 0
fi

stage "4/6 Publish"
curl -sf -X POST "$BASE_URL/api/v1/triage/publish/$ITEM_ID" \
  -H "Content-Type: application/json" \
  -d "$(factory_build_publish_body)" | pretty_json

stage "5/6 Verify student starter"
curl -sf "$BASE_URL/api/v1/sandbox/challenges/$ITEM_ID/starter" | jq '{
  ok,
  files: (.files | keys),
  readme_edit_targets: (.files["README.md"] | split("\n") | .[0:20])
}'

stage "Done"
echo "Published: $ITEM_ID"
echo "Student: http://localhost:3000/student/challenges/$ITEM_ID"
