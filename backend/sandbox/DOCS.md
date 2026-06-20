# Sandbox

## Purpose

Public challenge layer for students. Serves published challenges (Micro-PRD + synthetic SQLite datasets) and accepts code submissions queued for the AI Assessor.

## Contents

| File | Role |
|---|---|
| `models.py` | `PublishedChallenge`, `SubmitRequest`, `SubmitResponse`, `SubmissionRecord` |
| `synthesizer.py` | Procedural SQLite generator with injected anomalies |
| `submission_store.py` | In-memory submission queue (assessor-001 consumer) |

## How It Fits In

Publishing from `POST /api/v1/triage/publish/{id}` generates a dataset via `synthesizer.py` and sets backlog status to `published`. Routes in `api/sandbox_routes.py` expose the public student API. Frontend: `/student` and `/student/challenges/[id]`.

## Notes for the Next Session

- Datasets written to `backend/generated_datasets/{challenge_id}.sqlite` (gitignored)
- Injected anomalies: NULL `query_hash`, missing index on `execution_time_ms`, unindexed `sessions.event_id` join
- Submissions stored in memory only — assessor-001 should read from `submission_store`
- After code changes, check `docs/documentation-sync.md`
