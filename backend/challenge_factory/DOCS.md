# Challenge Factory

Generates per-challenge starter files from **TechnicalChallengeSpec** (single-pass inference) at Preview time.

## Flow (spec-driven)

1. Ingest → sanitize → score
2. `POST /triage/relax/{id}` — `generate_spec()` (one LLM call or heuristic) → `build_package(challenge_spec=…)`
3. `spec_to_microprd()` projects student brief **before** persist (spec is source of truth)
4. `generate_scaffold_from_spec()` interpolates stubs/tests from `interface_contract.public_api`
5. Founder reviews `challenge_package` + optional `challenge_spec` in response
6. `POST /triage/publish/{id}` — activates pre-validated package

```mermaid
flowchart LR
  ingest[SanitizedMetadata] --> specGen[generate_spec]
  specGen --> interpolate[scaffold_interpolate]
  interpolate --> validate[pytest validate]
  specGen --> microprd[spec_to_microprd]
  validate --> preview[Preview response]
  microprd --> preview
```

## Legacy bypass

| Condition | Path |
|---|---|
| `demo-*` item IDs | Hardcoded `starter_scaffold` + `synthesizer`; `legacy_spec_adapter` supplies runtime spec |
| `product_feature` track | Hardcoded product scaffold (until Phase 3) |
| `CHALLENGE_FACTORY_MODE=legacy\|dynamic\|auto` | Env override (`auto` = table above) |

## Module map

| File | Role |
|---|---|
| `models.py` | `TechnicalArchetype`, `ChallengeBlueprint`, `ChallengePackage` |
| `spec_models.py` | `TechnicalChallengeSpec`, `InterfaceContract` |
| `challenge_spec.py` | Single-pass `generate_spec()` + heuristic fallback |
| `archetype_catalog.py` | Per-archetype defaults, reference bodies, trigger inference |
| `scaffold_interpolate.py` | Dynamic stubs/tests from spec signatures |
| `spec_projection.py` | `spec_to_microprd`, `spec_to_blueprint`, `spec_to_readme` |
| `legacy_spec_adapter.py` | `resolve_challenge_spec()` for demo-* without store mutation |
| `legacy_router.py` | `use_legacy_factory()` |
| `blueprint_planner.py` | Legacy LLM blueprint (fallback when no spec) |
| `scaffold_technical.py` | Legacy archetype templates |
| `validator.py` | Syntax, security scan, pytest on `tests/` |
| `builder.py` | `build_package()`, staleness hash |

## Technical archetypes (Phase 1)

Sweet-spot system modules (auto-selected from ingest signals):

- `webhook_handler`, `idempotency_engine`, `data_adapter`, `cli_instrumentation`
- `data_masking`, `circuit_breaker`, `stream_parser`, `rls_proxy`

Explicit / legacy:

- `algorithm` — founder override only (never auto from retry logs)
- `data_core` — SQLite query path (`demo-003`)
- `integration`, `service_module`, `data_adjacent` — legacy aliases (normalized on read)

## Founder controls (API)

`RelaxRequest.blueprint.archetype` forces classification before scaffold (e.g. `algorithm` override).

Omit blueprint (or `ARCHETYPE=auto` in scripts) to let ingest signals choose the archetype.

`BacklogItem.challenge_spec` is optional — persisted after Preview for dynamic items.

## Consistency rule

**spec ↔ docs/SPEC.md ↔ interpolated tests ↔ Micro-PRD** must agree on edit targets and public API symbols. Validator + `validate_contract_alignment()` enforce this.

## Browser workspace sufficiency

| `data_plane` | Required in starter | Run Public Tests |
|---|---|---|
| `none` | `docs/SPEC.md`, self-contained tests | Student files only |
| `sqlite` | `docs/DATA.md` + `docs/SPEC.md` | Platform mounts `sandbox.sqlite` |

See [`../ai_pm/DOCS.md`](../ai_pm/DOCS.md) and [`../../scripts/DOCS.md`](../../scripts/DOCS.md).
