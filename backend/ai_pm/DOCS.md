# AI PM

## Purpose

AI Product Manager layer. Scores anonymized backlog items, applies founder-controlled relaxation (de-risking), and generates public Micro-PRDs. LLM calls receive **structural metadata only** — never raw startup content.

## Contents

| File | Role |
|---|---|
| `scorer.py` | Severity / Friction / Sensitivity scoring → Red/Yellow/Green tag |
| `relaxation.py` | Pure transforms: abstract logic, variable synthesis, noise injection |
| `microprd.py` | LLM Micro-PRD generator (template fallback if no API key) |
| `llm_client.py` | Injectable OpenAI wrapper — mockable in tests |
| `store.py` | In-memory backlog pre-seeded with 3 demo items |
| `models.py` | `BacklogItem`, `TechScores`, `RelaxationConfig`, `MicroPRD`, etc. |

## How It Fits In

Consumes `SanitizedMetadata` from the privacy proxy. Exposed via `api/triage_routes.py`. The relaxation preview (`POST /relax/{id}`) is pure — no LLM. LLM is only called for scoring and publish (`POST /publish/{id}`).

## Notes for the Next Session

- Heuristic scorer runs when `OPENAI_API_KEY` is absent — demo works offline
- Relaxation is deterministic: same `challenge_seed` + config → same synthesized field names
- `store.py` is in-memory only — replace with DB for production
- Variable synthesis uses Greek-letter tokens (`node_alpha`, `stream_beta`) — see `relaxation.py`
