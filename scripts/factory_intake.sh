#!/usr/bin/env bash
# Founder intake pipeline: problem brief → intake API → preview → publish → verify.
#
# Usage:
#   ./scripts/factory_intake.sh [base_url]
#
# Env:
#   PROBLEM="Your internal problem statement..."
#   SOURCE_LABEL="Founder brief label"
#   ARCHETYPE=integration|algorithm|service_module|...
#
# Requires: curl, jq. Backend at base_url (default http://localhost:8000).

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
ARCHETYPE="${ARCHETYPE:-integration}"
SOURCE_LABEL="${SOURCE_LABEL:-Founder brief — payment retries}"
PROBLEM="${PROBLEM:-Our payment webhook retries duplicate charges when Stripe returns 502. We need idempotent retry handling. Internal codename: NovaPay checkout v2.}"

pretty_json() { jq .; }

stage() {
  echo ""
  echo "============================================================"
  echo "==> $*"
  echo "============================================================"
}

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
RELAX_RESP=$(
  curl -sf -X POST "$BASE_URL/api/v1/triage/relax/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
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
          data_plane: "none"
        },
        reward: {
          reward_type: "cash_bounty",
          amount_usd: 500,
          interview_benchmark: 75,
          locked: true
        }
      }')"
)
echo "$RELAX_RESP" | pretty_json

echo ""
echo "--- Factory summary ---"
echo "$RELAX_RESP" | jq '{
  validation: .challenge_package.validation,
  starter_files: (.challenge_package.starter_files | keys),
  edit_targets: .challenge_package.blueprint.edit_targets,
  draft_title: .challenge_draft.title
}'

if [[ "$(echo "$RELAX_RESP" | jq -r '.challenge_package.validation.passed // false')" != "true" ]]; then
  echo "ERROR: validation failed" >&2
  exit 1
fi

stage "4/6 Publish"
curl -sf -X POST "$BASE_URL/api/v1/triage/publish/$ITEM_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "abstract_logic": true,
      "synthesize_variables": false,
      "noise_level": 0.0,
      "abstract_brand": true,
      "obfuscate_domain": false
    },
    "reward": {
      "reward_type": "cash_bounty",
      "amount_usd": 500,
      "interview_benchmark": 75,
      "locked": true
    }
  }' | pretty_json

stage "5/6 Verify student starter"
curl -sf "$BASE_URL/api/v1/sandbox/challenges/$ITEM_ID/starter" | jq '{
  ok,
  files: (.files | keys),
  readme_edit_targets: (.files["README.md"] | split("\n") | .[0:20])
}'

stage "Done"
echo "Published: $ITEM_ID"
echo "Student: http://localhost:3000/student/challenges/$ITEM_ID"
