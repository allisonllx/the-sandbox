# Progress Log

## Current Verified State

- Repository root: `/Users/allisonlawlixuan/Documents/repos/the_sandbox`
- Standard startup path: `./init.sh`
- Standard verification path: `python -m pytest backend/tests/ -v`
- Current highest-priority unfinished feature: `factory-001` Phase 2 (optional data plane + per-challenge secret tests)
- Latest passing: Spec-driven briefs + frontend markdown render; **166 tests**
- Current blocker: None

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
- Completed: Full privacy_proxy module, API routes, 23 tests
- Verification run: `python -m pytest backend/tests/test_sanitizer.py -v` → **23 passed**
- Evidence captured: All PII types stripped; zero-trust network test passes
- Commits: none
- Next best step: triage-001

### Session 003

- Date: 2026-06-20
- Goal: Implement triage-001 — AI PM Triage Matrix & Relaxation Control Dashboard
- Completed: ai_pm module, triage routes, startup frontend dashboard, 20 triage tests
- Verification run: **43 passed**
- Commits: none
- Next best step: sandbox-001

### Session 004

- Date: 2026-06-20
- Goal: Implement sandbox-001 — Public Sandbox Terminal & Micro-PRD Framework
- Completed:
  - `backend/sandbox/` — synthesizer (SQLite + 3 anomalies), submission_store, models
  - `backend/api/sandbox_routes.py` — list/get/download/submit endpoints
  - Publish flow now sets `published`, generates dataset
  - `backend/tests/test_sandbox.py` — 8 tests
  - `frontend/app/student/` — challenge browser + workspace page
  - `frontend/components/` — ChallengeCard, MicroPRDView, SandboxTerminal
  - `frontend/DOCS.md`, `backend/sandbox/DOCS.md`
  - Docs: README API table, documentation-sync map, api/DOCS.md
- Verification run: `python -m pytest backend/tests/ -v` → **54 passed**
- Evidence captured: Dataset anomalies verified; Micro-PRD 4 sections via API; submissions received
- Commits: none
- Docs: updated per documentation-sync.md
- Known risk or unresolved issue: Terminal "Run" is mock-only. Assessor not wired yet.
- Next best step: workspace-002 — see feature_list.json implementation_order (Monaco + starter → persistence → validate → submit → run jobs)

### Session 005

- Date: 2026-06-20
- Goal: Merge Student Workspace Design + Workspace Persistence MVP into feature_list.json
- Completed: Added `workspace-002` at priority 4 with ordered implementation_order checklist; bumped assessor-001 to priority 5
- Verification run: n/a (planning only)
- Evidence captured: n/a
- Commits: none
- Docs: no update required — feature_list.json is the planning artifact; ARCHITECTURE.md updates deferred until workspace-002 implementation
- Known risk or unresolved issue: None
- Next best step: workspace-002 task 1 — starter scaffold on publish

### Session 006

- Date: 2026-06-20
- Goal: Implement workspace-002 — Multi-File Workspace, Persistence & Public Test Runner
- Completed:
  - Backend: starter_scaffold, workspace, draft_store, validate, archive, run_jobs; disk submission_store
  - API: starter, workspace/draft, validate, run/jobs, inline + ZIP submit
  - Frontend: ChallengeWorkspace (Monaco), draftStorage (IndexedDB), updated student workspace page
  - Tests: test_draft_store.py, test_run_jobs.py; extended test_sandbox.py
  - Docs: sandbox/DOCS.md, frontend/DOCS.md, api/DOCS.md, ARCHITECTURE.md, README API table
- Verification run: `python -m pytest backend/tests/ -v` → **67 passed**; `npm run typecheck` → OK
- Evidence captured: see feature_list.json workspace-002 evidence array
- Commits: none
- Docs: updated per documentation-sync.md
- Known risk or unresolved issue: init.sh fails on spacy build for Python 3.13; pytest passes with existing env. Run job thread may warn if data/jobs cleared during teardown.
- Next best step: assessor-001 — Docker grading + full technical taste evaluation

### Session 007

- Date: 2026-06-20
- Goal: Multi-Track Innovation Hub (tracks-001 + product-001)
- Completed:
  - Backend: ChallengeTrack/DeliverableType enums, track_router, abstract_brand, track-aware microprd, demo-004 seed
  - Backend: product_starter_scaffold, publish branch, submit links + assessor registry, scorecard API
  - Frontend: Innovation Hub track tabs, ChallengeCard badges, ProductWorkspace, MicroPRDView product sections, ScorecardView
  - Tests: test_tracks.py (8 tests); updated test_triage (4 demo items), test_sandbox (assessed status)
  - Docs: PRODUCT.md, ARCHITECTURE.md, ai_pm/DOCS.md, sandbox/DOCS.md, feature_list.json
- Verification run: `python -m pytest backend/tests/ -v` → **77 passed**; `npm run typecheck` → OK
- Evidence captured: see feature_list.json tracks-001 and product-001 evidence arrays
- Commits: none
- Docs: updated per documentation-sync.md
- Known risk or unresolved issue: Technical assessor is structure stub only; Docker harness deferred to assessor-001
- Next best step: assessor-001 — isolated Docker runner + LLM taste layer

### Session 008

- Date: 2026-06-20
- Goal: Defensive Business Model hybrid hackathon demo (trust-001, rewards-001, rank-001)
- Completed:
  - scope_guard.py + demo-007 rejection; domain_obfuscator.py + demo-005 StealthCo; demo-006 Platform Pool
  - ChallengeReward lock gate on publish; RelaxationPanel reward + domain preview; student bounty badges
  - /student/leaderboard + /enterprise/radar stub pages; execution_points on scorecard
  - test_trust.py; docs PRODUCT.md defensive posture + README judge script
- Verification run: `python -m pytest backend/tests/ -v` → **81 passed**; `npm run typecheck` → OK
- Docs: updated per documentation-sync.md
- Commits: none
- Next best step: assessor-001

### Session 009

- Date: 2026-06-20
- Goal: blind-002 — Blind Audition Company Tech Profile
- Completed:
  - CompanyTechProfile model + company_profile.py generator (red sensitivity omits industry)
  - public_sanitize.py + build_public_challenge — student API strips brand_proxy, sanitizes Micro-PRD/evaluation_focus
  - Publish/relax wire company_profile; domain obfuscator public titles without fictional brand names
  - Frontend: ChallengeCard, MicroPRDView, RelaxationPanel profile preview, /student/trust
  - Anonymized leaderboard + enterprise radar copy
  - test_blind_audition.py (7 tests); README judge script; PRODUCT.md; feature_list.json blind-002
- Verification run: blind audition + trust + tracks tests → **21 passed**; `npm run typecheck` → OK
- Docs: backend/ai_pm/DOCS.md, docs/PRODUCT.md, README.md
- Commits: none
- Next best step: assessor-001

### Session 010

- Date: 2026-06-20
- Goal: Documentation sync — publish draft, three rank surfaces, blind audition architecture
- Completed:
  - PublishDraft flow: `publish_draft.py`, `PublishDraftEditor`, relax/publish `draft` wiring (prior session code; docs now synced)
  - Three rank surfaces: student leaderboard, sponsor matches, enterprise radar (prior session code; docs now synced)
  - Updated: docs/ARCHITECTURE.md, docs/PRODUCT.md, docs/api-patterns.md, README.md API table + feature status
  - Updated: backend/api/DOCS.md, backend/sandbox/DOCS.md, frontend/DOCS.md
- Verification run: `python -m pytest backend/tests/ -q` → **96 passed**
- Docs: updated per documentation-sync.md (all rows for touched modules)
- Commits: none
- Next best step: assessor-001 — Docker harness + full technical grading

### Session 011

- Date: 2026-06-20
- Goal: assessor-001 schema split — dual-layer Platform Signal + Sponsor Fit
- Completed:
  - backend/assessor/models.py, platform_*.py, sponsor_*.py, registry refactor
  - execution_points from platform only; Match Radar sorts by sponsor_fit_score
  - ScorecardView + types.ts dual sections; startup matches UI updated
  - test_assessor_layers.py (5 tests); feature_list.json assessor-001 phased
  - Docs: assessor/DOCS.md, ARCHITECTURE, PRODUCT, api-patterns, documentation-sync
- Verification run: `python -m pytest backend/tests/ -q` → **101 passed**; `npm run typecheck` → OK
- Docs: updated per documentation-sync.md
- Commits: none
- Next best step: assessor-001 Phase A — Docker harness + platform_technical secret tests

### Session 012

- Date: 2026-06-20
- Goal: assessor-001 Phase A — Docker harness + platform secret tests
- Completed:
  - docker/sandbox-runner/Dockerfile + backend/assessor/docker_runner.py
  - secret_tests/test_secret.py (not in starter scaffold)
  - security_scan.py static baseline; platform_technical wired to Docker
  - test_docker_assessor.py (6 tests)
- Verification run: `python -m pytest backend/tests/ -q` → **107 passed**
- Docs: assessor/DOCS.md, ARCHITECTURE.md, README.md docker build step
- Commits: none
- Next best step: assessor-001 Phase B — LLM sponsor fit layer

### Session 013

- Date: 2026-06-20
- Goal: assessor-001 Phase B — LLM sponsor fit layer
- Completed:
  - backend/assessor/sponsor_fit.py — LLM JSON scoring + heuristic fallback
  - Extended ChallengeContext with sanitized Micro-PRD fields
  - test_sponsor_fit_llm.py (6 tests); brand_proxy excluded from LLM payload
  - feature_list.json assessor-001 → passing
- Verification run: `python -m pytest backend/tests/ -q` → **113 passed**
- Docs: assessor/DOCS.md, README.md feature status
- Commits: none
- Next best step: pick next feature from feature_list.json (all MVP features passing)

### Session 014

- Date: 2026-06-20
- Goal: README refresh — stakeholders, dual-layer flow, blind audition, rank surfaces
- Completed: Rewrote README.md (stakeholder table, end-to-end flow, ingest API, deferred items)
- Docs: README.md — real vs demo disclaimer, shortened API ref
- Verification run: n/a (docs only)
- Commits: none

### Session 015

- Date: 2026-06-20
- Goal: llm-local-001 — local vLLM (Qwen) routing with OpenAI fallback
- Completed:
  - `backend/ai_pm/llm_client.py` — `RoutingLLMClient`, `LLMTier.sensitive` / `standard`
  - `backend/ai_pm/llm_domain_obfuscator.py` — LLM mask for novel domains
  - Wired into `domain_obfuscator.py`; scorer/microprd/sponsor_fit use sensitive tier
  - `test_llm_routing.py` (5), `test_llm_domain_obfuscator.py` (3)
- Verification run: `python -m pytest backend/tests/ -q` → **121 passed**
- Docs: README vLLM quickstart + env table, `backend/ai_pm/DOCS.md`, `docs/ARCHITECTURE.md`
- Docs: no update required for api-patterns — no HTTP contract change
- Commits: none
- Next best step: run vLLM locally and smoke-test triage with `LLM_BASE_URL` set

### Session 016

- Date: 2026-06-21
- Goal: factory-001 Phase 1 — Dynamic Challenge Factory (Preview → Review → Publish)
- Completed:
  - `backend/challenge_factory/` — blueprint planner, multi-archetype scaffolds, validator, builder
  - `ChallengeBlueprint` + `ChallengePackage` on `BacklogItem`; founder `RelaxRequest.blueprint`
  - `POST /relax` generates package for non-demo items; `POST /regenerate`; publish requires valid package
  - Legacy bypass for `demo-*` and product track (`CHALLENGE_FACTORY_MODE=auto`)
  - `test_challenge_factory.py` (10 tests); frontend types for package preview
- Verification run: `python -m pytest backend/tests/ -q` → **136 passed**
- Docs: `backend/challenge_factory/DOCS.md`, `backend/api/DOCS.md`, `docs/documentation-sync.md`, `frontend/lib/types.ts`
- Commits: none
- Next best step: factory-001 Phase 2 — schema/fixture agents + per-challenge secret tests

### Session 017

- Date: 2026-06-21
- Goal: Founder ingest (Option 1) + upload UI + documentation sync
- Completed:
  - `POST /triage/intake` — local sanitize + score for problem briefs
  - `/startup/upload` + `/startup/upload/loading` — logs or task description
  - `scripts/factory_intake.sh`, blueprint/README sync fix in challenge_factory
  - Docs: README, ARCHITECTURE, PRODUCT, api/DOCS, ai_pm/DOCS, scripts/README, feature_list intake-001
- Verification run: `python -m pytest backend/tests/ -q` → **139 passed**
- Docs: full documentation-sync pass for intake + factory + upload flows
- Commits: none
- Next best step: factory-001 Phase 2

### Session 018

- Date: 2026-06-21
- Goal: Standardise module documentation naming to `DOCS.md`
- Completed:
  - Renamed `scripts/README.md` → `scripts/DOCS.md`
  - Renamed `samples/demo_solutions/README.md` → `samples/demo_solutions/DOCS.md`
  - Updated links in README, api-patterns, challenge_factory/DOCS, documentation-sync, AGENTS.md
  - Documented convention: root `README.md` only; code folders use `DOCS.md`; challenge starter `README.md` unchanged
- Verification run: none (docs-only)
- Docs: documentation-sync.md naming section + full module list
- Commits: none
- Next best step: factory-001 Phase 2

### Session 019

- Date: 2026-06-21
- Goal: TechnicalChallengeSpec redesign — single-pass inference, dynamic scaffolds, 8 archetypes
- Completed:
  - `TechnicalChallengeSpec` + expanded `TechnicalArchetype` enum; optional `BacklogItem.challenge_spec`
  - Single-pass `generate_spec()` + heuristic fallback (`challenge_spec.py`, `archetype_catalog.py`)
  - Spec-driven pipeline: `scaffold_interpolate.py`, `spec_projection.py`, `legacy_spec_adapter.py`
  - Triage relax/publish wired: spec → package → `spec_to_microprd` before persist
  - Scripts: `ARCHETYPE=auto` default; omit blueprint when auto
  - Tests: `test_challenge_spec.py`, `test_scaffold_interpolate.py`, `test_legacy_spec_adapter.py`; factory payment-retry assertions updated
- Verification run: `python -m pytest backend/tests/ -q` → **160 passed**
- Docs: `backend/challenge_factory/DOCS.md` (Session 019); full sync in Session 020
- Commits: none
- Known risk: LLM stub still returns scorer JSON — heuristic path is hot path when LLM unavailable; physical `.tpl` files deferred (Python catalog drives interpolation)
- Next best step: factory-001 Phase 2 — per-challenge secret tests + optional fixture LLM pass

### Session 020

- Date: 2026-06-21
- Goal: Documentation sync — TechnicalChallengeSpec, archetype samples, product vs technical factory paths
- Completed: Updated AGENTS.md, README.md, ARCHITECTURE.md, PRODUCT.md, api-patterns.md, documentation-sync.md, all touched module DOCS (ai_pm, api, prompts, tests, scripts, samples)
- Verification run: n/a (docs-only)
- Docs: full pass per documentation-sync.md
- Commits: none
- Next best step: factory-001 Phase 2

### Session 021

- Date: 2026-06-21
- Goal: Fix generic stream_parser (and spec-driven) student briefs
- Completed:
  - `format_spec_context` + `spec_success_criteria` in `spec_projection.py` — assignment-style context/DoD from spec
  - Relax builds `PublishDraft` after spec projection (fixes stale package hash + generic draft)
  - Publish applies founder `PublishDraft` on top of spec-projected Micro-PRD
  - Student sandbox API skips legacy `microprd_enrich` when `challenge_spec` is set
  - Richer `stream_parser` heuristic defaults in `archetype_catalog.py`
  - Tests: `test_spec_projection.py`, `test_stream_parser_brief_is_specific_end_to_end`
- Verification run: `python -m pytest backend/tests/ -q` → **165 passed**
- Docs: `backend/challenge_factory/DOCS.md`, `backend/api/DOCS.md`, `backend/tests/DOCS.md`
- Commits: none
- Next best step: factory-001 Phase 2

### Session 022

- Date: 2026-06-21
- Goal: Add typed I/O examples to challenge briefs (incl. what a "line" looks like)
- Completed:
  - `SpecExample` model + `examples` on `TechnicalChallengeSpec`
  - `challenge_spec.py` prompt requires 2–4 typed examples (PEP 484 signatures, literal I/O)
  - `format_spec_examples()` in student brief + `docs/SPEC.md` projection
  - `_brief_examples_for()` heuristic catalog per archetype; `parse_lines` → `Iterable[str]`
  - Tests: `test_stream_parser_brief_includes_typed_examples`
- Verification run: spec + factory tests → **15 passed**
- Docs: `backend/prompts/DOCS.md`, `backend/challenge_factory/DOCS.md`
- Commits: none
- Next best step: factory-001 Phase 2

### Session 023

- Date: 2026-06-21
- Goal: Frontend markdown brief rendering + documentation sync
- Completed:
  - `BriefMarkdown`, `BriefMarkdownInline`, `BriefSectionBody`, `BriefAsideSection` — student left panel renders markdown (all Micro-PRD sections + anomalies/evaluation focus)
  - Full doc sync: `frontend/DOCS.md`, `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/api-patterns.md`, `docs/documentation-sync.md`, `AGENTS.md`, `README.md`, `backend/challenge_factory/DOCS.md`, `backend/ai_pm/DOCS.md`, `backend/api/DOCS.md`
- Verification run: `npm run typecheck` (frontend) → pass
- Docs: full pass per documentation-sync.md
- Commits: none
- Next best step: factory-001 Phase 2
