# AI PM

## Purpose

AI Product Manager layer. Scores anonymized backlog items, routes innovation tracks, applies founder-controlled relaxation (de-risking + brand abstraction), and produces track-aware public Micro-PRDs. LLM calls receive **structural metadata only** — never raw startup content.

## Contents

| File | Role |
|---|---|
| `scorer.py` | Severity / Friction / Sensitivity scoring → Red/Yellow/Green tag |
| `track_router.py` | Heuristic track suggestion (technical vs product_feature) + brand_proxy |
| `relaxation.py` | Pure transforms: abstract logic, variable synthesis, noise, brand abstraction |
| `domain_obfuscator.py` | Industry domain masking: rule-based (food/fintech/ride) + LLM for novel domains |
| `llm_domain_obfuscator.py` | LLM proposes `field_map` + public narrative when rules don't match |
| `company_profile.py` | Blind-audition Company Tech Profile generator (sensitivity-aware) |
| `public_sanitize.py` | Student API boundary — strips brand, sanitizes evaluation_focus/Micro-PRD |
| `publish_draft.py` | Founder-editable `PublishDraft` build/apply before release |
| `microprd.py` | Product track LLM Micro-PRD; technical fallback when spec path unavailable |
| `microprd_enrich.py` | Legacy blueprint enrichment — superseded by `spec_to_microprd` on dynamic path |
| `llm_client.py` | `RoutingLLMClient`: local vLLM → OpenAI per tier; mockable in tests |
| `store.py` | In-memory backlog pre-seeded with demo items |
| `models.py` | `ChallengeTrack`, `BacklogItem`, `IntakeRequest`, `MicroPRD`, `challenge_spec`, etc. |

Founder ingest is implemented in `api/triage_routes.py`:

- `POST /triage/intake` — calls `privacy_proxy.sanitize` then `_create_backlog_item`
- `POST /triage/score` — metadata-only path (upload loading page step 2)

Dynamic starter generation: see [`../challenge_factory/DOCS.md`](../challenge_factory/DOCS.md).

## LLM routing

| Tier | Default chain | Use |
|---|---|---|
| `sensitive` | local vLLM only | Triage scoring, domain obfuscation, challenge spec, sponsor fit |
| `standard` | local vLLM → OpenAI | Non-sensitive future paths (e.g. Keep on Bay copy) |

Env:

- `LLM_BASE_URL` — OpenAI-compatible local server (vLLM)
- `OPENAI_API_KEY` — cloud fallback / standard tier
- `LLM_ALLOW_CLOUD_SENSITIVE=1` — allow OpenAI for sensitive when local is unavailable (off by default)

## How It Fits In

Consumes `SanitizedMetadata` from the privacy proxy. Exposed via `api/triage_routes.py`.

- **Ingest:** `/intake`, `/score`, or `/proxy/sanitize` + `/score`
- **Preview (technical, non-demo):** `/relax` → `generate_spec()` → `build_package(challenge_spec=…)` → `spec_to_microprd()` before persist; stores optional `BacklogItem.challenge_spec`
- **Preview (product / demo-*):** `/relax` → track-aware Micro-PRD only; `challenge_package` is null; legacy scaffolds at publish
- **Publish:** dynamic items require valid non-stale `challenge_package` from Preview; product/demo use hardcoded scaffolds

## Notes for the Next Session

- Heuristic scorer runs when no LLM backend is configured — demo works offline
- `demo-004` is the Product Feature seed (EatsHub merchant discovery) — **no dynamic factory package**
- `demo-006` resolves a runtime spec via `legacy_spec_adapter` but still uses legacy publish scaffolds
- Relaxation is deterministic: same `challenge_seed` + config → same synthesized field names
- When `obfuscate_domain` is enabled, `domain_obfuscator.build_field_map` remaps column names in the relaxed preview before publish
- Public student API never returns `brand_proxy` — only `CompanyTechProfile` via `public_sanitize.build_public_challenge`
- `store.py` is in-memory only — replace with DB for production
