# Architecture

## Overview

The Sandbox is a two-sided, zero-trust R&D and proof-of-work talent platform organized as an **Innovation Hub** with pluggable **innovation tracks**. Growth-stage startups connect internal feedback/log channels to a local privacy proxy that scrubs PII and extracts structural metadata without ever sending raw data externally. The AI PM layer triages the backlog, routes items to a track (Technical or Product Feature for MVP), applies brand abstraction, and lets founders publish de-risked challenges. Students solve track-specific workspaces; submissions are graded by **track-aware assessor plugins**.

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
│   ├── ai_pm/                # Triage matrix, track router, Micro-PRD generator, relaxation
│   ├── assessor/             # Pluggable per-track assessor plugins (technical, product)
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
│   ├── PRODUCT.md            # Non-technical product overview
│   └── documentation-sync.md # Code path → doc update map
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
ai_pm/track_router.py  (heuristic track suggestion + brand_proxy)
  │
  ▼
ai_pm/relaxation.py  (founder applies controls in the UI)
  ├─ Abstract proprietary logic toggle
  ├─ Variable-name synthesizer
  ├─ Statistical noise slider (0–100%)
  └─ Brand abstraction (company tokens → brand_proxy)
  │
  ▼
ai_pm/microprd.py  ──► Track-aware Micro-PRD
  ├─ Technical: Context, Success, Constraints, Instructions
  └─ Product Feature: + persona, problem framing, design considerations, deliverables
  │
  ▼
Publish branch by track:
  ├─ technical → synthesizer.py (SQLite + anomalies) + starter_scaffold.py
  └─ product_feature → product_starter_scaffold.py (HTML/CSS/JS + DESIGN.md)
  │
  ▼
[Challenge published to public Innovation Hub]
```

### 2. Student Submission → Scorecard (track-aware)

```
[Student browser]
Innovation Hub browse (track filter tabs)
  │
  ├─ technical → ChallengeWorkspace (Monaco Python) → Run public tests → Submit
  └─ product_feature → ProductWorkspace (Monaco prototype + link fields) → Submit
  │
  ▼
assessor/registry.py
  ├─ TechnicalAssessor — preflight + structure stub (Docker harness in assessor-001)
  └─ ProductAssessor — DESIGN.md rubric + prototype structure checks
  │
  ▼
Scorecard rendered in browser
  ├─ Technical: Performance · Security Resilience · Architectural Elegance
  └─ Product: Product Thinking · UX & IA · Implementation · Communication
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
