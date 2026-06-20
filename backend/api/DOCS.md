# API Routes

## Purpose

HTTP layer for the backend. Thin route handlers that delegate to domain modules — no business logic here.

## Contents

| File | Prefix | Endpoints |
|---|---|---|
| `routes.py` | `/api/v1/proxy` | `POST /sanitize`, `GET /health` |
| `triage_routes.py` | `/api/v1/triage` | `GET /backlog`, `POST /score`, `POST /relax/{id}`, `POST /publish/{id}` |

Routers are mounted in `main.py`. OpenAPI docs at `/docs`.

## How It Fits In

Translates HTTP requests into calls to `privacy_proxy/` and `ai_pm/`. The frontend (`frontend/lib/api.ts`) proxies `/api/*` to this server during local dev.

## Notes for the Next Session

- Follow `docs/api-patterns.md` for response shapes on new endpoints
- Errors should use structured `{ code, message, detail, hint }` — existing routes still use FastAPI defaults; migrate when touched
- CORS allows `http://localhost:3000` only — update for production deployment
