# Tests

## Purpose

pytest suite verifying the privacy proxy and AI PM triage layer. All tests run without network access or a live OpenAI key.

## Contents

| File | Covers |
|---|---|
| `test_sanitizer.py` | PII masking, NER status fields, structural extraction, zero-network guard |
| `test_triage.py` | Scoring, sensitivity tags, relaxation controls, demo store |
| `fixtures/sample_log.txt` | Realistic log lines with synthetic PII for integration tests |

## How It Fits In

Run from the **repo root** so the `backend` package resolves correctly:

```bash
python -m pytest backend/tests/ -v
```

## Notes for the Next Session

- LLM calls are stubbed via `MagicMock` — never hit OpenAI in CI
- `TestNoNetworkCalls` monkeypatches `socket.connect` to prove the privacy proxy stays offline
- When adding endpoints, assert structured status fields (see `docs/api-patterns.md`), not just HTTP 200
- New features should add tests here before marking `feature_list.json` as passing
