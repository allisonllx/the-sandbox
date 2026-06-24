#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# --- Commands — update these once the project directories are initialised ---
# Backend (Python / FastAPI)
BACKEND_INSTALL_CMD=(pip install -r backend/requirements.txt)
BACKEND_VERIFY_CMD=(python -m pytest backend/tests -q)

# Frontend (Next.js)
FRONTEND_INSTALL_CMD=(npm --prefix frontend install)
FRONTEND_VERIFY_CMD=(npm --prefix frontend run typecheck)

START_CMD=(python -m uvicorn backend.main:app --reload --port 8000)

echo "==> Working directory: $PWD"

if [ -f backend/requirements.txt ]; then
  echo "==> Installing backend dependencies"
  "${BACKEND_INSTALL_CMD[@]}"

  echo "==> Running backend verification"
  "${BACKEND_VERIFY_CMD[@]}"
else
  echo "==> Skipping backend — backend/requirements.txt not found yet"
fi

if [ -f frontend/package.json ]; then
  echo "==> Installing frontend dependencies"
  "${FRONTEND_INSTALL_CMD[@]}"

  echo "==> Running frontend type check"
  "${FRONTEND_VERIFY_CMD[@]}"
else
  echo "==> Skipping frontend — frontend/package.json not found yet"
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  if docker image inspect the-sandbox-runner:latest >/dev/null 2>&1; then
    echo "==> Assessor Docker image the-sandbox-runner:latest already present"
  elif [ -f docker/sandbox-runner/Dockerfile ]; then
    echo "==> Building assessor Docker image the-sandbox-runner:latest"
    docker build -t the-sandbox-runner:latest docker/sandbox-runner
  fi
else
  echo "==> Skipping assessor Docker image — Docker daemon not available (submit grading uses degraded mode)"
fi

echo "==> Startup command"
printf '    %q' "${START_CMD[@]}"
printf '\n'

if [ "${RUN_START_COMMAND:-0}" = "1" ]; then
  echo "==> Starting the app"
  exec "${START_CMD[@]}"
fi

echo "Set RUN_START_COMMAND=1 if you want init.sh to launch the app directly."
