#!/usr/bin/env bash
# Publish a demo challenge, then submit the matching sample solution.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHALLENGE_ID="${1:?Usage: test_sample.sh demo-003 [base_url]}"
BASE_URL="${2:-http://localhost:8000}"

echo "==> Publishing ${CHALLENGE_ID}"
python3 "${ROOT}/publish_sample.py" "${CHALLENGE_ID}" "${BASE_URL}"

echo ""
echo "==> Submitting sample from samples/demo_solutions/${CHALLENGE_ID}/"
python3 "${ROOT}/submit_sample.py" "${CHALLENGE_ID}" "${BASE_URL}"
