#!/usr/bin/env bash
# End-to-end dynamic challenge factory: sanitize → score → preview → publish → verify.
#
# Usage:
#   ./scripts/factory_pipeline.sh [base_url]
#
# Env overrides:
#   ARCHETYPE=algorithm|service_module|integration|data_adjacent|data_core
#   SOURCE_LABEL="My ingest label"
#
# Requires: curl, jq. Backend at base_url (default http://localhost:8000).

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
ARCHETYPE="${ARCHETYPE:-algorithm}"
SOURCE_LABEL="${SOURCE_LABEL:-Factory pipeline smoke test}"

pretty_json() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    python3 -m json.tool
  fi
}

stage() {
  echo ""
  echo "============================================================"
  echo "==> $*"
  echo "============================================================"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: '$1' is required but not installed." >&2
    exit 1
  fi
}

require_cmd curl
require_cmd jq

stage "0/7 Health check — $BASE_URL"
curl -sf "$BASE_URL/" | pretty_json

stage "1/7 Sanitize raw log (privacy proxy)"
SANITIZE_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/proxy/sanitize" \
    -H "Content-Type: application/json" \
    -d '{
      "content": "2024-03-12 ERROR payment retry_count=3 idempotency_key=abc-123 gateway_response_code=502 amount_cents=499 processor_name=stripe",
      "format": "log"
    }'
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
RELAX_BODY=$(
  jq -n \
    --arg archetype "$ARCHETYPE" \
    '{
      config: {
        abstract_logic: true,
        synthesize_variables: false,
        noise_level: 0.0,
        abstract_brand: true,
        obfuscate_domain: false
      },
      blueprint: {
        archetype: $archetype,
        primary_focus: "Implement the core module and pass public tests",
        data_plane: "none",
        stack_guidance: ["Python 3.11"],
        starter_hints: "Focus on the main src/ edit target named in README.md"
      },
      reward: {
        reward_type: "cash_bounty",
        amount_usd: 500,
        interview_benchmark: 75,
        locked: true
      }
    }'
)
RELAX_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/triage/relax/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -d "$RELAX_BODY"
)
echo "$RELAX_RESP" | pretty_json

echo ""
echo "--- Factory summary ---"
echo "$RELAX_RESP" | jq '{
  blueprint: .challenge_blueprint,
  validation: .challenge_package.validation,
  starter_files: (.challenge_package.starter_files | keys),
  draft_title: .challenge_draft.title
}'

VALIDATION_PASSED=$(echo "$RELAX_RESP" | jq -r '.challenge_package.validation.passed // false')
if [[ "$VALIDATION_PASSED" != "true" ]]; then
  echo ""
  echo "ERROR: challenge_package.validation.passed is not true — fix before publish." >&2
  echo "$RELAX_RESP" | jq '.challenge_package.validation.errors // []' >&2
  exit 1
fi

stage "5/7 Publish"
PUBLISH_BODY=$(
  jq -n '{
    config: {
      abstract_logic: true,
      synthesize_variables: false,
      noise_level: 0.0,
      abstract_brand: true,
      obfuscate_domain: false
    },
    reward: {
      reward_type: "cash_bounty",
      amount_usd: 500,
      interview_benchmark: 75,
      locked: true
    }
  }'
)
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
