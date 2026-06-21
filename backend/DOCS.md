# Backend

## Purpose

FastAPI application for The Sandbox. Hosts the zero-trust privacy proxy, AI PM triage layer, and (planned) assessor engine. All startup-side sensitive processing runs here before any anonymized metadata crosses to external LLM APIs.

## Contents

| Path | Role |
|---|---|
| `main.py` | FastAPI app entry point — mounts routers, CORS |
| `requirements.txt` | Pinned Python dependencies |
| `privacy_proxy/` | Local sanitization pipeline (PII scrubbing, NER, structural extraction) |
| `ai_pm/` | Backlog scoring, relaxation controls, Micro-PRD generation |
| `prompts/` | Cross-module LLM system prompts (ai_pm + assessor) |
| `assessor/` | Dual-layer platform signal + sponsor fit grading |
| `sandbox/` | Synthetic dataset generator, public challenges, submission queue |
| `api/` | HTTP route handlers |
| `tests/` | pytest suite (54 tests) |

## How It Fits In

The frontend proxies `/api/*` to this server on port 8000. The privacy proxy is the trust boundary — downstream modules (`ai_pm/`) must only consume `SanitizedMetadata`, never raw ingest text.

## Notes for the Next Session

- Start with: `python -m uvicorn backend.main:app --reload --port 8000`
- Run tests from repo root: `python -m pytest backend/tests/ -v`
- `OPENAI_API_KEY` is optional — scorer and Micro-PRD generator fall back to heuristics/templates
- Read `docs/api-patterns.md` before adding endpoints
- After code changes, check `docs/documentation-sync.md` for which docs to update
