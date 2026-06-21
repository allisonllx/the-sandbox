# Prompts

## Purpose

Central registry of LLM system prompts used across backend modules. Keeps prompt text out of business logic and avoids nesting assessor prompts under `ai_pm/`.

## Contents

| File | Used by | Role |
|---|---|---|
| `shared.py` | All prompt modules | Reusable fragments (JSON-only, blind audition, metadata boundary) |
| `scorer.py` | `ai_pm/scorer.py` | Triage rubric + yes/no signals |
| `scorer_validation.py` | `ai_pm/scorer.py` | Signal ↔ score consistency checks |
| `microprd.py` | `ai_pm/microprd.py` | Technical + product Micro-PRD prompts |
| `domain_obfuscator.py` | `ai_pm/llm_domain_obfuscator.py` | LLM domain masking for novel industries |
| `sponsor_fit.py` | `assessor/sponsor_fit.py` | Technical + product sponsor fit rubrics |

## How It Fits In

Call sites import constants only — user payload builders and response parsers stay in the calling module. LLM routing lives in `ai_pm/llm_client.py`.

## Notes for the Next Session

- Add new prompts as one file per call site under this folder
- Shared tone/safety rules belong in `shared.py`
- Triage responses with a `signals` block are validated in `scorer_validation.py`
