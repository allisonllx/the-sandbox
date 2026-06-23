# Frontend

## Purpose

Next.js 14 student, startup, and enterprise UIs for The Sandbox. Proxies `/api/*` to the FastAPI backend on port 8000.

## Contents

| Path | Role |
|---|---|
| `app/startup/` | CTO dashboard — triage backlog (collapsible In triage / Live / Closed sections), quick intake, publish & close submissions |
| `app/startup/upload/` | Founder upload — task description or log file → sanitize → score |
| `app/startup/upload/loading/` | Processing UI (`/proxy/sanitize` then `/triage/score`) |
| `app/startup/matches/[challengeId]/` | Sponsor Match Radar (per-challenge performers) |
| `app/student/` | Innovation Hub challenge browser + track tabs |
| `app/student/challenges/[id]/` | Micro-PRD left panel + workspace (technical or product track) |
| `app/student/leaderboard/` | Global Execution Points (student motivation) |
| `app/student/trust/` | Sponsor verification protocol narrative (stub) |
| `app/enterprise/radar/` | Platform-wide top-tier candidates (enterprise demo) |
| `components/ChallengeWorkspace.tsx` | Monaco editor, autosave, run/submit, draggable terminal, **Add file** (`src/helpers/*.py`) |
| `lib/workspaceFiles.ts` | Helper path validation + workspace limit copy |
| `components/ProductWorkspace.tsx` | Product track prototype editor + DESIGN.md |
| `components/PublishDraftEditor.tsx` | Founder-editable release preview (raw markdown textarea) |
| `components/MicroPRDView.tsx` | Student brief sections — delegates to `BriefSectionBody` |
| `components/BriefMarkdown.tsx` | Subset markdown renderer (**bold**, `` `code` ``, nested lists); inherits JetBrains Mono |
| `components/BriefSectionBody.tsx` | Prose vs bullet sections; `BriefAsideSection` for anomalies / evaluation focus |
| `components/CompanyProfilePanel.tsx` | Blind-audition Company Tech Profile preview |
| `components/FounderIntakePanel.tsx` | Sidebar quick intake → `POST /triage/intake` |
| `components/BacklogSidebar.tsx` | CTO sidebar — collapsible **In triage** / **Live challenges** / **Closed** sections |
| `components/BacklogCard.tsx` | Backlog list card (full in triage; compact in live/closed) |
| `components/RelaxationPanel.tsx` | Preview, publish, **Close submissions**; read-only summary when closed |
| `components/ScorecardView.tsx` | Dual-layer platform + sponsor scorecard |
| `lib/api.ts` | Typed API client — `sanitize`, `scoreMetadata`, `intake`, `publish`, `closeChallenge`, draft, validate, run, submit |
| `lib/uploadSession.ts` | sessionStorage between `/startup/upload` and loading page |
| `lib/draftStorage.ts` | IndexedDB draft cache |
| `lib/types.ts` | TypeScript interfaces mirroring backend models |

## Student brief rendering

The workspace left panel (`/student/challenges/[id]`) shows the public Micro-PRD:

| Section | Component | Markdown |
|---|---|---|
| Context, User Persona, Problem Framing | `BriefMarkdown` | Full block (headings, examples lists) |
| Definition of Success, Constraints, Sandbox Instructions | `BriefSectionBody` list mode | Inline `` `code` `` / **bold** per bullet |
| Injected Anomalies, Evaluation Focus | `BriefAsideSection` + `BriefSectionBody` | Same inline rendering |

**Founder vs student:** `PublishDraftEditor` keeps raw markdown for editing; students see rendered output only. No extra npm dependency — custom parser in `BriefMarkdown.tsx` matches the backend brief subset.

Backend brief source: `spec_to_microprd()` → `format_spec_context()` + `format_spec_examples()` (see `backend/challenge_factory/spec_projection.py`).

## How It Fits In

`next.config.mjs` rewrites `/api/*` → `http://localhost:8000/api/*`.

- Startup founders ingest at `/startup/upload` or sidebar intake; publish at `/startup`
- CTO sidebar partitions backlog: triage items stay in **In triage**; after publish items move to **Live challenges**; **Close submissions** archives to **Closed** (hidden from student hub, Match Radar still available)
- Students work at `/student/challenges/[id]`; global rank at `/student/leaderboard`
- Enterprise demo at `/enterprise/radar`

## Notes for the Next Session

- Run `npm install` once (includes `@monaco-editor/react`), then `npm run dev`
- Workspace bootstrap: `GET /sandbox/challenges/{id}/workspace` sets cookie; drafts sync to server + IndexedDB
- RelaxationPanel: **Preview Changes** loads `challenge_draft`; **Approve & Publish** sends edited `draft` in publish body; published items show **Close submissions** → `POST /triage/close/{id}`
- Assessor scorecard: dual-layer Platform Signal + Sponsor Fit in ScorecardView
- After code changes, check `docs/documentation-sync.md`
