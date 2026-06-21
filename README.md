# The Sandbox

A zero-trust **Innovation Hub** and proof-of-work talent platform. Growth-stage startups turn internal backlogs into safe, blind-audition challenges. Students prove capability on real engineering problems without résumés, referrals, or company logos on the line.

> *"We aren't a job board; we are a zero-trust proof-of-work protocol."*

---

## Stakeholders

| Stakeholder | Role | Primary surfaces |
|---|---|---|
| **Startup sponsor** (CTO / founder) | Ingests problems, de-risks IP, publishes challenges, reviews **Sponsor Match Radar** for their challenge only | `/startup` · `/startup/matches/{id}` |
| **Student** | Discovers blind-audition challenges, solves in track workspace, earns **Execution Points** from platform-verified signal | `/student` · `/student/challenges/{id}` · `/student/leaderboard` · `/student/trust` |
| **Enterprise recruiter** | Browses platform-wide top-tier talent (demo seed UI) | `/enterprise/radar` |

Startups never see other companies' performers. Students never see sponsor names. Global rank and sponsor fit are **intentionally different scores**.

---

## End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STARTUP SPONSOR                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Raw logs / feedback  →  Privacy Proxy (local PII strip)                    │
│       →  POST /triage/score  →  AI PM triage (Severity / Friction / Sens.)  │
│       →  Relaxation + domain obfuscation  →  editable Release Preview       │
│       →  Lock reward + scope check  →  Publish                              │
│       →  Match Radar (/startup/matches/{id}) sorted by Sponsor Fit          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    public challenge (blind audition — no brand_proxy)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STUDENT                                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Innovation Hub  →  Company Tech Profile + Micro-PRD (no sponsor name)      │
│       →  Technical: Monaco workspace + dataset + public Run                 │
│       →  Product: prototype + DESIGN.md                                     │
│       →  Submit  →  Dual-layer scorecard                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ASSESSOR (dual-layer)                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Platform Signal  — Docker secret tests + security scan (track-standard)    │
│       →  Execution Points  →  student leaderboard (demo) + enterprise radar │
|       (demo)                                                                │
│  Sponsor Fit      — LLM vs challenge success criteria (heuristic offline)   │
│       →  Match Radar rank for that challenge only                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Trust guarantee:** raw corporate data never leaves the sanitization boundary. External LLMs see anonymized structural metadata (triage) or sanitized public challenge context + student submission (sponsor fit) — never `brand_proxy`, source labels, or raw log lines.

---

## How the Pieces Fit Together

### 1. Ingest & triage (startup)

Founders add problems by piping text through the privacy proxy, then scoring metadata into the backlog:

```bash
# Step 1 — sanitize locally (metadata only in response)
curl -s -X POST http://localhost:8000/api/v1/proxy/sanitize \
  -H "Content-Type: application/json" \
  -d '{"content": "2024-03-12 ERROR Login failed for user@example.com ...", "format": "log"}'

# Step 2 — score and add to backlog
curl -s -X POST http://localhost:8000/api/v1/triage/score \
  -H "Content-Type: application/json" \
  -d '{"metadata": { ... }, "source_label": "Slack #bugs"}'
```

The hackathon dashboard ships with **pre-seeded demo backlog items** (`demo-003` … `demo-007`) so judges can run the full loop without ingest UI. Adding new problems via API is supported; a startup paste/upload UI is optional polish.

### 2. De-risk & publish (startup)

On `/startup`, founders:

1. Review Severity / Friction / Sensitivity and sensitivity shield (Red / Yellow / Green)
2. Apply **Relaxation Controls** — abstract logic, synthesize column names, noise injection, domain obfuscation
3. **Preview Changes** — edit the **Release Preview** (title, success criteria, company profile, evaluation focus)
4. **Lock reward** (required gate — escrow is stubbed; see [What's Implemented vs Demo Theater](#whats-implemented-vs-whats-demo-theater))
5. **Approve & Publish** — generic scope check (~8h estimate) blocks oversized items; `demo-007` is a **hardcoded** always-fail demo (see disclaimer)

Published challenges expose a **Company Tech Profile** to students (stage, team size, stack) — never the internal `brand_proxy`.

### 3. Blind audition (student-facing boundary)

| Internal (CTO only) | Public (students) |
|---|---|
| `brand_proxy`, `source_label`, `sponsor_profile` | `CompanyTechProfile` |
| Domain before/after preview | Sanitized Micro-PRD + obfuscated column names |
| Real industry tokens | Abstract titles, red-sensitivity omits `industry_broad` |

Students verify sponsor legitimacy at `/student/trust` (narrative stub — see [demo disclaimer](#whats-implemented-vs-whats-demo-theater)).

### 4. Solve & submit (student)

| Track | Workspace | Deliverables |
|---|---|---|
| **Technical** | Monaco multi-file editor, public Run, autosave | `src/queries.py` + starter scaffold; synthetic SQLite dataset |
| **Product Feature** | Prototype editor | HTML/CSS/JS + **DESIGN.md**; optional Figma/deploy links |

### 5. Dual-layer assessment

Every submission produces two independent scores:

| Layer | What it measures | Used for |
|---|---|---|
| **Platform Signal** | Track-standard objective rubric (Docker secret tests, security scan, deliverable structure) | **Execution Points** — global student motivation + enterprise radar |
| **Sponsor Fit** | Alignment with *this* challenge's success criteria and evaluation focus (LLM or heuristic) | **Match Radar** — `/startup/matches/{id}` only |

A student can rank highly on Execution Points globally while not topping a specific sponsor's Match Radar — and vice versa.

### 6. Three rank surfaces (by design)

See [What's Implemented vs Demo Theater](#whats-implemented-vs-whats-demo-theater) — only Match Radar uses live submission data today.

| Audience | Route | Sort key |
|---|---|---|
| Students | `/student/leaderboard` | Execution Points (demo seed) |
| Startup sponsors | `/startup/matches/{id}` | Sponsor Fit (live when submissions exist) |
| Enterprises | `/enterprise/radar` | Platform signal (demo seed) |

---

## Defensive Posture

See [What's Implemented vs Demo Theater](#whats-implemented-vs-whats-demo-theater) for which mitigations are enforced vs narrated. Demo CTO-only labels: **StealthCo** (`demo-005`), **NovaPay** (`demo-003`), **Platform Pool** (`demo-006`). Students never see these names.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ · FastAPI · Pydantic v2 |
| Privacy Proxy | Regex PII masking · spaCy `en_core_web_sm` (local NER, offline) |
| AI / LLM | Local vLLM (Qwen via OpenAI-compatible API) for sensitive paths · OpenAI (`gpt-4o-mini`) fallback for `standard` tier and optional cloud sensitive · heuristic fallback when no LLM |
| Assessor | Dual-layer: Docker secret tests (platform) + LLM sponsor fit |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS · Monaco editor |
| Testing | pytest · 121 tests |
| Code Runner | Docker assessor (`the-sandbox-runner`) for secret tests; in-process for student **Run** |

---

## Project Structure

```
the_sandbox/
├── backend/
│   ├── privacy_proxy/          # Local PII scrubbing, NER, structural extraction
│   ├── ai_pm/                  # Triage, relaxation, blind audition, Micro-PRD, publish draft
│   ├── assessor/               # Dual-layer platform signal + sponsor fit
│   ├── sandbox/                # Datasets, submissions, leaderboard, match radar
│   ├── api/                    # HTTP routes
│   └── tests/
├── frontend/
│   ├── app/startup/            # Triage dashboard + sponsor Match Radar
│   ├── app/student/            # Innovation Hub, workspace, leaderboard, trust
│   └── app/enterprise/radar/   # Enterprise subscription view (demo)
├── docker/sandbox-runner/      # Assessor container image
├── docs/                       # ARCHITECTURE, PRODUCT, api-patterns
├── .env.example                # Environment template (copy to .env)
├── feature_list.json           # Feature state + verification evidence
└── init.sh
```

Module docs: [`backend/privacy_proxy/DOCS.md`](backend/privacy_proxy/DOCS.md) · [`backend/ai_pm/DOCS.md`](backend/ai_pm/DOCS.md) · [`backend/assessor/DOCS.md`](backend/assessor/DOCS.md) · [`backend/sandbox/DOCS.md`](backend/sandbox/DOCS.md) · [`backend/api/DOCS.md`](backend/api/DOCS.md) · [`frontend/DOCS.md`](frontend/DOCS.md)

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
python -m pytest backend/tests/ -v    # expect 121 passed
```

### Assessor Docker image (optional)

```bash
docker build -t the-sandbox-runner docker/sandbox-runner
```

Without Docker, platform technical grading degrades to static security scan only — student code is **never** executed on the host.

Or run everything via `./init.sh`.

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

Read this before the judge script — it labels what is real pipeline code vs hackathon shortcuts.

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

Auth, multi-tenant startups, persistent database (backlog is in-memory), real escrow/KYC, startup paste/upload UI (use API or seeds).

**Practical demo tip:** show **implemented** flows on `demo-003` or `demo-005` (publish + student submit + live Match Radar). Show **demo shortcuts** explicitly: try publishing `demo-007` (422 scope rejection), open leaderboard (seed data), mention reward lock is a gate not a payment.

---

## Judge Demo Script

1. **Blind audition** — `/startup` → `demo-005` → *Obfuscate Industry Domain* → Preview (Company Tech Profile) → Lock reward → Publish → `/student/challenges/demo-005` shows stage/team/stack only — no StealthCo or food/merchant tokens
2. **Editable release preview** — Preview Changes → edit title, success criteria, company profile → Publish with draft
3. **Scope cap demo** — select `demo-007` → Publish → HTTP 422 `SCOPE_EXCEEDED` (hardcoded reject for judges; other items use generic hour estimate)
4. **Reward lock** — must Lock reward before publish (422 if not); no real payment rails
5. **Verified sponsor + bounty** — `demo-003` → Lock $500 → Publish → student card shows Verified Sponsor + escrow label (UI only)
6. **Dual-layer scorecard** — submit as student → Platform Signal + Sponsor Fit sections; EP from platform only
7. **Three rank surfaces** — `/student/leaderboard` (seed) · `/startup/matches/demo-003` (live after submit) · `/enterprise/radar` (seed)
8. **Trust narrative** — `/student/trust`

---

## Demo Walkthrough (5 min)

**Startup path**

1. Open `/startup` — pick `demo-003` or `demo-005`
2. Toggle relaxation controls → **Preview Changes** → edit Release Preview
3. Lock reward → **Approve & Publish**
4. Open **Match Radar** link → `/startup/matches/{id}`

**Student path**

1. Open `/student` — filter by track
2. Open a challenge — note Company Tech Profile (no sponsor name)
3. Technical: run public tests, submit → dual-layer scorecard
4. Product (`demo-004`): submit with DESIGN.md

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
| `POST` | `/api/v1/proxy/sanitize` | Ingest: raw text → metadata |
| `POST` | `/api/v1/triage/score` | Ingest: metadata → backlog item |
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

**Deferred post-MVP:** auth, multi-tenant isolation, real Stripe escrow, sponsor KYC, startup ingest UI, live global leaderboard aggregation.

---

## Agent / Contributor Notes

Sessions should read [`AGENTS.md`](AGENTS.md) first, then [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`claude-progress.md`](claude-progress.md) for verified state.
