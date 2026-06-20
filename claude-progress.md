# Progress Log

## Current Verified State

- Repository root: `/Users/allisonlawlixuan/Documents/repos/the_sandbox`
- Standard startup path: `./init.sh`
- Standard verification path: `python -m pytest backend/tests/test_sanitizer.py -v`
- Current highest-priority unfinished feature: `sandbox-001` — Public Sandbox Terminal & Micro-PRD Framework
- Current blocker: None. `privacy-001` is passing. spaCy model (`en_core_web_sm`) not yet downloaded — run `python -m spacy download en_core_web_sm` to enable NER entity counting (all other tests pass without it).

## Session Log

### Session 001

- Date: 2026-06-20
- Goal: Scaffold repo context files from PRD
- Completed: Created AGENTS.md, feature_list.json, claude-progress.md, init.sh, session-handoff.md, clean-state-checklist.md, evaluator-rubric.md, docs/ARCHITECTURE.md, docs/PRODUCT.md
- Verification run: n/a (no code yet)
- Evidence captured: n/a
- Commits: none
- Files or artifacts updated: all context files created fresh
- Known risk or unresolved issue: Tech stack not yet locked
- Next best step: Confirm tech stack, begin privacy-001

### Session 002

- Date: 2026-06-20
- Goal: Implement privacy-001 — Local Privacy Proxy & Sanitization Engine
- Completed:
  - `backend/` directory structure (privacy_proxy/, api/, tests/fixtures/)
  - `backend/privacy_proxy/models.py` — Pydantic models (SanitizeRequest, SanitizedMetadata, etc.)
  - `backend/privacy_proxy/pii_patterns.py` — regex PII detection (email, phone, JWT, AWS key, Stripe SDK key, IPv4, generic api_key, private key blocks)
  - `backend/privacy_proxy/ner_engine.py` — spaCy local NER wrapper with graceful degradation
  - `backend/privacy_proxy/structural_extractor.py` — JSON / CSV / log structural metadata extraction
  - `backend/privacy_proxy/sanitizer.py` — main pipeline orchestrator (guardrail → scrub → NER → extract)
  - `backend/api/routes.py` + `backend/main.py` — FastAPI endpoint POST /api/v1/proxy/sanitize
  - `backend/tests/test_sanitizer.py` — 23 tests covering all verification checklist items
  - `backend/requirements.txt`
- Verification run: `python -m pytest backend/tests/test_sanitizer.py -v` → **23 passed**
- Evidence captured: All PII types stripped; no raw content in output; zero-trust network test passes
- Commits: none
- Files or artifacts updated: feature_list.json (privacy-001 → passing)
- Known risk or unresolved issue: spaCy model not yet downloaded (optional for NER entity counts)
- Next best step: Begin `sandbox-001` — Public Sandbox Terminal & Micro-PRD Framework.

### Session 003

- Date: 2026-06-20
- Goal: Implement triage-001 — AI PM Triage Matrix & Relaxation Control Dashboard
- Completed:
  - `backend/ai_pm/models.py` — TechScores, SensitivityTag, RelaxationConfig, BacklogItem, MicroPRD, all API request/response shapes
  - `backend/ai_pm/llm_client.py` — injectable OpenAI wrapper with LLMUnavailableError, module-level singleton for testing
  - `backend/ai_pm/scorer.py` — LLM scorer (sends anonymized metadata only) + heuristic fallback
  - `backend/ai_pm/relaxation.py` — pure relaxation controls (abstract logic, variable synthesizer, noise injector)
  - `backend/ai_pm/microprd.py` — LLM Micro-PRD generator with template fallback
  - `backend/ai_pm/store.py` — in-memory backlog store pre-seeded with 3 demo items (red/yellow/green)
  - `backend/api/triage_routes.py` — GET /backlog, POST /score, POST /relax/{id}, POST /publish/{id}
  - `backend/main.py` — triage router registered
  - `backend/tests/test_triage.py` — 20 tests
  - `frontend/` — Next.js 14 + Tailwind CSS + TypeScript scaffolded
  - `frontend/app/startup/page.tsx` — split-screen CTO dashboard
  - `frontend/components/BacklogCard.tsx`, `RelaxationPanel.tsx`, `SensitivityBadge.tsx`, `ScoreBar.tsx`
  - `frontend/lib/api.ts`, `lib/types.ts`
- Verification run: `python -m pytest backend/tests/ -v` → **43 passed** (privacy-001 + triage-001)
- Evidence captured: All relaxation controls verified deterministic; no LLM called before approval; all 3 sensitivity tiers covered
- Commits: none
- Files or artifacts updated: feature_list.json (triage-001 → passing), requirements.txt (+openai)
- Known risk or unresolved issue: Frontend needs `npm install` before first run. OPENAI_API_KEY needed for live LLM scoring; heuristic fallback works without it.
- Next best step: `sandbox-001` — student-facing challenge browser + interactive terminal
