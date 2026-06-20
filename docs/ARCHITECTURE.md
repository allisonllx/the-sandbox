# Architecture

## Overview

The Sandbox is a two-sided, zero-trust R&D and proof-of-work talent platform. Growth-stage startups connect their internal feedback/log channels to a local privacy proxy that scrubs PII and extracts structural metadata without ever sending raw data externally. That sanitized metadata is processed by an AI Product Manager layer that triages the backlog and lets founders publish de-risked coding challenges. Students solve those challenges inside an interactive browser terminal using synthetically generated datasets, and their submissions are graded automatically by an AI Assessor that evaluates both correctness and code taste.

## Tech Stack

- **Backend:** Python 3.11+ · FastAPI · Pydantic
- **Privacy Proxy:** Python · spaCy (local NER) · regex · runs fully offline
- **Frontend:** Next.js 14 · TypeScript · Tailwind CSS
- **Database:** PostgreSQL (platform data) · SQLite (per-challenge synthetic datasets)
- **AI / LLM:** OpenAI API or Anthropic API — receives anonymized structural metadata only
- **Code Runner:** Docker (ephemeral containers, no network, resource-limited)
- **Infra / Build:** Docker Compose (local dev) · to be confirmed for cloud deployment

## Directory Structure

```
the_sandbox/
├── backend/                  # FastAPI application
│   ├── privacy_proxy/        # Local sanitization engine (runs offline)
│   ├── ai_pm/                # Triage matrix, Micro-PRD generator, noise synthesizer
│   ├── assessor/             # Code runner orchestration, LLM taste evaluator
│   ├── api/                  # REST route definitions
│   ├── tests/                # pytest test suite
│   └── requirements.txt
├── frontend/                 # Next.js application
│   ├── app/                  # App Router pages
│   │   ├── startup/          # CTO dashboard: triage matrix + relaxation controls
│   │   └── student/          # Challenge browser + sandbox terminal + scorecard
│   ├── components/
│   └── package.json
├── docker/                   # Dockerfiles for ephemeral code-runner containers
├── docs/                     # Project documentation
│   ├── api-patterns.md       # API design patterns
│   ├── ARCHITECTURE.md       # This file
│   └── PRODUCT.md            # Non-technical product overview
├── AGENTS.md                 # Agent operating rules (read this first every session)
├── feature_list.json         # Authoritative feature state tracker
├── claude-progress.md        # Session log and current verified state
├── init.sh                   # Standard startup and verification script
├── session-handoff.md        # Compact handoff template for cross-session continuity
├── clean-state-checklist.md  # End-of-session checklist
└── evaluator-rubric.md       # Acceptance rubric for implemented features
```

## Key Data Flows

### 1. Startup Ingest → Public Challenge

```
[Startup local process]
Raw log / feedback text (Slack export, Intercom CSV, error logs)
  │
  ▼
privacy_proxy/sanitizer.py
  ├─ Regex PII masking (email, phone, API key, JWT)
  ├─ Local NER pass (names, org identifiers)
  └─ Structural metadata extraction (field names, types, frequencies)
  │
  ▼  [only anonymized metadata crosses this boundary]
ai_pm/triage.py  ──► LLM API (structural metadata only)
  ├─ Severity / Friction / Sensitivity scoring
  └─ Red / Yellow / Green sensitivity tag
  │
  ▼
ai_pm/relaxation.py  (founder applies controls in the UI)
  ├─ Abstract proprietary logic toggle
  ├─ Variable-name synthesizer
  └─ Statistical noise slider (0–100%)
  │
  ▼
ai_pm/microprd.py  ──► Micro-PRD (Context, Success, Constraints, Instructions)
ai_pm/synthesizer.py  ──► Synthetic SQLite dataset with injected anomalies
  │
  ▼
[Challenge published to public sandbox]
```

### 2. Student Submission → Scorecard

```
[Student browser]
Interactive terminal → code submission
  │
  ▼
assessor/runner.py
  └─ Spins up ephemeral Docker container (no network, memory + CPU caps)
     Runs solution against secret edge-case tests
  │
  ▼
assessor/taste_evaluator.py  ──► LLM API
  └─ Evaluates: error handling, architectural simplicity, optimization efficiency
  │
  ▼
Scorecard rendered in browser (Performance · Security Resilience · Architectural Elegance)
  │
  ▼
[Top profiles surfaced to sponsoring company CTO dashboard]
```

## External Dependencies

| Service | Purpose | Data sent |
|---|---|---|
| OpenAI / Anthropic API | Triage scoring, Micro-PRD generation, taste evaluation | Anonymized structural metadata and code submissions only |
| Docker (local/cloud) | Ephemeral code execution sandbox | Student code only, no corporate data |
| PostgreSQL | Platform state (users, challenges, scores) | No raw startup data |

## Known Constraints

- The privacy proxy is the system's critical security boundary. No code path may bypass it to send raw startup data externally. Any refactor touching `privacy_proxy/` must be reviewed against the zero-trust constraint in `AGENTS.md`.
- Student code execution containers must have `--network none` and hard resource limits (`--memory 256m --cpus 0.5` or equivalent). Never relax these without explicit approval.
- The LLM taste evaluator receives the student's code submission. Confirm this does not transitively contain any startup metadata before wiring up the assessor.
- Tech stack choices above are proposed based on the PRD. Confirm before writing `backend/requirements.txt` or `frontend/package.json`.
