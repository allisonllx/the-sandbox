# Assessor

## Purpose

Dual-layer submission grading:

- **Platform Signal** — track-standard, objective rubric; feeds **Execution Points** (global student rank + enterprise radar)
- **Sponsor Fit** — challenge-specific criteria alignment; feeds **Match Radar** only (`/startup/matches/{id}`)

## Contents

| File | Role |
|---|---|
| `models.py` | `ScoreLayer`, `ChallengeContext`, `build_dual_layer_scorecard` |
| `platform_technical.py` | Track-standard technical dimensions (Docker tests in Phase A) |
| `platform_product.py` | Structural deliverable rubric (no challenge-specific keywords) |
| `sponsor_technical.py` | Criteria/taste fit per challenge (LLM in Phase B) |
| `sponsor_product.py` | Persona/problem framing fit per challenge |
| `registry.py` | `assess_submission()` — orchestrates both layers |

## Scorecard shape

```json
{
  "platform": { "dimensions": {}, "score": 91, "summary": "...", "notes": [] },
  "sponsor": { "dimensions": {}, "score": 80, "summary": "...", "notes": [] },
  "execution_points": 109,
  "sponsor_fit_score": 80,
  "platform_score": 91,
  "dimensions": { "...": "platform.dimensions alias" }
}
```

## How It Fits In

Called from `api/sandbox_routes.py` on submit with `challenge_item` for sponsor context. `sponsor_matches.py` sorts by `sponsor_fit_score`.

## assessor-001 phases

| Phase | Scope | Status |
|---|---|---|
| **Schema + split** | Dual-layer scorecard, heuristic platform/sponsor assessors | Done |
| **Phase A** | Docker harness + secret tests → `platform_technical` | Not started |
| **Phase B** | LLM sponsor fit from sanitized Micro-PRD + evaluation_focus | Not started |

## Notes for the Next Session

- Interview pass requires **both** platform score and sponsor fit ≥ benchmark
- Do not add challenge-specific keyword checks to platform assessors
- LLM sponsor fit must receive sanitized challenge context only — never `brand_proxy`
