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

## What's Real vs Demo

This repo is a **hackathon MVP**: core trust and grading mechanics are implemented; billing, auth, and some recruiter UX are narrative stubs. Use this table when demoing to judges.

| Area | Status | Notes |
|---|---|---|
| Privacy proxy (PII strip) | **Real** | Local-only; no raw content in API responses |
| Ingest (`sanitize` → `score`) | **Real API**, no UI | Backlog pre-seeded with `demo-*` items for judges |
| Triage, relaxation, domain obfuscation | **Real** | Deterministic transforms + optional LLM |
| Blind audition boundary | **Real** | Students never get `brand_proxy`; public API sanitized |
| Editable release preview | **Real** | `PublishDraft` before publish |
| Scope cap (~8h) | **Real gate** | `demo-007` → 422 |
| Reward lock before publish | **Real gate** | No Stripe / escrow — money is fake |
| Publish → dataset + starter | **Real** | SQLite synthesizer + scaffold on disk |
| Student workspace + submit | **Real** | Monaco, drafts, disk-backed submissions |
| Public **Run** (pre-submit tests) | **Real** | In-process pytest on host |
| Assessor platform signal | **Real** (needs Docker) | Secret tests in isolated container; degrades without Docker |
| Assessor sponsor fit | **Real** (needs `OPENAI_API_KEY`) | Heuristic fallback offline |
| Dual-layer scorecard | **Real** | EP from platform only; Match Radar from sponsor fit |
| Sponsor Match Radar | **Hybrid** | **Live** rankings when submissions exist; **demo seed** when empty |
| Student leaderboard | **Demo seed** | Not aggregated from live submissions yet |
| Enterprise radar | **Demo seed** | Subscription narrative only |
| `/student/trust`, verified badges | **Narrative stub** | UI copy; no KYC backend |
| Auth, multi-tenant, persistent DB | **Not built** | In-memory backlog; anonymous workspace cookies |

**Rule of thumb:** if a student or sponsor *does something in the app* (publish, submit, score), it usually hits real backend logic. If a page shows **platform-wide talent rankings** without a submit flow behind it, treat it as demo seed unless Match Radar shows `source: live`.

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
4. **Lock reward** (required gate — escrow is stubbed, see table above)
5. **Approve & Publish** — scope cap (~8h) blocks oversized items (`demo-007` → 422)

Published challenges expose a **Company Tech Profile** to students (stage, team size, stack) — never the internal `brand_proxy`.

### 3. Blind audition (student-facing boundary)

| Internal (CTO only) | Public (students) |
|---|---|
| `brand_proxy`, `source_label`, `sponsor_profile` | `CompanyTechProfile` |
| Domain before/after preview | Sanitized Micro-PRD + obfuscated column names |
| Real industry tokens | Abstract titles, red-sensitivity omits `industry_broad` |

Students verify sponsor legitimacy at `/student/trust` (narrative stub — see disclaimer).

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

See **What's Real vs Demo** — only Match Radar uses live submission data today.

| Audience | Route | Sort key |
|---|---|---|
| Students | `/student/leaderboard` | Execution Points (demo seed) |
| Startup sponsors | `/startup/matches/{id}` | Sponsor Fit (live when submissions exist) |
| Enterprises | `/enterprise/radar` | Platform signal (demo seed) |

---

## Defensive Posture

See **What's Real vs Demo** for which mitigations are enforced vs narrated. Demo CTO-only labels: **StealthCo** (`demo-005`), **NovaPay** (`demo-003`), **Platform Pool** (`demo-006`). Students never see these names.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ · FastAPI · Pydantic v2 |
| Privacy Proxy | Regex PII masking · spaCy `en_core_web_sm` (local NER, offline) |
| AI / LLM | OpenAI API (`gpt-4o-mini`) · heuristic fallback when key absent |
| Assessor | Dual-layer: Docker secret tests (platform) + LLM sponsor fit |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS · Monaco editor |
| Testing | pytest · 113 tests |
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
- `OPENAI_API_KEY` *(optional — heuristic + offline fallbacks work without it)*

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# Optional: local NER model (~12 MB)
pip install "spacy==3.7.0"
pip install "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"

export OPENAI_API_KEY=sk-...   # optional

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
python -m pytest backend/tests/ -v    # expect 113 passed
```

### Assessor Docker image (optional)

```bash
docker build -t the-sandbox-runner docker/sandbox-runner
```

Without Docker, platform technical grading degrades to static security scan only — student code is **never** executed on the host.

Or run everything via `./init.sh`.

---

## Judge Demo Script

1. **Blind audition** — `/startup` → `demo-005` → *Obfuscate Industry Domain* → Preview (Company Tech Profile) → Lock reward → Publish → `/student/challenges/demo-005` shows stage/team/stack only — no StealthCo or food/merchant tokens
2. **Editable release preview** — Preview Changes → edit title, success criteria, company profile → Publish with draft
3. **Scope cap** — `demo-007` → Publish → 422 `SCOPE_EXCEEDED` with breakdown
4. **Verified sponsor + bounty** — `demo-003` → Lock $500 → Publish → student card shows Verified Sponsor + escrow label
5. **Dual-layer scorecard** — submit as student → Platform Signal + Sponsor Fit sections; EP from platform only
6. **Three rank surfaces** — `/student/leaderboard` · `/startup/matches/demo-003` (Sponsor Fit) · `/enterprise/radar`
7. **Trust narrative** — `/student/trust`

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

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | No | Triage scoring, Micro-PRD generation, sponsor fit LLM. Heuristic fallback if absent. |

Secrets must never be committed. Use `.env` locally (in `.gitignore`).

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

**Deferred post-MVP:** auth, multi-tenant isolation, real Stripe escrow, sponsor KYC, startup ingest UI, live global leaderboard aggregation.

---

## Agent / Contributor Notes

Sessions should read [`AGENTS.md`](AGENTS.md) first, then [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`claude-progress.md`](claude-progress.md) for verified state.
