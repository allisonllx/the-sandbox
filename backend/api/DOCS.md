# API Routes

## Purpose

HTTP layer for the backend. Thin route handlers that delegate to domain modules — no business logic here.

## Contents

| File | Prefix | Endpoints |
|---|---|---|
| `routes.py` | `/api/v1/proxy` | `POST /sanitize`, `GET /health` |
| `triage_routes.py` | `/api/v1/triage` | Backlog, scope, matches, score, relax, publish |
| `sandbox_routes.py` | `/api/v1/sandbox` | Challenges, starter, workspace/draft, validate, run jobs, submit, scorecard, leaderboard, enterprise radar |

Routers are mounted in `main.py`. OpenAPI docs at `/docs`.

### Triage (`triage_routes.py`)

| Method | Path | Notes |
|---|---|---|
| `GET` | `/backlog` | All backlog items (CTO-only fields incl. `brand_proxy`) |
| `GET` | `/backlog/{id}` | Single backlog item |
| `GET` | `/backlog/{id}/scope` | Scope estimate + union-rep breakdown |
| `GET` | `/backlog/{id}/matches` | **Sponsor Match Radar** — performers for this challenge only |
| `POST` | `/score` | Score a `SanitizedMetadata` blob |
| `POST` | `/relax/{id}` | Relaxation preview; returns `challenge_draft` (`PublishDraft`) |
| `POST` | `/publish/{id}` | Publish challenge; accepts optional `draft` in body; requires locked reward + scope pass |

### Sandbox (`sandbox_routes.py`)

| Method | Path | Notes |
|---|---|---|
| `GET` | `/challenges` | Public challenges (`?track=` filter); blind-audition sanitized |
| `GET` | `/challenges/{id}` | Single challenge + Micro-PRD |
| `GET` | `/challenges/{id}/starter` | Multi-file starter scaffold (JSON) |
| `GET` | `/challenges/{id}/starter/download` | Starter as ZIP |
| `GET` | `/challenges/{id}/workspace` | Bootstrap workspace session + load draft |
| `PUT` | `/challenges/{id}/draft` | Save workspace draft |
| `DELETE` | `/challenges/{id}/draft` | Clear draft after submit |
| `POST` | `/validate` | Python syntax diagnostics |
| `GET` | `/challenges/{id}/dataset` | Synthetic SQLite (technical track) |
| `POST` | `/challenges/{id}/run` | Enqueue public test run |
| `GET` | `/jobs/{id}` | Poll run job |
| `POST` | `/challenges/{id}/submit` | Inline multi-file submit |
| `POST` | `/challenges/{id}/submit/zip` | ZIP submit (raw body) |
| `GET` | `/submissions/{id}/scorecard` | Assessor scorecard |
| `GET` | `/challenges/{id}/submissions/count` | Debug/demo count |
| `GET` | `/leaderboard` | **Student global** Execution Points (demo) |
| `GET` | `/enterprise/radar` | **Enterprise platform-wide** top tier (demo) |

Public challenge responses use `public_sanitize.build_public_challenge()` — no `brand_proxy`.

## How It Fits In

Translates HTTP requests into calls to `privacy_proxy/`, `ai_pm/`, and `sandbox/`. The frontend (`frontend/lib/api.ts`) proxies `/api/*` to this server during local dev.

## Notes for the Next Session

- Follow `docs/api-patterns.md` for response shapes on new endpoints
- Errors should use structured `{ code, message, detail, hint }` — existing routes still use FastAPI defaults; migrate when touched
- CORS allows `http://localhost:3000` only — update for production deployment
- `POST /relax/{id}` and `POST /publish/{id}` share `RelaxRequest` body (`config`, optional `track`, optional `draft`)
