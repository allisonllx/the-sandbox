# Architecture

## Overview

The Sandbox is a two-sided, zero-trust R&D and proof-of-work talent platform organized as an **Innovation Hub** with pluggable **innovation tracks**. Growth-stage startups connect internal feedback/log channels to a local privacy proxy that scrubs PII and extracts structural metadata without ever sending raw data externally. The AI PM layer triages the backlog, routes items to a track (Technical or Product Feature for MVP), applies relaxation and blind-audition controls, and lets founders **edit the student release preview** before publish. Students solve track-specific workspaces; submissions are graded by **track-aware assessor plugins**.

## Tech Stack

- **Backend:** Python 3.11+ · FastAPI · Pydantic v2
- **Privacy Proxy:** Python · spaCy (local NER) · regex · runs fully offline
- **Frontend:** Next.js 14 · TypeScript · Tailwind CSS · Monaco editor
- **Persistence (MVP):** In-memory backlog · file-backed drafts/submissions/jobs under `data/`
- **Datasets:** SQLite per challenge (technical track only)
- **AI / LLM:** Local vLLM (OpenAI-compatible) for **sensitive** tier by default; OpenAI cloud for **standard** tier and optional sensitive fallback (`LLM_ALLOW_CLOUD_SENSITIVE`). Receives anonymized structural metadata only for triage/Micro-PRD; never raw PII.
- **Code Runner:** Public tests in-process (student Run button); assessor secret tests in Docker (`assessor-001 Phase A`)

## Directory Structure

```
the_sandbox/
├── backend/
│   ├── privacy_proxy/        # Local sanitization engine (offline)
│   ├── ai_pm/                # Triage, track router, relaxation, blind audition, Micro-PRD
│   │   ├── company_profile.py
│   │   ├── domain_obfuscator.py
│   │   ├── public_sanitize.py
│   │   └── publish_draft.py
│   ├── challenge_factory/    # Blueprint-driven starter generation at Preview
│   ├── assessor/             # Dual-layer platform signal + sponsor fit
│   ├── sandbox/              # Datasets, submissions, rank stubs
│   │   ├── leaderboard.py          # Student global rank (demo)
│   │   ├── sponsor_matches.py      # Per-challenge match radar (startup)
│   │   └── enterprise_radar.py     # Platform-wide top tier (enterprise)
│   ├── api/                  # REST route definitions
│   └── tests/
├── frontend/
│   ├── app/startup/          # CTO dashboard, /startup/upload, /startup/matches/[id]
│   ├── app/student/          # Innovation Hub, workspace, leaderboard, trust
│   └── app/enterprise/radar/ # Enterprise subscription view (demo)
├── scripts/                  # factory_intake.sh, factory_pipeline.sh
├── docs/
├── feature_list.json
├── claude-progress.md
└── init.sh
```

## Trust Boundaries

### Internal (CTO dashboard only)

- `source_label`, `sponsor_profile`, `brand_proxy`
- Raw `evaluation_focus` before public sanitization
- Domain obfuscation before/after preview (`domain_preview`)

### Public student API (`sandbox_routes._to_public`)

- **Never** returns `brand_proxy` or `sponsor_profile`
- Returns `CompanyTechProfile` (blind audition)
- Micro-PRD and evaluation focus passed through `public_sanitize.py`
- Red-sensitivity items omit `industry_broad` on company profile

## Key Data Flows

### 1. Startup Ingest → Public Challenge

```
[Startup — three ingest surfaces]
  /startup/upload          → sanitize → score → backlog (loading UI shows each step)
  /startup sidebar intake  → POST /triage/intake (sanitize + score in one call)
  API / scripts            → POST /proxy/sanitize + POST /triage/score

Raw log / feedback / founder brief text
  │
  ▼
privacy_proxy/sanitizer.py  →  SanitizedMetadata (PII stripped locally)
  │
  ▼  [only metadata crosses boundary]
ai_pm/scorer.py + track_router.py  →  Severity / Friction / Sensitivity + track suggestion
  │
  ▼
ai_pm/relaxation.py + domain_obfuscator.py (optional)
  ├─ Field relaxation, noise, domain column renames
  └─ Domain narrative transform (CTO preview)
  │
  ▼
POST /triage/relax/{id}
  ├─ Returns relaxed field preview + challenge_draft (PublishDraft)
  ├─ Non-demo technical: challenge_factory.build_package() → challenge_package + validation
  └─ Founder edits title, context, blueprint (archetype, stack hints), company profile in UI
  │
  ▼
POST /triage/regenerate/{id}  (optional — after draft/blueprint edits)
  └─ Re-runs challenge_factory; marks stale until validation passes
  │
  ▼
POST /triage/publish/{id}  (requires locked reward + scope guard pass)
  ├─ Applies founder PublishDraft overrides
  ├─ Non-demo technical: requires valid non-stale challenge_package (no generation at publish)
  ├─ Legacy demo-* / product track: hardcoded starter_scaffold / synthesizer at publish
  ├─ Generates track-aware Micro-PRD
  ├─ company_profile.py → CompanyTechProfile on BacklogItem
  └─ Branch: technical → Python starter (+ SQLite if data_plane) | product → frontend starter
  │
  ▼
GET /sandbox/challenges/{id}  →  public_sanitize.build_public_challenge()
```

### 2. Student Submission → Scorecard

```
Student workspace → submit → assessor/registry.py
  ├─ platform_* assessor → platform_signal_score → execution_points (global rank)
  └─ sponsor_* assessor → sponsor_fit_score (Match Radar only)
  │
  ▼
Dual-layer scorecard in browser (+ interview pass when both layers ≥ benchmark)
```

### 3. Three Rank Surfaces (demo stubs)

| Audience | Route | API | Scope |
|---|---|---|---|
| **Students** | `/student/leaderboard` | `GET /sandbox/leaderboard` | Global platform Execution Points |
| **Startup sponsors** | `/startup/matches/{id}` | `GET /triage/backlog/{id}/matches` | **Sponsor Fit** for this challenge only |
| **Enterprises** | `/enterprise/radar` | `GET /sandbox/enterprise/radar` | Platform-wide top tier (platform signal) |

Startups do **not** see the student global leaderboard or other sponsors' challenge performers.

## External Dependencies

| Service | Purpose | Data sent |
|---|---|---|
| Local vLLM (Qwen) | Triage, domain obfuscation, sponsor fit (**sensitive** tier) | Anonymized structural metadata + sanitized challenge context — stays on-prem when `LLM_BASE_URL` set |
| OpenAI API | **Standard** tier; optional cloud fallback for sensitive | Anonymized structural metadata only (sensitive cloud blocked unless `LLM_ALLOW_CLOUD_SENSITIVE=1`) |
| Docker | Ephemeral assessor containers (network disabled) | Student submission code only |

## Known Constraints

- Privacy proxy is the critical security boundary — see `AGENTS.md`
- Public **Run** uses in-process pytest (student feedback loop); **submit grading** uses Docker secret tests for platform signal
- Backlog and rank data are in-memory / demo seed — no PostgreSQL or auth yet
