# AI PM

## Purpose

AI Product Manager layer. Scores anonymized backlog items, routes innovation tracks, applies founder-controlled relaxation (de-risking + brand abstraction), and generates track-aware public Micro-PRDs. LLM calls receive **structural metadata only** — never raw startup content.

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
| `microprd.py` | Track-aware LLM Micro-PRD generator (template fallback if no LLM) |
| `llm_client.py` | `RoutingLLMClient`: local vLLM → OpenAI per tier; mockable in tests |
| `store.py` | In-memory backlog pre-seeded with demo items |
| `models.py` | `ChallengeTrack`, `BacklogItem`, `IntakeRequest`, `MicroPRD`, etc. |

Founder ingest is implemented in `api/triage_routes.py`:

- `POST /triage/intake` — calls `privacy_proxy.sanitize` then `_create_backlog_item`
- `POST /triage/score` — metadata-only path (upload loading page step 2)

Dynamic starter generation: see [`../challenge_factory/DOCS.md`](../challenge_factory/DOCS.md).

## LLM routing

| Tier | Default chain | Use |
|---|---|---|
| `sensitive` | local vLLM only | Triage scoring, domain obfuscation, Micro-PRD, sponsor fit |
| `standard` | local vLLM → OpenAI | Non-sensitive future paths (e.g. Keep on Bay copy) |

Env:

- `LLM_BASE_URL` — OpenAI-compatible local server (vLLM)
- `OPENAI_API_KEY` — cloud fallback / standard tier
- `LLM_ALLOW_CLOUD_SENSITIVE=1` — allow OpenAI for sensitive when local is unavailable (off by default)

## How It Fits In

Consumes `SanitizedMetadata` from the privacy proxy. Exposed via `api/triage_routes.py`.

- **Ingest:** `/intake`, `/score`, or `/proxy/sanitize` + `/score`
- **Preview:** `/relax` runs Micro-PRD + `challenge_factory.build_package()` for non-demo technical items
- **Publish:** legacy `demo-*` / product track use hardcoded scaffolds; dynamic items require valid `challenge_package` from Preview

## Notes for the Next Session

- Heuristic scorer runs when no LLM backend is configured — demo works offline
- `demo-004` is the Product Feature seed (EatsHub merchant discovery)
- Relaxation is deterministic: same `challenge_seed` + config → same synthesized field names
- When `obfuscate_domain` is enabled, `domain_obfuscator.build_field_map` remaps column names (e.g. `restaurant_id` → `locker_id`) in the relaxed preview before publish
- Yellow/Red sensitivity on **generic** domains triggers `llm_domain_obfuscator` when `LLM_DOMAIN_OBFUSCATE=1`
- Public student API never returns `brand_proxy` — only `CompanyTechProfile` via `public_sanitize.build_public_challenge`
- `store.py` is in-memory only — replace with DB for production
