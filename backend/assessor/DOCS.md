# Assessor

## Purpose

Dual-layer submission grading:

- **Platform Signal** — track-standard, objective rubric; feeds **Execution Points** (global student rank + enterprise radar)
- **Sponsor Fit** — challenge-specific criteria alignment; feeds **Match Radar** only (`/startup/matches/{id}`)

## Contents

| File | Role |
|---|---|
| `models.py` | `ScoreLayer`, `ChallengeContext`, `build_dual_layer_scorecard` |
| `docker_runner.py` | Ephemeral Docker execution for secret tests (no network, resource limits) |
| `security_scan.py` | Static forbidden-pattern scan before container run |
| `secret_tests/test_secret.py` | Platform secret tests — **never** in starter scaffold |
| `platform_technical.py` | Platform dimensions from Docker + security scan |
| `platform_product.py` | Structural deliverable rubric (no challenge-specific keywords) |
| `sponsor_fit.py` | LLM sponsor fit + heuristic fallback (technical + product) |
| `sponsor_technical.py` | Thin delegate to `sponsor_fit` |
| `sponsor_product.py` | Thin delegate to `sponsor_fit` |
| `registry.py` | `assess_submission()` — orchestrates both layers |

## Sponsor Fit LLM

System prompts live in `ai_pm/prompts/sponsor_fit.py`. Uses sanitized challenge payload only:

- Title, context, definition of success, evaluation focus, structural constraints
- Truncated student submission files (no `brand_proxy`, no corporate metadata)

Falls back to deterministic heuristics when `OPENAI_API_KEY` is absent.

## Docker runner

Build once:

```bash
docker build -t the-sandbox-runner docker/sandbox-runner
```

If Docker is unavailable, platform technical scoring degrades (static security scan only — **no host execution** of student code).

## Notes for the Next Session

- Interview pass requires **both** platform score and sponsor fit ≥ benchmark
- Do not add challenge-specific keyword checks to platform assessors
- Wire live global leaderboard aggregation from platform EP (optional polish)
