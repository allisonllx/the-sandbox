# API Design Patterns

Required reading when adding or changing API endpoints in this repository.

The goal: **clients and operators should never have to guess what happened.** Machine-checkable structured fields carry operational state; human-readable strings supplement them — never replace them.

---

## 1. Response Envelope

Every endpoint returns a consistent top-level shape.

### Success

```json
{
  "ok": true,
  "data": { ... }
}
```

Some existing endpoints (e.g. `POST /api/v1/proxy/sanitize`) use a domain-specific key instead of `data` (`metadata`, `microprd`). That is acceptable for established routes. **New endpoints should prefer `data`.**

### Failure

HTTP status codes carry the category (4xx client, 5xx server). The body must still be structured:

```json
{
  "ok": false,
  "error": {
    "code": "ITEM_NOT_FOUND",
    "message": "Backlog item not found.",
    "detail": "No item with id 'demo-999'.",
    "hint": "Call GET /api/v1/triage/backlog to list valid IDs."
  }
}
```

| Field | Required | Purpose |
|---|---|---|
| `code` | Yes | Stable, machine-readable identifier (`SCREAMING_SNAKE_CASE`) |
| `message` | Yes | Short summary for humans |
| `detail` | No | Specific context (IDs, field names, counts) |
| `hint` | No | Actionable next step for the caller |

**Do not** return ambiguous plain strings like `"error": "Something went wrong"`.

FastAPI `HTTPException(detail=...)` should be migrated to this shape when endpoints are touched.

---

## 2. Operational State vs Narrative

Separate **what happened** (structured) from **why / context** (prose).

| Layer | Field type | Example |
|---|---|---|
| Operational state | Enum / boolean / count | `"status": "completed_empty"` |
| Human narrative | `processing_notes`, `message` | `"NER pass completed — no entities detected"` |

**Rule:** If a client might branch on the outcome, it must not parse prose. Add a structured field.

### Anti-pattern (do not do this)

```json
{
  "ner_entity_counts": [],
  "processing_notes": [
    "NER pass skipped or returned no entities (model may not be installed)."
  ]
}
```

An empty array + vague note forces the caller to guess between two unrelated outcomes.

### Pattern (do this)

```json
{
  "ner": {
    "status": "completed_empty",
    "model_available": true,
    "entity_counts": []
  },
  "processing_notes": [
    "NER pass completed — no PERSON, ORG, GPE, or PRODUCT entities detected in scrubbed text."
  ]
}
```

Clients check `ner.status`. Humans read `processing_notes`.

---

## 3. Status Enums

Use explicit status enums instead of inferring from empty collections.

| Bad | Good |
|---|---|
| `items: []` — empty list or error? | `"status": "completed_empty"` |
| `null` — missing or skipped? | `"status": "skipped"` with reason |
| boolean `success: true` only | `ok: true` + domain `status` field |

Naming convention: `{past_tense_verb}` or `{past_tense_verb}_{modifier}`

Examples used in this repo:

| Status | Meaning |
|---|---|
| `not_run` | Pipeline stage was not reached (e.g. empty input) |
| `skipped` | Stage was bypassed (dependency missing, config off) |
| `completed_empty` | Stage ran successfully, produced no output |
| `completed` | Stage ran successfully, produced output |
| `failed` | Stage attempted and errored |

---

## 4. Privacy Boundary

Endpoints that touch startup data must never return raw content.

| Allowed in responses | Never allowed |
|---|---|
| Field names, inferred types | Raw log lines, cell values |
| PII type + count | PII values (even masked fragments that reconstruct) |
| Event-type frequencies | User-identifying strings |
| Structural metadata | Unscrubbed input echoed back |

If an endpoint accepts raw text, the response contains **metadata only** — see `POST /api/v1/proxy/sanitize`.

---

## 5. Endpoint Checklist

Before merging a new or changed endpoint:

- [ ] Success response uses the envelope (`ok: true` + payload)
- [ ] Error response uses `{ ok: false, error: { code, message, ... } }`
- [ ] Operational outcomes have structured status fields (not inferred from emptiness)
- [ ] Human-readable notes are supplementary, not the only signal
- [ ] No raw corporate data crosses the response boundary
- [ ] OpenAPI description on the route explains what data the endpoint sends externally (if any)
- [ ] At least one test asserts the structured status field, not just HTTP 200

---

## 6. Reference: Sanitize Response

`POST /api/v1/proxy/sanitize` is the reference implementation.

```json
{
  "ok": true,
  "metadata": {
    "format_detected": "log",
    "fields": [ ... ],
    "pii_detections": [
      { "pii_type": "email", "count": 1 }
    ],
    "ner": {
      "status": "completed_empty",
      "model_available": true,
      "entity_counts": []
    },
    "ner_entity_counts": [],
    "blocked_chunk_count": 0,
    "processing_notes": [
      "3 PII token(s) masked across 3 type(s).",
      "NER pass completed — no PERSON, ORG, GPE, or PRODUCT entities detected in scrubbed text."
    ]
  },
  "error": null
}
```

`metadata.ner` is the canonical NER block. `metadata.ner_entity_counts` is kept for backward compatibility and mirrors `ner.entity_counts`.

### NER status values

| `ner.status` | `model_available` | Meaning |
|---|---|---|
| `not_run` | any | Input was empty or blocked before NER ran |
| `skipped` | `false` | spaCy model not installed |
| `completed_empty` | `true` | Model ran; no PERSON/ORG/GPE/PRODUCT found |
| `completed` | `true` | Model ran; entities detected |

---

## 7. Reference: Error Response (target shape)

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request body failed validation.",
    "detail": "Field 'content' must not be empty.",
    "hint": "Provide at least one non-empty line of log text."
  }
}
```

HTTP `422` for validation, `404` for missing resources, `500` only for unexpected server faults.

---

## 8. Reference: Publish Draft Flow

Founders edit student-facing copy before publish via `PublishDraft`:

- `POST /api/v1/triage/relax/{id}` returns `challenge_draft` in the response (preview baseline)
- Founder edits in `PublishDraftEditor`; publish sends optional `draft` in the same `RelaxRequest` body as `config`
- `POST /api/v1/triage/publish/{id}` applies draft overrides before Micro-PRD generation and public sanitization

Key fields: `title`, `context`, `definition_of_success`, `evaluation_focus`, `company_profile` (blind audition).

Public student responses never echo CTO-only fields (`brand_proxy`, `source_label`).

---

## 9. Reference: Rank Endpoints (demo stubs)

Three intentionally separate rank surfaces:

| Endpoint | Audience | Scope |
|---|---|---|
| `GET /api/v1/sandbox/leaderboard` | Students | Global platform rank |
| `GET /api/v1/triage/backlog/{id}/matches` | Startup sponsors | Single challenge only |
| `GET /api/v1/sandbox/enterprise/radar` | Enterprise recruiters | Platform-wide top tier |

Responses use anonymized display names (e.g. `Candidate A7F2`) — no sponsor or company names.

### Reference: Dual-Layer Scorecard

Submit responses include nested `platform` and `sponsor` layers:

```json
{
  "platform": { "dimensions": { "tests_passed": 95 }, "score": 91 },
  "sponsor": { "dimensions": { "criteria_alignment": 82 }, "score": 80 },
  "execution_points": 109,
  "sponsor_fit_score": 80,
  "dimensions": { "tests_passed": 95 }
}
```

- `execution_points` = `round(platform.score * 1.2)` — global rank only
- `sponsor_fit_score` = `sponsor.score` — Match Radar sort key
- Top-level `dimensions` aliases `platform.dimensions` for backward compatibility

---

## 10. Reference: Founder Ingest

Three equivalent ways to create a backlog item from raw founder input. **Raw text never persists** — only sanitized metadata is stored.

| Path | Steps | UI / script |
|---|---|---|
| One-call intake | `POST /triage/intake` | `/startup` sidebar, `factory_intake.sh` |
| Two-step upload | `POST /proxy/sanitize` → `POST /triage/score` | `/startup/upload/loading`, `factory_pipeline.sh` |

### `POST /api/v1/triage/intake`

Request:

```json
{
  "problem_statement": "Our payment retry queue drops tasks under load...",
  "source_label": "founder-brief"
}
```

Response (domain-specific keys — established route):

```json
{
  "item_id": "item-abc123",
  "metadata": { "title": "...", "schema": [], "..." : "..." },
  "sensitivity": { "overall": 0.42, "..." : "..." }
}
```

Operational rules:

- PII scrubbing runs locally in `privacy_proxy.sanitize()` before scoring
- Empty `problem_statement` → HTTP 422 with structured error
- Created item appears in `GET /api/v1/triage/backlog` like any scored item

See [`backend/ai_pm/DOCS.md`](../backend/ai_pm/DOCS.md) and [`scripts/DOCS.md`](../scripts/DOCS.md).
