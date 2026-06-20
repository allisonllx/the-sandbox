# The Sandbox

A zero-trust, two-sided R&D and proof-of-work talent platform. Startups turn their messy internal backlogs into safe, publishable coding challenges. Students solve those challenges to prove real-world engineering capability — without résumés, referrals, or recruiting filters.

---

## How It Works

```
[Startup local process]
Raw logs / feedback text (Slack, Intercom, CSV, error logs)
        │
        ▼
  Privacy Proxy          ← strips all PII locally; nothing raw leaves this boundary
        │ anonymized structural metadata only
        ▼
  AI PM Triage           ← LLM scores Severity / Friction / Sensitivity
        │
        ▼
  Relaxation Controls    ← founder abstracts logic, synthesizes variable names,
        │                   injects statistical noise
        ▼
  Micro-PRD + Synthetic Dataset  ← published to public sandbox
        │
        ▼
[Student terminal]
  Student solves challenge ──► AI Assessor grades taste + correctness ──► CTO dashboard
```

The critical guarantee: **raw corporate data never leaves the local process.** The LLM only ever sees anonymized structural metadata (field names, inferred types, event frequencies, row scale).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ · FastAPI · Pydantic v2 |
| Privacy Proxy | Regex PII masking · spaCy `en_core_web_sm` (local NER, offline) |
| AI / LLM | OpenAI API (`gpt-4o-mini`) · heuristic fallback when key absent |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS |
| Testing | pytest · 46 tests, 0 mocks for network calls in privacy layer |
| Code Runner | Docker (ephemeral containers) — planned for `assessor-001` |

---

## Project Structure

```
the_sandbox/
├── backend/
│   ├── privacy_proxy/       # Zero-trust sanitization engine
│   │   ├── pii_patterns.py  # Regex: email, phone, JWT, AWS/Stripe keys, IPv4 …
│   │   ├── ner_engine.py    # spaCy local NER (graceful degradation if not installed)
│   │   ├── structural_extractor.py  # JSON / CSV / log metadata extraction
│   │   └── sanitizer.py     # Pipeline: guardrail → scrub → NER → extract
│   ├── ai_pm/               # AI Product Manager layer
│   │   ├── scorer.py        # LLM Severity / Friction / Sensitivity scoring
│   │   ├── relaxation.py    # Abstract logic, variable synthesis, noise injection
│   │   ├── microprd.py      # Micro-PRD generator
│   │   └── store.py         # In-memory backlog (3 pre-loaded demo items)
│   ├── api/
│   │   ├── routes.py        # POST /api/v1/proxy/sanitize
│   │   └── triage_routes.py # GET/POST /api/v1/triage/*
│   ├── tests/               # 46 pytest tests
│   ├── main.py              # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── app/startup/         # CTO dashboard (split-screen triage UI)
│   ├── components/          # BacklogCard, RelaxationPanel, SensitivityBadge, ScoreBar
│   ├── lib/                 # API client, TypeScript types
│   └── package.json
├── docs/
│   ├── api-patterns.md      # API design patterns — required when adding endpoints
│   ├── ARCHITECTURE.md      # System architecture + data-flow diagrams
│   ├── PRODUCT.md           # Non-technical product overview
│   └── documentation-sync.md  # Which docs to update when code changes
├── AGENTS.md                # Agent operating rules (read first every session)
├── feature_list.json        # Feature state tracker
├── claude-progress.md       # Session log
└── init.sh                  # Standard startup script
```

---

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, directory layout, data flows |
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | User personas, core flows, scope, roadmap |
| [`docs/api-patterns.md`](docs/api-patterns.md) | API response shapes and endpoint conventions |
| [`docs/documentation-sync.md`](docs/documentation-sync.md) | Code path → doc mapping; keep docs in sync with changes |

Agent sessions should read `AGENTS.md` first, then the relevant topic doc above.

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- An `OPENAI_API_KEY` environment variable *(optional — all features work without it using heuristic fallback)*

---

## Quickstart

### 1. Clone and enter the repo

```bash
git clone <repo-url> the_sandbox
cd the_sandbox
```

### 2. Backend

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# (Optional but recommended) Download the local NER model — ~12 MB
# Install spaCy first, then download the model via pip (more reliable than the spaCy CLI)
pip install "spacy==3.7.0"
pip install "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"

# Set your OpenAI key (optional — heuristic fallback works without it)
export OPENAI_API_KEY=sk-...

# Start the API server
# Use `python -m uvicorn` to guarantee the active venv's interpreter is used
python -m uvicorn backend.main:app --reload --port 8000
```

The API will be live at **http://localhost:8000**. OpenAPI docs at **http://localhost:8000/docs**.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be live at **http://localhost:3000** → auto-redirects to **/startup**.

### 4. Run the test suite

```bash
# From the repo root
python -m pytest backend/tests/ -v
```

Expected output: **46 passed**.

---

## Demo Walkthrough

The backend ships with three pre-scored backlog items so the full demo loop works out of the box — no pipeline setup required.

1. **Open the CTO dashboard** at `http://localhost:3000/startup`
2. **Click any backlog card** — the right panel shows Severity / Friction / Sensitivity scores and the Red / Yellow / Green sensitivity shield
3. **Toggle Relaxation Controls** — enable *Synthesize Variable Names* and drag the noise slider to ~50%, then click **Preview Changes** to see the before/after field name diff
4. **Click Approve & Publish** — the backend generates a Micro-PRD (LLM if key is set, template fallback otherwise) and renders it inline

To exercise the privacy proxy directly:

```bash
curl -s -X POST http://localhost:8000/api/v1/proxy/sanitize \
  -H "Content-Type: application/json" \
  -d '{
    "content": "2024-03-12 ERROR [auth] Login failed for john.doe@acme.com token=sk_live_AbCdEf12345678 ip=10.0.0.5",
    "format": "log"
  }' | python -m json.tool
```

The response contains **only structural metadata** — no email, no token, no IP address.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/proxy/sanitize` | Run the privacy proxy on raw text |
| `GET` | `/api/v1/proxy/health` | Check proxy status + NER model availability |
| `GET` | `/api/v1/triage/backlog` | List all backlog items (sorted by severity) |
| `GET` | `/api/v1/triage/backlog/{id}` | Get a single backlog item |
| `POST` | `/api/v1/triage/score` | Score a `SanitizedMetadata` blob |
| `POST` | `/api/v1/triage/relax/{id}` | Preview relaxation controls (no LLM) |
| `POST` | `/api/v1/triage/publish/{id}` | Approve item and generate Micro-PRD |

Full interactive docs: **http://localhost:8000/docs**

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | No | OpenAI key for live LLM scoring and Micro-PRD generation. Falls back to heuristic mode if absent. |

Secrets must never be committed. Use `.env` locally (already in `.gitignore`).

---

## Feature Status

| Feature | Status |
|---|---|
| `privacy-001` Local Privacy Proxy | ✅ Passing — 23 tests |
| `triage-001` AI PM Triage Dashboard | ✅ Passing — 20 tests |
| `sandbox-001` Student Terminal & Micro-PRD | 🔲 Not started |
| `assessor-001` AI Assessor & Scorecard | 🔲 Not started |
