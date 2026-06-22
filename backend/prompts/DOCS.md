# Prompts

## Purpose

Central registry of LLM system prompts used across backend modules. Keeps prompt text out of business logic and avoids nesting assessor prompts under `ai_pm/`.

## Contents

| File | Used by | Role |
|---|---|---|
| `shared.py` | All prompt modules | Reusable fragments (JSON-only, blind audition, metadata boundary) |
| `challenge_spec.py` | `challenge_factory/challenge_spec.py` | **Hot path** — single-pass archetype + full `TechnicalChallengeSpec` JSON |
| `scorer.py` | `ai_pm/scorer.py` | Triage rubric + yes/no signals |
| `scorer_validation.py` | `ai_pm/scorer.py` | Signal ↔ score consistency checks |
| `microprd.py` | `ai_pm/microprd.py` | Product track Micro-PRD; technical fallback when spec projection unavailable |
| `blueprint_planner.py` | `challenge_factory/blueprint_planner.py` | Legacy LLM blueprint (off hot path — superseded by spec inference) |
| `scaffold_technical.py` | `challenge_factory/scaffold_technical.py` | Legacy LLM scaffold (off hot path — superseded by `scaffold_interpolate.py`) |
| `domain_obfuscator.py` | `ai_pm/llm_domain_obfuscator.py` | LLM domain masking for novel industries |
| `sponsor_fit.py` | `assessor/sponsor_fit.py` | Technical + product sponsor fit rubrics |

## How It Fits In

Call sites import constants only — user payload builders and response parsers stay in the calling module. LLM routing lives in `ai_pm/llm_client.py`.

**Dynamic technical factory (Preview):**

```
ingest metadata → challenge_spec.py prompt → TechnicalChallengeSpec
  → scaffold_interpolate (no LLM for signatures)
  → spec_projection.spec_to_microprd (deterministic brief + typed examples)
```

Heuristic fallback in `archetype_catalog.py` mirrors the prompt's trigger matrix when LLM is unavailable.

- `examples` is **required** in LLM output (2–4 typed I/O cases); heuristic path uses `_brief_examples_for()` in `archetype_catalog.py`
- Student `microprd.context` is markdown; frontend `BriefMarkdown` renders the subset (see `frontend/DOCS.md`)

## Notes for the Next Session

- Add new prompts as one file per call site under this folder
- Shared tone/safety rules belong in `shared.py`
- Triage responses with a `signals` block are validated in `scorer_validation.py`
- New archetypes: extend trigger matrix in `challenge_spec.py` **and** `archetype_catalog.py`
