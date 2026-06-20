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
| `sponsor_technical.py` | Criteria/taste fit per challenge (LLM in Phase B) |
| `sponsor_product.py` | Persona/problem framing fit per challenge |
| `registry.py` | `assess_submission()` — orchestrates both layers |

## Docker runner

Build once:

```bash
docker build -t the-sandbox-runner docker/sandbox-runner
```

Container flags: `--network none`, `--memory 512m`, `--cpus 1.0`, `--cap-drop ALL`, `--security-opt no-new-privileges`.

Student code is written to a temp workspace, dataset copied as `sandbox.sqlite`, secret tests mounted read-only at `/secret_tests/test_secret.py`.

If Docker is unavailable, platform technical scoring degrades (static security scan only — **no host execution** of student code).

## assessor-001 phases

| Phase | Scope | Status |
|---|---|---|
| **Schema + split** | Dual-layer scorecard, heuristic platform/sponsor assessors | Done |
| **Phase A** | Docker harness + secret tests → `platform_technical` | Done |
| **Phase B** | LLM sponsor fit from sanitized Micro-PRD + evaluation_focus | Not started |

## Notes for the Next Session

- Interview pass requires **both** platform score and sponsor fit ≥ benchmark
- Do not add challenge-specific keyword checks to platform assessors
- LLM sponsor fit must receive sanitized challenge context only — never `brand_proxy`
