# Frontend

## Purpose

Next.js 14 student and startup UIs for The Sandbox. Proxies `/api/*` to the FastAPI backend on port 8000.

## Contents

| Path | Role |
|---|---|
| `app/startup/` | CTO dashboard — triage backlog + relaxation controls |
| `app/student/` | Challenge browser |
| `app/student/challenges/[id]/` | Micro-PRD + sandbox terminal + submit |
| `components/` | Shared UI (BacklogCard, RelaxationPanel, ChallengeCard, MicroPRDView, SandboxTerminal) |
| `lib/api.ts` | Typed API client |
| `lib/types.ts` | TypeScript interfaces mirroring backend models |

## How It Fits In

`next.config.mjs` rewrites `/api/*` → `http://localhost:8000/api/*`. Startup founders publish at `/startup`; students work at `/student`.

## Notes for the Next Session

- Run `npm install` once, then `npm run dev`
- Assessor scorecard UI will live under `/student/challenges/[id]` or a new route in assessor-001
- After code changes, check `docs/documentation-sync.md` and `docs/PRODUCT.md` for flow updates
