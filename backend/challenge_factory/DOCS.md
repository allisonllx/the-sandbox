# Challenge Factory

Generates per-challenge starter files from Micro-PRD + **ChallengeBlueprint** at Preview time.

## Flow

1. `POST /triage/relax/{id}` — relaxation + Micro-PRD + factory (non-legacy items)
2. Founder reviews `challenge_package` in response (starter tree + validation)
3. `POST /triage/regenerate/{id}` — re-run after draft/blueprint edits
4. `POST /triage/publish/{id}` — activates pre-validated package (no generation)

## Legacy bypass

| Condition | Path |
|---|---|
| `demo-*` item IDs | Hardcoded `starter_scaffold` + `synthesizer` |
| `product_feature` track | Hardcoded product scaffold (until Phase 3) |
| `CHALLENGE_FACTORY_MODE=legacy\|dynamic\|auto` | Env override (`auto` = table above) |

## Module map

| File | Role |
|---|---|
| `models.py` | `ChallengeBlueprint`, `ChallengePackage`, `ValidationReport` |
| `legacy_router.py` | `use_legacy_factory()` |
| `blueprint_planner.py` | Infer archetype + data plane (LLM + heuristic) |
| `scaffold_technical.py` | Archetype templates + optional LLM scaffold |
| `validator.py` | Syntax, security scan, pytest on `tests/` |
| `builder.py` | `build_package()`, staleness hash |

## Technical archetypes

- `algorithm` — pure logic, no DB
- `service_module` — single module/class focus
- `integration` — multi-module wiring
- `data_adjacent` — data helpers optional
- `data_core` — query/SQLite focus (uses legacy synthesizer when `data_plane=sqlite`)

## Founder controls (API)

`RelaxRequest.blueprint`:

- `archetype`, `primary_focus`, `data_plane`
- `stack_guidance`, `starter_hints` (Phase 1 text hints)
- `edit_targets` (optional override)

`reference_solution` is stored on `BacklogItem.challenge_package` but stripped from API JSON responses.

## PRD ↔ starter sync

- `finalize_starter_package()` aligns README + blueprint `edit_targets` with generated files.
- `ai_pm.microprd.sync_with_blueprint()` updates Micro-PRD `structural_constraints` and `sandbox_instructions` to match — runs at Preview/Publish and in the student challenge API.

## Browser workspace sufficiency

Students use the in-browser editor — they must not need opaque local downloads to
understand data or run public tests.

| `data_plane` | Required in starter | Run Public Tests |
|---|---|---|
| `none` | Self-contained tests (no sqlite skip fixtures) | Student files only |
| `sqlite` | `docs/DATA.md` schema reference | Platform mounts `sandbox.sqlite` |

Validator: `workspace_sufficiency.check_browser_workspace_sufficiency()`.
Run jobs: `run_jobs.enqueue_run(..., dataset_path=...)` copies DB into temp workspace.

## Upstream: founder ingest

Backlog items reach the factory after:

| Path | Endpoint / UI |
|---|---|
| Upload UI | `/startup/upload` → `POST /proxy/sanitize` + `POST /triage/score` |
| Quick intake | `POST /triage/intake` or sidebar on `/startup` |
| Scripts | `./scripts/factory_intake.sh` / `factory_pipeline.sh` |

See [`../ai_pm/DOCS.md`](../ai_pm/DOCS.md) and [`../../scripts/DOCS.md`](../../scripts/DOCS.md).
