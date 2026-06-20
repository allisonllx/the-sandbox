# The Sandbox

A zero-trust, two-sided R&D and proof-of-work talent platform. Startups turn their messy internal backlogs into safe, publishable coding challenges. Students solve those challenges to prove real-world engineering capability without résumés, referrals, or recruiting filters.

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
| Testing | pytest · 54 tests |
| Code Runner | Docker (ephemeral containers) — planned for `assessor-001` |

---

## Project Structure

Subfolder layout with one-line roles. File-level detail lives in each folder's `DOCS.md`.

```
the_sandbox/
├── backend/                    # FastAPI app → backend/DOCS.md
│   ├── privacy_proxy/          # PII scrubbing, NER, structural extraction
│   ├── ai_pm/                  # Triage scoring, relaxation, Micro-PRD
│   ├── sandbox/                # Synthetic datasets, submission queue
│   ├── api/                    # HTTP routes (proxy, triage, sandbox)
│   ├── tests/                  # pytest suite
│   ├── main.py
│   └── requirements.txt
├── frontend/                   # Next.js app → frontend/DOCS.md
│   ├── app/startup/            # CTO triage dashboard
│   ├── app/student/            # Challenge browser + workspace
│   ├── components/
│   └── lib/                    # API client, TypeScript types
├── docs/                       # Architecture, product, API conventions
├── AGENTS.md
├── feature_list.json
├── claude-progress.md
└── init.sh
```

Module docs: [`backend/privacy_proxy/DOCS.md`](backend/privacy_proxy/DOCS.md), [`backend/ai_pm/DOCS.md`](backend/ai_pm/DOCS.md), [`backend/sandbox/DOCS.md`](backend/sandbox/DOCS.md), [`backend/api/DOCS.md`](backend/api/DOCS.md), [`backend/tests/DOCS.md`](backend/tests/DOCS.md), [`frontend/DOCS.md`](frontend/DOCS.md)

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

Expected output: **54 passed**.

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
| `POST` | `/api/v1/triage/publish/{id}` | Publish challenge, generate Micro-PRD + dataset |
| `GET` | `/api/v1/sandbox/challenges` | List published public challenges |
| `GET` | `/api/v1/sandbox/challenges/{id}` | Get challenge with Micro-PRD |
| `GET` | `/api/v1/sandbox/challenges/{id}/dataset` | Download synthetic SQLite dataset |
| `GET` | `/api/v1/sandbox/challenges/{id}/starter` | Multi-file starter scaffold (JSON) |
| `GET` | `/api/v1/sandbox/challenges/{id}/starter/download` | Starter scaffold as ZIP |
| `GET` | `/api/v1/sandbox/challenges/{id}/workspace` | Bootstrap workspace session + load draft |
| `PUT` | `/api/v1/sandbox/challenges/{id}/draft` | Save workspace draft |
| `POST` | `/api/v1/sandbox/validate` | Python syntax diagnostics for Monaco |
| `POST` | `/api/v1/sandbox/challenges/{id}/run` | Enqueue public test run (async) |
| `GET` | `/api/v1/sandbox/jobs/{id}` | Poll run job output |
| `POST` | `/api/v1/sandbox/challenges/{id}/submit` | Submit inline multi-file solution |
| `POST` | `/api/v1/sandbox/challenges/{id}/submit/zip` | Submit ZIP archive (raw body) |

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
| `sandbox-001` Student Terminal & Micro-PRD | ✅ Passing — 8 tests |
| `workspace-002` Multi-File Workspace & Persistence | ✅ Passing — 13 new tests (67 total) |
| `assessor-001` AI Assessor & Scorecard | 🔲 Not started |
