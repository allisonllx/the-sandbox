# Privacy Proxy

## Purpose

Client-side sanitization engine. Accepts raw startup logs, CSV, or JSON and returns **structural metadata only** — no PII, no raw content. This is the zero-trust boundary of the platform.

## Contents

| File | Role |
|---|---|
| `sanitizer.py` | Main pipeline: guardrail → PII scrub → NER → structural extract |
| `pii_patterns.py` | Regex patterns for email, phone, JWT, API keys, IPs, etc. |
| `ner_engine.py` | Offline spaCy NER wrapper (`en_core_web_sm`) |
| `structural_extractor.py` | Parses scrubbed text into field names, types, row scale |
| `models.py` | Pydantic models: `SanitizedMetadata`, `NERSummary`, request/response shapes |

## How It Fits In

Called by `POST /api/v1/proxy/sanitize` (`api/routes.py`). Its output (`SanitizedMetadata`) is the locked input contract for `ai_pm/scorer.py` and the triage dashboard.

## Notes for the Next Session

- **Must never make network calls** — enforced by tests
- NER degrades gracefully if spaCy model is missing; check `metadata.ner.status` not prose notes
- `ner.status` values: `not_run`, `skipped`, `completed_empty`, `completed`
- PII scrubbing runs **before** NER — names embedded in emails won't be detected as PERSON entities
