# Tests

## Purpose

pytest suite verifying the privacy proxy, AI PM triage layer, challenge factory, and public sandbox. All tests run without network access or a live OpenAI key.

## Contents

| File | Covers |
|---|---|
| `test_sanitizer.py` | PII masking, NER status fields, structural extraction, zero-network guard |
| `test_triage.py` | Scoring, sensitivity tags, relaxation controls, demo store |
| `test_sandbox.py` | Publish flow, close submissions, starter scaffold, workspace/draft, validate, submit, ZIP guard |
| `test_sponsor_submission_review.py` | Match Radar submission_id + CTO submission detail endpoint |
| `test_challenge_factory.py` | Dynamic Preview/Publish, archetype override, package staleness |
| `test_challenge_spec.py` | Heuristic archetype inference + spec shape |
| `test_spec_projection.py` | Spec → Micro-PRD brief formatting, typed examples, non-generic student copy |
| `test_scaffold_interpolate.py` | Dynamic stubs/tests + per-archetype validation smokes |
| `test_legacy_spec_adapter.py` | Runtime spec for `demo-*` without store mutation |
| `test_microprd_enrich.py` | Legacy blueprint enrichment (demo/legacy paths) |
| `test_workspace_sufficiency.py` | Browser workspace gates (DATA.md, SPEC.md) |
| `test_draft_store.py` | Draft persistence and size limits |
| `test_run_jobs.py` | Async run job lifecycle and concurrency |
| `fixtures/sample_log.txt` | Realistic log lines with synthetic PII for integration tests |

## How It Fits In

Run from the **repo root** so the `backend` package resolves correctly:

```bash
python -m pytest backend/tests/ -v
```

Per-archetype factory smokes (requires running backend):

```bash
PREVIEW_ONLY=1 ./scripts/samples/run_all_previews.sh
```

## Notes for the Next Session

- LLM calls are stubbed via `MagicMock` — heuristic spec path is hot path in tests
- `TestNoNetworkCalls` monkeypatches `socket.connect` to prove the privacy proxy stays offline
- When adding endpoints, assert structured status fields (see `docs/api-patterns.md`), not just HTTP 200
- New archetypes: extend `test_scaffold_interpolate.py` parametrize list + `scripts/samples/logs/`
