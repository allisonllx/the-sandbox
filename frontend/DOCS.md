# Frontend

## Purpose

Next.js 14 student, startup, and enterprise UIs for The Sandbox. Proxies `/api/*` to the FastAPI backend on port 8000.

## Contents

| Path | Role |
|---|---|
| `app/startup/` | CTO dashboard — triage backlog, quick intake (`FounderIntakePanel`), link to upload |
| `app/startup/upload/` | Founder upload — task description or log file → sanitize → score |
| `app/startup/upload/loading/` | Processing UI (`/proxy/sanitize` then `/triage/score`) |
| `app/startup/matches/[challengeId]/` | Sponsor Match Radar (per-challenge performers) |
| `app/student/` | Innovation Hub challenge browser + track tabs |
| `app/student/challenges/[id]/` | Micro-PRD + workspace (technical or product track) |
| `app/student/leaderboard/` | Global Execution Points (student motivation) |
| `app/student/trust/` | Sponsor verification protocol narrative (stub) |
| `app/enterprise/radar/` | Platform-wide top-tier candidates (enterprise demo) |
| `components/ChallengeWorkspace.tsx` | Multi-file Monaco editor, autosave, run/submit |
| `components/ProductWorkspace.tsx` | Product track prototype editor + DESIGN.md |
| `components/PublishDraftEditor.tsx` | Founder-editable release preview before publish |
| `components/CompanyProfilePanel.tsx` | Blind-audition Company Tech Profile preview |
| `components/FounderIntakePanel.tsx` | Sidebar quick intake → `POST /triage/intake` |
| `components/` | Shared UI (BacklogCard, RelaxationPanel, ChallengeCard, MicroPRDView, ScorecardView) |
| `lib/api.ts` | Typed API client — `sanitize`, `scoreMetadata`, `intake`, draft, validate, run, submit |
| `lib/uploadSession.ts` | sessionStorage between `/startup/upload` and loading page |
| `lib/draftStorage.ts` | IndexedDB draft cache |
| `lib/types.ts` | TypeScript interfaces mirroring backend models |

## How It Fits In

`next.config.mjs` rewrites `/api/*` → `http://localhost:8000/api/*`.

- Startup founders ingest at `/startup/upload` or sidebar intake; publish at `/startup`
- Students work at `/student/challenges/[id]`; global rank at `/student/leaderboard`
- Enterprise demo at `/enterprise/radar`

## Notes for the Next Session

- Run `npm install` once (includes `@monaco-editor/react`), then `npm run dev`
- Workspace bootstrap: `GET /sandbox/challenges/{id}/workspace` sets cookie; drafts sync to server + IndexedDB
- RelaxationPanel: **Preview Changes** loads `challenge_draft`; **Approve & Publish** sends edited `draft` in publish body
- Assessor scorecard: dual-layer Platform Signal + Sponsor Fit in ScorecardView
- After code changes, check `docs/documentation-sync.md`
