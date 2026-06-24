# Architecture

## Overview

The Sandbox is a two-sided, zero-trust R&D and proof-of-work talent platform organized as an **Innovation Hub** with pluggable **innovation tracks**. Growth-stage startups connect internal feedback/log channels to a local privacy proxy that scrubs PII and extracts structural metadata without ever sending raw data externally. The AI PM layer triages the backlog, routes items to a track (Technical or Product Feature for MVP), applies relaxation and blind-audition controls, and lets founders **edit the student release preview** before publish. Students solve track-specific workspaces; submissions are graded by **track-aware assessor plugins**.

## Tech Stack

- **Backend:** Python 3.11+ · FastAPI · Pydantic v2
- **Privacy Proxy:** Python · spaCy (local NER) · regex · runs fully offline
- **Frontend:** Next.js 14 · TypeScript · Tailwind CSS · Monaco editor
- **Persistence (MVP):** Local filesystem under `data/` · in-memory backlog — **no application database** (see [Persistence](#persistence-hackathon-mvp))
- **Datasets:** SQLite per challenge (technical track only) — synthetic fixtures in `backend/generated_datasets/`, not the app DB
- **AI / LLM:** OpenAI cloud **default for dev/demo** (`OPENAI_API_KEY`); optional local vLLM (Qwen) for privacy-first sensitive tier (`LLM_BASE_URL` + `LLM_ALLOW_CLOUD_SENSITIVE=0`). Receives anonymized structural metadata only for triage/Micro-PRD; never raw PII.
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
│   ├── challenge_factory/    # TechnicalChallengeSpec → dynamic starter at Preview
│   │   ├── challenge_spec.py       # Single-pass spec inference
│   │   ├── scaffold_interpolate.py # Stubs/tests from interface_contract
│   │   └── spec_projection.py      # spec_to_microprd, format_spec_context, SpecExample projection
│   ├── assessor/             # Dual-layer platform signal + sponsor fit
│   ├── sandbox/              # Datasets, submissions, rank stubs
│   │   ├── leaderboard.py          # Student global rank (demo)
│   │   ├── sponsor_matches.py      # Per-challenge match radar (startup)
│   │   └── enterprise_radar.py     # Platform-wide top tier (enterprise)
│   ├── api/                  # REST route definitions
│   └── tests/
├── frontend/
│   ├── app/startup/          # CTO dashboard (triage/live/closed sidebar), upload, matches/[id]
│   ├── app/student/          # Innovation Hub, workspace, leaderboard, trust
│   ├── components/           # BriefMarkdown, BriefSectionBody (student brief rendering)
│   └── app/enterprise/radar/ # Enterprise subscription view (demo)
├── scripts/                  # factory_*.sh + samples/run_archetype.sh (per-archetype smokes)
├── data/                     # Server-side durable state (drafts, submissions, jobs) — gitignored
│   ├── drafts/
│   ├── submissions/
│   └── jobs/
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

## Persistence (hackathon MVP)

There is **no application database** (PostgreSQL, etc.) in this build. Storage is deliberately local and lightweight for the hackathon; a production deployment would introduce a persistent DB for backlog, users, auth, and multi-tenant isolation.

| Layer | What | Where | Survives backend restart? |
|---|---|---|---|
| **Server — backlog** | CTO triage items, publish/close state, relaxed previews, Micro-PRDs on items | In-memory (`backend/ai_pm/store.py`) | **No** — resets to pre-seeded `demo-*` items |
| **Server — durable** | Workspace drafts, submissions, public test run jobs | `data/drafts/`, `data/submissions/`, `data/jobs/` | **Yes** (on-disk under repo root) |
| **Server — datasets** | Synthetic SQLite challenge databases | `backend/generated_datasets/*.sqlite` | **Yes** |
| **Browser** | Draft cache, upload flow handoff, anonymous workspace session | IndexedDB (`draftStorage.ts`), `sessionStorage`, HTTP cookie | **Yes** (per browser; drafts also sync to server) |

**Important distinction:** SQLite files in `generated_datasets/` are **challenge fixtures** for students to query in technical workspaces — they are not the platform metadata store.

**Post-hackathon direction:** replace `store.py` with a DB-backed repository (e.g. Postgres) for backlog and tenancy; optionally move submission blobs to object storage; add auth and user profiles. Rank leaderboard / enterprise radar demo seeds may remain stubbed until live aggregation exists.

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
  ├─ Non-demo technical:
  │    generate_spec() (one LLM call or heuristic)
  │    → spec_to_microprd() (markdown brief + typed examples)
  │    → build PublishDraft baseline from projected Micro-PRD
  │    → build_package(challenge_spec=…, draft=challenge_draft)
  │    → challenge_package + validation + optional challenge_spec
  ├─ Product track / demo-*: no dynamic package (legacy scaffolds at publish)
  └─ Founder may override archetype via RelaxRequest.blueprint (e.g. algorithm)
  │
  ▼
POST /triage/regenerate/{id}  (optional — after draft/blueprint edits)
  └─ Re-runs spec + factory; marks stale until validation passes
  │
  ▼
POST /triage/publish/{id}  (requires locked reward + scope guard pass)
  ├─ Applies founder PublishDraft overrides
  ├─ Non-demo technical: requires valid non-stale challenge_package (no generation at publish)
  ├─ Legacy demo-* / product track: hardcoded starter_scaffold / synthesizer at publish
  ├─ Generates track-aware Micro-PRD
  ├─ company_profile.py → CompanyTechProfile on BacklogItem
  ├─ status → published; item appears in student hub + CTO **Live challenges** sidebar
  └─ Branch: technical → Python starter (+ SQLite if data_plane) | product → frontend starter
  │
  ▼
GET /sandbox/challenges/{id}  →  public_sanitize.build_public_challenge()
  └─ Only items with status=published (closed items return 404)
  └─ sandbox_routes._student_microprd(): spec-driven items skip legacy microprd_enrich
  └─ frontend MicroPRDView + BriefMarkdown render microprd.context as HTML (subset markdown)
  │
  ▼ (optional — founder closes hiring window)
POST /triage/close/{id}  (published → closed only)
  ├─ Removes challenge from student hub (list_published filter)
  ├─ Rejects new submissions (404 on sandbox routes)
  └─ Match Radar still available via GET /triage/backlog/{id}/matches
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
| **Startup sponsors** | `/startup/matches/{id}` | `GET /triage/backlog/{id}/matches` | **Sponsor Fit** for this challenge only (published or closed) |
| **Enterprises** | `/enterprise/radar` | `GET /sandbox/enterprise/radar` | Platform-wide top tier (platform signal) |

Startups do **not** see the student global leaderboard or other sponsors' challenge performers.

## External Dependencies

| Service | Purpose | Data sent |
|---|---|---|
| Local vLLM (Qwen) | Triage, domain obfuscation, sponsor fit (**sensitive** tier, when `LLM_BASE_URL` set) | Anonymized structural metadata — on-prem when configured |
| OpenAI API | **Default dev LLM**; sensitive + standard tier when key set | Anonymized structural metadata only; block sensitive cloud with `LLM_ALLOW_CLOUD_SENSITIVE=0` |
| Docker | Ephemeral assessor containers (network disabled) | Student submission code only |

## Known Constraints

- Privacy proxy is the critical security boundary — see `AGENTS.md`
- Public **Run** uses in-process pytest (student feedback loop); **submit grading** uses Docker secret tests for platform signal
- Persistence is filesystem + in-memory only — see [Persistence (hackathon MVP)](#persistence-hackathon-mvp); no auth or multi-tenant DB yet
