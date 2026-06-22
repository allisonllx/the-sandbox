# Shared helpers for factory pipeline scripts.
# Source from factory_pipeline.sh / factory_intake.sh — do not execute directly.

factory_pretty_json() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    python3 -m json.tool
  fi
}

factory_stage() {
  echo ""
  echo "============================================================"
  echo "==> $*"
  echo "============================================================"
}

factory_require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: '$1' is required but not installed." >&2
    exit 1
  fi
}

# Relax request body — omit blueprint when ARCHETYPE=auto.
# Set TRACK=technical|product_feature to force innovation track (intake samples use technical).
factory_build_relax_body() {
  local archetype="${ARCHETYPE:-auto}"
  local track="${TRACK:-}"
  if [[ "$archetype" == "auto" && -z "$track" ]]; then
    jq -n \
      '{
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
  elif [[ "$archetype" == "auto" ]]; then
    jq -n \
      --arg track "$track" \
      '{
        config: {
          abstract_logic: true,
          synthesize_variables: false,
          noise_level: 0.0,
          abstract_brand: true,
          obfuscate_domain: false
        },
        track: $track,
        reward: {
          reward_type: "cash_bounty",
          amount_usd: 500,
          interview_benchmark: 75,
          locked: true
        }
      }'
  elif [[ -z "$track" ]]; then
    jq -n \
      --arg archetype "$archetype" \
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
  else
    jq -n \
      --arg archetype "$archetype" \
      --arg track "$track" \
      '{
        config: {
          abstract_logic: true,
          synthesize_variables: false,
          noise_level: 0.0,
          abstract_brand: true,
          obfuscate_domain: false
        },
        track: $track,
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
  fi
}

factory_build_publish_body() {
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
}

factory_print_summary() {
  local relax_resp="$1"
  echo ""
  echo "--- Factory summary ---"
  echo "$relax_resp" | jq '{
    archetype: (.challenge_spec.classification.archetype // .challenge_blueprint.archetype // null),
    confidence: (.challenge_spec.classification.confidence // null),
    trigger_signals: (.challenge_spec.classification.trigger_signals // []),
    challenge_package_present: (.challenge_package != null),
    validation: (.challenge_package.validation // null),
    starter_files: ((.challenge_package.starter_files // {}) | keys),
    edit_targets: (.challenge_package.blueprint.edit_targets // .challenge_blueprint.edit_targets // []),
    draft_title: (.challenge_draft.title // null),
    spec_title: (.challenge_spec.title // null),
    note: (if .challenge_package == null then "No dynamic package (product track or legacy item — factory package not generated at preview)" else null end)
  }'
}

factory_assert_validation() {
  local relax_resp="$1"
  if [[ "$(echo "$relax_resp" | jq -r '.challenge_package != null')" != "true" ]]; then
    echo ""
    echo "NOTE: challenge_package is null — skipping factory validation (product/legacy path)." >&2
    return 0
  fi
  if [[ "$(echo "$relax_resp" | jq -r '.challenge_package.validation.passed // false')" != "true" ]]; then
    echo ""
    echo "ERROR: challenge_package.validation.passed is not true." >&2
    echo "$relax_resp" | jq '.challenge_package.validation.errors // []' >&2
    exit 1
  fi
}
