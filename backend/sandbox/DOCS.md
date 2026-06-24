# Sandbox

## Purpose

Public challenge layer for students (Innovation Hub). Serves track-aware published challenges, workspace drafts, public test runs (technical track), disk-backed submissions with optional external links (product track), and demo rank stubs.

## Contents

| File | Role |
|---|---|
| `models.py` | Public API models incl. track fields, `SubmitRequest.links`, scorecard response |
| `synthesizer.py` | Procedural SQLite generator with injected anomalies (technical track) |
| `starter_scaffold.py` | Python starter + `browser_workspace_readme_section()`, `platform_sandbox_instructions()` |
| `product_starter_scaffold.py` | HTML/CSS/JS + DESIGN.md + mock JSON (product track) |
| `workspace.py` | Anonymous `sandbox_workspace_id` cookie helpers |
| `draft_store.py` | File-backed drafts under `data/drafts/` |
| `validate.py` | `ast.parse` / `py_compile` diagnostics for Monaco |
| `archive.py` | Safe ZIP pack/unpack (path traversal guard, size caps) |
| `run_jobs.py` | In-process async public test runs under `data/jobs/` |
| `submission_store.py` | Disk snapshots under `data/submissions/` (files + links + scorecard) |
| `leaderboard.py` | Demo global student rank seed (`Candidate A7F2`, etc.) |
| `sponsor_matches.py` | Per-challenge match radar for startup sponsors |
| `enterprise_radar.py` | Platform-wide top-tier demo for enterprise subscription view |

## How It Fits In

Publishing from `POST /api/v1/triage/publish/{id}` branches by track:

- **Technical (dynamic factory):** `BacklogItem.starter_files` from `challenge_factory` — includes `docs/SPEC.md`, interpolated `src/*` stubs, `tests/test_public.py`
- **Technical (legacy demo-*):** `starter_scaffold.py` + synthesizer SQLite
- **Product track:** `product_starter_scaffold.py` (HTML/CSS/JS + DESIGN.md)

Routes in `api/sandbox_routes.py` expose list/filter by track, starter, workspace, submit (with assessor), scorecard, and three rank surfaces:

| Module | API | Frontend |
|---|---|---|
| `leaderboard.py` | `GET /sandbox/leaderboard` | `/student/leaderboard` |
| `sponsor_matches.py` | `GET /triage/backlog/{id}/matches` | `/startup/matches/[challengeId]` |
| `submission_store.py` | `GET /triage/backlog/{id}/submissions/{submission_id}` | `/startup/matches/.../submissions/[submissionId]` |
| `enterprise_radar.py` | `GET /sandbox/enterprise/radar` | `/enterprise/radar` |

Frontend: `/student` track tabs; `/student/challenges/[id]` routes to `ChallengeWorkspace` or `ProductWorkspace`.

**Browser workspace (technical):** students may **Add file** under `src/helpers/*.py` only. **Run Public Tests** runs pytest — no shell, no `main.py`, no website preview. Copy also appears in starter `README.md` and Micro-PRD sandbox instructions.

## Notes for the Next Session

- Product track: no dataset download; submit requires DESIGN.md for strong assessor scores
- Dynamic factory starters include `docs/SPEC.md` — students should read it before editing `src/*`
- `GET /sandbox/challenges?track=product_feature` filters published challenges only (`BacklogStatus.published` — closed items return 404 on all sandbox routes)
- Sponsor matches scope to **one challenge** — startups never see cross-company performers
- After code changes, check `docs/documentation-sync.md`
