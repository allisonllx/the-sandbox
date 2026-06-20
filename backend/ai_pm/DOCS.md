# AI PM

## Purpose

AI Product Manager layer. Scores anonymized backlog items, routes innovation tracks, applies founder-controlled relaxation (de-risking + brand abstraction), and generates track-aware public Micro-PRDs. LLM calls receive **structural metadata only** — never raw startup content.

## Contents

| File | Role |
|---|---|
| `scorer.py` | Severity / Friction / Sensitivity scoring → Red/Yellow/Green tag |
| `track_router.py` | Heuristic track suggestion (technical vs product_feature) + brand_proxy |
| `relaxation.py` | Pure transforms: abstract logic, variable synthesis, noise, brand abstraction |
| `microprd.py` | Track-aware LLM Micro-PRD generator (template fallback if no API key) |
| `llm_client.py` | Injectable OpenAI wrapper — mockable in tests |
| `store.py` | In-memory backlog pre-seeded with 4 demo items (incl. demo-004 product) |
| `models.py` | `ChallengeTrack`, `BacklogItem`, `MicroPRD` product sections, etc. |

## How It Fits In

Consumes `SanitizedMetadata` from the privacy proxy. Exposed via `api/triage_routes.py`. Publish branches by track: technical generates SQLite + Python starter; product_feature generates frontend starter + DESIGN.md.

## Notes for the Next Session

- Heuristic scorer runs when `OPENAI_API_KEY` is absent — demo works offline
- `demo-004` is the Product Feature seed (EatsHub merchant discovery)
- Relaxation is deterministic: same `challenge_seed` + config → same synthesized field names
- `store.py` is in-memory only — replace with DB for production
