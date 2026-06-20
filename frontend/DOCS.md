# Frontend

## Purpose

Next.js 14 student and startup UIs for The Sandbox. Proxies `/api/*` to the FastAPI backend on port 8000.

## Contents

| Path | Role |
|---|---|
| `app/startup/` | CTO dashboard — triage backlog + relaxation controls |
| `app/student/` | Challenge browser |
| `app/student/challenges/[id]/` | Micro-PRD + Monaco workspace + submit |
| `components/ChallengeWorkspace.tsx` | Multi-file Monaco editor, autosave, run/submit |
| `components/` | Shared UI (BacklogCard, RelaxationPanel, ChallengeCard, MicroPRDView) |
| `lib/api.ts` | Typed API client (draft, validate, run, submit) |
| `lib/draftStorage.ts` | IndexedDB draft cache |
| `lib/types.ts` | TypeScript interfaces mirroring backend models |

## How It Fits In

`next.config.mjs` rewrites `/api/*` → `http://localhost:8000/api/*`. Startup founders publish at `/startup`; students work at `/student/challenges/[id]`.

## Notes for the Next Session

- Run `npm install` once (includes `@monaco-editor/react`), then `npm run dev`
- Workspace bootstrap: `GET /sandbox/challenges/{id}/workspace` sets cookie; drafts sync to server + IndexedDB
- Assessor scorecard UI will land in assessor-001
- After code changes, check `docs/documentation-sync.md`
