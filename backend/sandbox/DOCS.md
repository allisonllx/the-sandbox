# Sandbox

## Purpose

Public challenge layer for students (Innovation Hub). Serves track-aware published challenges, workspace drafts, public test runs (technical track), and disk-backed submissions with optional external links (product track).

## Contents

| File | Role |
|---|---|
| `models.py` | Public API models incl. track fields, `SubmitRequest.links`, scorecard response |
| `synthesizer.py` | Procedural SQLite generator with injected anomalies (technical track) |
| `starter_scaffold.py` | 5-file Python starter (technical track) |
| `product_starter_scaffold.py` | HTML/CSS/JS + DESIGN.md + mock JSON (product track) |
| `workspace.py` | Anonymous `sandbox_workspace_id` cookie helpers |
| `draft_store.py` | File-backed drafts under `data/drafts/` |
| `validate.py` | `ast.parse` / `py_compile` diagnostics for Monaco |
| `archive.py` | Safe ZIP pack/unpack (path traversal guard, size caps) |
| `run_jobs.py` | In-process async public test runs under `data/jobs/` |
| `submission_store.py` | Disk snapshots under `data/submissions/` (files + links + scorecard) |

## How It Fits In

Publishing from `POST /api/v1/triage/publish/{id}` branches by track. Routes in `api/sandbox_routes.py` expose list/filter by track, starter, workspace, submit (with assessor), and scorecard GET. Frontend: `/student` track tabs; `/student/challenges/[id]` routes to `ChallengeWorkspace` or `ProductWorkspace`.

## Notes for the Next Session

- Product track: no dataset download; submit requires DESIGN.md for strong assessor scores
- `GET /sandbox/challenges?track=product_feature` filters published challenges
- After code changes, check `docs/documentation-sync.md`
