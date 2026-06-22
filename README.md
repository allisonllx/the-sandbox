# The Sandbox

Startups turn internal bugs and backlog items into **public coding challenges**. Students solve them to prove skill: without a traditional job application and without seeing which company wrote the problem.

**Zero-trust** here means: sensitive data (log lines, emails, internal product names) is cleaned up **on the startup's machine first**. Only a safe, abstract summary crosses into the rest of the platform.

> *"We aren't a job board; we are a proof-of-work protocol."*

---

## Who uses this?

| Who | What they do | Where in the app |
|---|---|---|
| **Startup** (CTO / founder) | Turn an internal problem into a publishable challenge, set a bounty, review who submitted | `/startup` · `/startup/upload` · `/startup/matches/{id}` |
| **Student** | Browse challenges, read the brief, build a solution, submit | `/student` · `/student/challenges/{id}` · `/student/leaderboard` |
| **Enterprise recruiter** *(demo UI)* | Browse platform-wide top talent | `/enterprise/radar` |

Three things to know up front:

- Students **never** see the real company name on a challenge (see [Blind audition](#3-blind-audition)).
- Startups **only** see submitters for **their own** challenge, not other companies' candidates.
- "How good are they in general?" and "How well did they solve *my* problem?" are **two different scores** (see [Grading & rankings](#5-grading--rankings)).

---

## The journey (at a glance)

Plain-language view of the full loop. Technical terms are defined in the sections below.

```
  ┌────────────────────── STARTUP ──────────────────────┐
  │  1. Paste logs, upload a file, or write a problem   │
  │     brief (cleaned locally)                         │
  │  2. See how urgent & risky the issue is             │
  │  3. Tweak the public brief, set bounty, publish     │
  │  4. Review who submitted — ranked for this challenge│
  └──────────────────────────┬──────────────────────────┘
                             │  public challenge goes live
                             │  (no company logo / internal names)
                             ▼
  ┌────────────────────── STUDENT ──────────────────────┐
  │  1. Browse challenges in the Innovation Hub         │
  │  2. Read brief + anonymous company profile          │
  │  3. Build solution (code editor or prototype)       │
  │  4. Submit → receive feedback scores                │
  └──────────────────────────┬──────────────────────────┘
                             ▼
  ┌──────────────────── OUTCOMES ───────────────────────┐
  │  Student: points on global leaderboard (demo seed)  │
  │  Startup: ranked list for their challenge (live)    │
  │  Enterprise: top-tier view across platform (demo)   │
  └─────────────────────────────────────────────────────┘
```

**Privacy rule:** Raw corporate text never leaves the local sanitization step. External AI (if enabled) sees field names and counts, not full log lines, emails, or internal codenames.

---

## How the pieces fit together

The sections below map to the journey above. Skim the headings first; drill in where you need detail.

### 1. Ingest & triage (startup)

**Goal:** Get a messy internal signal (Slack thread, log export, ticket, or founder-written brief) into a ranked backlog item without leaking PII.

Three equivalent ingest paths (all run **sanitize → score** locally before triage):

| Path | Where | API |
|---|---|---|
| **Upload UI** | `/startup/upload` → loading page | `POST /proxy/sanitize` then `POST /triage/score` |
| **Quick intake** | Sidebar on `/startup` | `POST /triage/intake` (wraps sanitize + score) |
| **API / scripts** | curl or `./scripts/factory_*.sh` | same as above |

1. **Privacy proxy** — runs locally. Strips emails, tokens, names, etc. Output is *structural metadata* (column names, event counts, row scale), not the original text.
2. **AI triage** — scores each item on three axes (0–100):
   - **Severity** — how badly it hurts the system
   - **Friction** — how often users hit it
   - **Sensitivity** — how risky it is to publish the *shape* of this problem publicly
3. **Sensitivity shield** — Red / Yellow / Green tag derived from the sensitivity score. Guides how aggressively to mask before publish.

The hackathon dashboard ships with **pre-seeded demo items** (`demo-003` … `demo-007`) so you can skip ingest UI. Adding new items:

```bash
# Option A — founder brief (one call)
curl -s -X POST http://localhost:8000/api/v1/triage/intake \
  -H "Content-Type: application/json" \
  -d '{"problem_statement":"Our webhook retries duplicate charges on 502...","source_label":"Founder brief","format":"text"}'

# Option B — logs (two steps, same as /startup/upload)
curl -s -X POST http://localhost:8000/api/v1/proxy/sanitize \
  -H "Content-Type: application/json" \
  -d '{"content": "2024-03-12 ERROR Login failed for user@example.com ...", "format": "log"}' \
  | tee /tmp/meta.json

curl -s -X POST http://localhost:8000/api/v1/triage/score \
  -H "Content-Type: application/json" \
  -d "$(jq '{metadata: .metadata, source_label: "Slack #bugs"}' /tmp/meta.json)"
```

**End-to-end scripts** (non-demo item → Preview → Publish):

```bash
./scripts/factory_intake.sh    # founder brief via /triage/intake
./scripts/factory_pipeline.sh  # log sanitize → score → relax → publish
```

See [`samples/demo_solutions/DOCS.md`](samples/demo_solutions/DOCS.md) for publish → submit demos on `demo-*` items.

### 2. De-risk & publish (startup)

**Goal:** Founder controls what students actually see before anything goes live.

On `/startup`, for each backlog item:

1. **Review scores** — Severity / Friction / Sensitivity and the Red / Yellow / Green shield
2. **Preview Changes** — generates Micro-PRD + **challenge package** (starter files + validation) for non-demo technical items via the [Challenge Factory](backend/challenge_factory/DOCS.md)
3. **Relaxation controls** — optional transforms that make the public challenge safer:
   - Rename internal column names to generic ones
   - Inject noise into scale hints
   - **Domain obfuscation** — reframe an industry-specific problem as a neutral scenario (e.g. food-delivery checkout → equipment locker rental) so students can't guess the sponsor
4. **Release preview** — edit the public title, success criteria, **challenge blueprint** (archetype, stack hints), company profile, and evaluation focus before publish
5. **Lock reward** — required checklist step before publish (payment is stubbed in the demo — see [disclaimer](#whats-implemented-vs-whats-demo-theater))
6. **Approve & publish** — scope guard blocks oversized challenges; non-demo items require a valid Preview package; `demo-007` is a hardcoded always-fail demo prop

### 3. Blind audition

**Goal:** Students trust the challenge is real without learning *which* company posted it.

| What the startup sees (internal) | What the student sees (public) |
|---|---|
| Real source label, internal codenames | Anonymous **Company Tech Profile** (stage, team size, stack) |
| Before/after domain masking preview | Sanitized **Micro-PRD** (the challenge brief) |
| Industry-specific field names | Renamed / abstract column names |

Students can read `/student/trust` for the trust narrative (marketing copy in the demo; no live KYC backend).

### 4. Solve & submit (student)

**Goal:** Student builds and submits in-browser.

| Track | What you do | What you submit |
|---|---|---|
| **Technical** | Multi-file **Monaco** editor (same engine as VS Code), run public tests, autosave | Python starter + synthetic SQLite dataset |
| **Product Feature** | Prototype editor | HTML/CSS/JS + **DESIGN.md** |

After submit, the student sees a **scorecard** with two sections (see next).

### 5. Grading & rankings

**Goal:** Separate "objective platform quality" from "does this person fit *my* challenge?"

Every submission gets a **dual-layer scorecard**:

| Layer | Plain English | Feeds |
|---|---|---|
| **Platform Signal** | Did the solution pass automated checks? (secret tests in Docker, security scan, deliverable structure) | **Execution Points** — global student motivation score |
| **Sponsor Fit** | How well does this submission match *this challenge's* success criteria? (LLM or heuristic) | **Match Radar** — startup's ranked list at `/startup/matches/{id}` |

A student can score high globally but not top a specific startup's list — and vice versa. That's intentional.

### 6. Three places rankings appear

See [What's Implemented vs Demo Theater](#whats-implemented-vs-whats-demo-theater) for which of these use live data today.

| Who looks | Page | Sorted by |
|---|---|---|
| Student | `/student/leaderboard` | Execution Points *(demo seed)* |
| Startup | `/startup/matches/{id}` | Sponsor Fit *(live after submissions)* |
| Enterprise | `/enterprise/radar` | Platform Signal *(demo seed)* |

---

## Defensive posture

Which security rules are enforced vs narrated for the demo: [What's Implemented vs Demo Theater](#whats-implemented-vs-whats-demo-theater).

Demo-only internal names students never see: **StealthCo** (`demo-005`), **NovaPay** (`demo-003`), **Platform Pool** (`demo-006`).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ · FastAPI · Pydantic v2 |
| Privacy Proxy | Regex PII masking · spaCy `en_core_web_sm` (local NER, offline) |
| AI / LLM | Local vLLM (Qwen via OpenAI-compatible API) for sensitive paths · OpenAI (`gpt-4o-mini`) fallback for `standard` tier and optional cloud sensitive · heuristic fallback when no LLM |
| Assessor | Dual-layer: Docker secret tests (platform) + LLM sponsor fit |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS · Monaco editor |
| Testing | pytest · 126 tests |
| Code Runner | Docker assessor (`the-sandbox-runner`) for secret tests; in-process for student **Run** |

---

## Project Structure

```
the_sandbox/
├── backend/
│   ├── privacy_proxy/          # Local PII scrubbing, NER, structural extraction
│   ├── ai_pm/                  # Triage, relaxation, blind audition, Micro-PRD, publish draft
│   ├── prompts/                # LLM system prompts (ai_pm + assessor)
│   ├── assessor/               # Dual-layer platform signal + sponsor fit
│   ├── sandbox/                # Datasets, submissions, leaderboard, match radar
│   ├── api/                    # HTTP routes
│   └── tests/
├── frontend/
│   ├── app/startup/            # Triage dashboard + sponsor Match Radar
│   ├── app/student/            # Innovation Hub, workspace, leaderboard, trust
│   └── app/enterprise/radar/   # Enterprise subscription view (demo)
├── docker/sandbox-runner/      # Assessor container image
├── samples/demo_solutions/     # Reference submissions for demo-003/004/005
├── docs/                       # ARCHITECTURE, PRODUCT, api-patterns
├── .env.example                # Environment template (copy to .env)
├── feature_list.json           # Feature state + verification evidence
└── init.sh
```

Module docs: [`backend/privacy_proxy/DOCS.md`](backend/privacy_proxy/DOCS.md) · [`backend/ai_pm/DOCS.md`](backend/ai_pm/DOCS.md) · [`backend/prompts/DOCS.md`](backend/prompts/DOCS.md) · [`backend/assessor/DOCS.md`](backend/assessor/DOCS.md) · [`backend/sandbox/DOCS.md`](backend/sandbox/DOCS.md) · [`backend/api/DOCS.md`](backend/api/DOCS.md) · [`frontend/DOCS.md`](frontend/DOCS.md)

Topic docs: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/PRODUCT.md`](docs/PRODUCT.md) · [`docs/api-patterns.md`](docs/api-patterns.md)

---

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker *(optional — required for full platform secret-test grading on submit)*
- vLLM + Qwen *(optional — recommended for sensitive triage/obfuscation; keeps column names on-prem)*
- LLM / OpenAI keys *(optional — heuristics work without any LLM; see [Environment Variables](#environment-variables))*

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# Optional: local NER model (~12 MB)
pip install "spacy==3.7.0"
pip install "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"

cp .env.example .env
# Edit .env — uncomment OPENAI_API_KEY and/or adjust LLM_BASE_URL
set -a && source .env && set +a

python -m uvicorn backend.main:app --reload --port 8000
```

API: **http://localhost:8000** · OpenAPI: **http://localhost:8000/docs**

### Frontend

```bash
cd frontend && npm install && npm run dev
```

App: **http://localhost:3000** → redirects to **/startup**

### Tests

```bash
python -m pytest backend/tests/ -v    # expect 126 passed
```

### Assessor Docker image (optional)

```bash
docker build -t the-sandbox-runner docker/sandbox-runner
```

Without Docker, platform technical grading degrades to static security scan only — student code is **never** executed on the host.

Or run everything via `./init.sh`.

### Sample solutions (testing)

Ready-to-submit reference projects for `demo-003`, `demo-004`, and `demo-005` live in [`samples/demo_solutions/`](samples/demo_solutions/DOCS.md). One-liner after the backend is running:

```bash
./samples/demo_solutions/test_sample.sh demo-003
```

---

## Environment Variables

Copy [`.env.example`](.env.example) to `.env` and load it before starting the backend:

```bash
cp .env.example .env
set -a && source .env && set +a
```

The backend does not auto-load `.env` — export vars manually or use the `source` pattern above. Never commit `.env` (listed in `.gitignore`).

### Local LLM (sensitive tier — privacy-first)

| Variable | Default | Description |
|---|---|---|
| `LLM_BASE_URL` | *(unset)* | OpenAI-compatible local endpoint, e.g. `http://localhost:8000/v1` when running vLLM. **Preferred for triage, domain obfuscation, Micro-PRD, sponsor fit.** |
| `LLM_MODEL` | `Qwen/Qwen2.5-7B-Instruct` | Model id on the local server. |
| `LLM_API_KEY` | `local` | API key sent to the local server (vLLM often accepts any value). |
| `LLM_ALLOW_CLOUD_SENSITIVE` | off | Set `1` to allow OpenAI when local vLLM is down for **sensitive** tier. Default: blocked (privacy-first). |
| `LLM_DOMAIN_OBFUSCATE` | on | Set `0` to disable LLM domain masking for novel industries. |

Start vLLM in a separate terminal (not a pip dependency of this repo):

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000
```

### OpenAI cloud (optional)

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(unset)* | Cloud fallback for **standard** tier; optional sensitive fallback when `LLM_ALLOW_CLOUD_SENSITIVE=1`. Heuristic/template paths if absent. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model id for OpenAI requests. |

### Minimal setups

| Goal | Config |
|---|---|
| Offline demo (no LLM) | Leave all vars unset — heuristics + templates |
| Privacy-first production | `LLM_BASE_URL` only; keep `LLM_ALLOW_CLOUD_SENSITIVE` unset |
| Local + cloud fallback | `LLM_BASE_URL` + `OPENAI_API_KEY` + `LLM_ALLOW_CLOUD_SENSITIVE=1` |
| Cloud only (dev) | `OPENAI_API_KEY` only *(sensitive tier hits OpenAI unless local is also set)* |

---

## What's Implemented vs What's Demo Theater

Read this before the judge script: it labels what is real pipeline code vs hackathon shortcuts.

The README uses three labels:

| Label | Meaning |
|---|---|
| **Implemented** | Code runs for any backlog item you create — not limited to `demo-*` seeds |
| **Demo shortcut** | Real UI/API exists, but this hackathon uses pre-written samples or hardcoded IDs to make judging easy |
| **Not built** | Shown in copy or UI only; no backend |

### Implemented (works beyond seeded items)

These pipelines are **general-purpose**. You can `POST /triage/score` a new item from sanitized metadata and run the same flow as `demo-003`:

- **Privacy proxy** — any raw log text via `POST /proxy/sanitize`
- **Triage scoring** — Severity / Friction / Sensitivity on any `SanitizedMetadata`
- **Relaxation controls** — column rename, noise, abstract logic on any item's metadata
- **Domain obfuscation** — keyword/field transforms when you toggle it at publish (not tied to one demo ID)
- **Blind audition** — every published challenge strips `brand_proxy` on the student API
- **Release preview + publish** — Micro-PRD, synthetic dataset, starter scaffold for any item that passes guards
- **Student workspace + submit** — Monaco editor, drafts, submission storage
- **Dual-layer assessor** — platform (Docker if available) + sponsor fit (LLM if key set) on any submission

The dashboard opens on **7 pre-seeded backlog items** (`demo-001` … `demo-007`) so judges skip ingest UI. That is sample **input data**, not a separate code path — except where noted below.

### Demo shortcuts (don't over-generalize these)

| What | What actually happens |
|---|---|
| **Pre-seeded backlog** | `demo-*` items ship in `store.py` with crafted titles/metadata for the judge script. New items via API work the same way once scored. |
| **`demo-007` publish fails** | A **deliberate demo prop**. `demo-007` is hardcoded in `scope_guard.py` to always fail publish with HTTP **422** (`SCOPE_EXCEEDED`) so you can show “AI PM blocks oversized scope.” Other items use the generic ~8h estimate; `demo-007` always fails regardless. |
| **Reward “lock”** | **Rule is enforced** — publish returns 422 if you don't click Lock reward. **Payment is not** — no Stripe, no escrow account; `locked: true` is a boolean in the request body. Think: real checklist gate, fake money. |
| **Match Radar empty state** | If nobody submitted yet, shows **hardcoded fake candidates** for that challenge ID. After a real submit, rankings use live scorecards (`source: live`). |
| **Student leaderboard / enterprise radar** | Always **hardcoded seed rows** (e.g. Candidate A7F2). Not computed from live submissions yet. |
| **`/student/trust`, verified badges** | Marketing copy + UI badges only; no sponsor KYC backend. |
| **LLM / Docker** | Optional. **Sensitive** calls prefer local vLLM (`LLM_BASE_URL`); OpenAI remains fallback / **standard** tier. Without any LLM or Docker, assessor and triage use heuristics — still runs, less “smart.” |

### Not built

Auth, multi-tenant startups, persistent database (backlog is in-memory), real escrow/KYC.

**Practical demo tip:** show **implemented** flows on `demo-003` or `demo-005` (publish + student submit + live Match Radar). Show **demo shortcuts** explicitly: try publishing `demo-007` (422 scope rejection), open leaderboard (seed data), mention reward lock is a gate not a payment.

---

## Judge demo script

Terms above in plain English: this is the click-by-click path for judges.

1. **Blind audition** — `/startup` → `demo-005` → toggle *Obfuscate Industry Domain* → Preview → Lock reward → Publish → open `/student/challenges/demo-005` — students see stage/team/stack only, not StealthCo or food/merchant tokens
2. **Editable release preview** — Preview Changes → edit title, success criteria, company profile → Publish with draft
3. **Scope cap demo** — select `demo-007` → Publish → HTTP 422 `SCOPE_EXCEEDED` (hardcoded reject for judges)
4. **Reward lock** — must Lock reward before publish (422 if not); no real payment rails
5. **Verified sponsor + bounty** — `demo-003` → Lock $500 → Publish → student card shows Verified Sponsor + escrow label (UI only)
6. **Dual-layer scorecard** — submit as student → Platform Signal + Sponsor Fit sections on the scorecard
7. **Three ranking pages** — `/student/leaderboard` (seed) · `/startup/matches/demo-003` (live after submit) · `/enterprise/radar` (seed)
8. **Trust narrative** — `/student/trust`

---

## Demo walkthrough (5 min)

**Startup path**

1. Open `/startup` — pick `demo-003` or `demo-005`
2. Try relaxation toggles → **Preview Changes** → edit the public brief
3. Lock reward → **Approve & Publish**
4. Open the match list → `/startup/matches/{id}`

**Student path**

1. Open `/student` — pick a challenge
2. Note: no company name, only anonymous company profile
3. Technical track: code in Monaco, run tests, submit → scorecard with two score sections
4. Product track (`demo-004`): submit prototype + DESIGN.md

**Ingest (API)**

```bash
curl -s -X POST http://localhost:8000/api/v1/proxy/sanitize \
  -H "Content-Type: application/json" \
  -d '{"content": "ERROR Login failed for john.doe@acme.com token=sk_live_x ip=10.0.0.5", "format": "log"}' \
  | python -m json.tool
```

Response contains structural metadata only — no email, token, or IP.

---

## API Reference

Key entry points only. Full contract: **http://localhost:8000/docs** · module detail: [`backend/api/DOCS.md`](backend/api/DOCS.md)

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/proxy/sanitize` | Ingest: raw text → metadata (local) |
| `POST` | `/api/v1/triage/score` | Ingest: metadata → backlog item |
| `POST` | `/api/v1/triage/intake` | Ingest: founder brief → sanitize + score (one call) |
| `POST` | `/api/v1/triage/relax/{id}` | Preview: Micro-PRD + challenge factory package |
| `POST` | `/api/v1/triage/regenerate/{id}` | Re-run factory after draft/blueprint edits |
| `POST` | `/api/v1/triage/publish/{id}` | Publish challenge |
| `GET` | `/api/v1/sandbox/challenges` | Student: list public challenges |
| `POST` | `/api/v1/sandbox/challenges/{id}/submit` | Student: submit → scorecard |
| `GET` | `/api/v1/triage/backlog/{id}/matches` | Sponsor: Match Radar |

---

## Feature Status

All hackathon MVP features passing (`feature_list.json`):

| Feature | Summary |
|---|---|
| `privacy-001` | Local privacy proxy + PII strip |
| `triage-001` | AI PM triage dashboard + relaxation controls |
| `sandbox-001` | Student terminal + Micro-PRD |
| `workspace-002` | Monaco workspace, persistence, public Run |
| `tracks-001` / `product-001` | Technical + Product Feature innovation tracks |
| `trust-001` | Scope cap + domain obfuscation |
| `rewards-001` | Reward lock gate (stub escrow) |
| `blind-002` | Blind audition Company Tech Profile |
| `rank-001` | Three rank surfaces (student / sponsor / enterprise) |
| `assessor-001` | Dual-layer assessor (Docker platform + LLM sponsor fit) |
| `llm-local-001` | Local vLLM routing + LLM domain obfuscation (OpenAI fallback) |
| `factory-001` | Dynamic challenge factory — blueprint-driven starters at Preview (Phase 1) |
| `intake-001` | Founder ingest — `/triage/intake` + `/startup/upload` UI |

**Deferred post-MVP:** auth, multi-tenant isolation, real Stripe escrow, sponsor KYC, live global leaderboard aggregation, factory Phase 2–3 (per-challenge secret tests, product factory UI panel).

---

## Agent / Contributor Notes

Sessions should read [`AGENTS.md`](AGENTS.md) first, then [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`claude-progress.md`](claude-progress.md) for verified state.
