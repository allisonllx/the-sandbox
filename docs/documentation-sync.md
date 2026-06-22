# Documentation Sync

When you change code, update related documentation **in the same session**. Do not leave docs stale for the next agent to discover.

Use this file as a lookup: find the code path you touched, check every doc in the row.

---

## How to use this

1. Identify which folder(s) you edited.
2. Check the **module `DOCS.md`** in that folder first.
3. If the change affects behavior, contracts, architecture, or user flows, check the **top-level `docs/`** files listed.
4. If nothing needed updating, record `"Docs: no update required — <reason>"` in `claude-progress.md`.

---

## Code path → documentation map

| Code path | Module doc (check first) | Also check `docs/` when… |
|---|---|---|
| `backend/privacy_proxy/` | `backend/privacy_proxy/DOCS.md` | **ARCHITECTURE.md** — data-flow or trust-boundary changes; **api-patterns.md** — `SanitizedMetadata` / `NERSummary` response shape changes |
| `backend/ai_pm/` | `backend/ai_pm/DOCS.md` | **ARCHITECTURE.md** — triage or relaxation pipeline changes; **PRODUCT.md** — founder/student flow changes; **api-patterns.md** — new triage endpoints or response fields |
| `backend/assessor/` | `backend/assessor/DOCS.md` | **ARCHITECTURE.md** — scorecard pipeline; **PRODUCT.md** — EP vs sponsor fit; **api-patterns.md** — scorecard shape |
| `backend/sandbox/` | `backend/sandbox/DOCS.md` | **ARCHITECTURE.md** — student flow; **PRODUCT.md** — student UX; **api-patterns.md** — sandbox endpoints |
| `backend/challenge_factory/` | `backend/challenge_factory/DOCS.md` | **ARCHITECTURE.md** — Preview→Publish factory pipeline; **api-patterns.md** — relax/regenerate response fields |
| `scripts/` | `scripts/DOCS.md`, `scripts/samples/DOCS.md` | **README.md** (root) — factory script quickstart in main onboarding |
| `samples/demo_solutions/` | `samples/demo_solutions/DOCS.md` | **README.md** (root) — sample publish/submit quickstart |
| `backend/api/` | `backend/api/DOCS.md` | **api-patterns.md** — any new/changed endpoint (required); **README.md** — API reference table; **ARCHITECTURE.md** — new external integration |
| `backend/prompts/` | `backend/prompts/DOCS.md` | When prompt contracts change (e.g. new `challenge_spec` fields) |
| `backend/tests/` | `backend/tests/DOCS.md` | Usually no `docs/` update unless verification rules or API contracts changed |
| `backend/main.py`, `backend/requirements.txt` | `backend/DOCS.md` | **README.md** — startup commands, dependencies, or project structure |
| `frontend/app/`, `frontend/components/`, `frontend/lib/` | `frontend/DOCS.md` | **PRODUCT.md** — user-facing flow or UX intent; **ARCHITECTURE.md** — new pages or client-server boundaries |
| `init.sh` | `backend/DOCS.md` | **README.md** — Quickstart / verification commands |
| `feature_list.json` | — | **PRODUCT.md** — if scope or roadmap materially changed |

---

## Top-level docs — when to update

| File | Update when… |
|---|---|
| `docs/ARCHITECTURE.md` | Directory structure, data flows, tech stack, external dependencies, or security boundaries change |
| `docs/PRODUCT.md` | User personas, core flows, out-of-scope items, or roadmap gaps change |
| `docs/api-patterns.md` | Response envelopes, error shapes, status enums, or endpoint conventions change |
| `docs/documentation-sync.md` | New backend module or doc folder added — add a row to the map above |
| `README.md` | Quickstart, prerequisites, project structure tree, or API reference table changes |
| `AGENTS.md` | Agent workflow, constraints, or topic-doc list changes |

---

## Module `DOCS.md` — when to update

Each code folder uses **`DOCS.md`** for module-local agent docs (not `README.md`). The repo root keeps **`README.md`** for human onboarding, quickstart, and the API reference table.

**Exception:** student challenge starters and sample submissions still use `README.md` inside published file trees — that name is part of the challenge contract, not repo documentation.

Update a folder's `DOCS.md` when:

- Files are added, removed, or renamed
- Module purpose or invariants change
- Key exports, endpoints, or dependencies change
- Gotchas for the next session change

Current module docs:

```
README.md                    # root onboarding only
backend/DOCS.md
backend/privacy_proxy/DOCS.md
backend/ai_pm/DOCS.md
backend/assessor/DOCS.md
backend/api/DOCS.md
backend/challenge_factory/DOCS.md
backend/prompts/DOCS.md
backend/sandbox/DOCS.md
backend/tests/DOCS.md
frontend/DOCS.md
scripts/DOCS.md
scripts/samples/DOCS.md
samples/demo_solutions/DOCS.md
```

---

## Examples

| You changed… | Update |
|---|---|
| Added `POST /api/v1/triage/foo` | `backend/api/DOCS.md`, `docs/api-patterns.md`, `README.md` API table |
| New PII pattern in `pii_patterns.py` | `backend/privacy_proxy/DOCS.md` only |
| New `ner.status` enum value | `backend/privacy_proxy/DOCS.md`, `docs/api-patterns.md`, `frontend/lib/types.ts` |
| Renamed relaxation toggle behavior | `backend/ai_pm/DOCS.md`, `docs/PRODUCT.md` (if user-visible) |
| Refactored tests only, same behavior | `claude-progress.md`: "Docs: no update required" |
| New archetype, scaffold, or spec field | `backend/challenge_factory/DOCS.md`, `backend/prompts/DOCS.md`, `scripts/samples/`, **AGENTS.md**; extend `test_scaffold_interpolate.py` + sample log/brief |
| New archetype sample script | `scripts/samples/DOCS.md`, `scripts/DOCS.md`, **README.md** quickstart |
| Student brief markdown / examples / frontend render | `backend/challenge_factory/DOCS.md`, `frontend/DOCS.md`, **docs/PRODUCT.md**, **docs/ARCHITECTURE.md**, **docs/api-patterns.md** |

---

## Cross-cutting invariants

Some bugs span multiple modules — the doc map alone is not enough.

### Challenge brief ↔ starter files

If you touch `challenge_factory/`, `spec_projection.py`, `scaffold_interpolate.py`,
student-facing sandbox routes, or `frontend/components/BriefMarkdown.tsx` / `MicroPRDView.tsx`,
verify **spec ↔ SPEC.md ↔ tests ↔ Micro-PRD ↔ rendered student brief** agree on edit
targets, public API symbols, and typed examples. Do not leave legacy `src/queries.py`
copy in dynamic/factory paths.

**Smoke check (technical):** `./scripts/samples/run_archetype.sh idempotency_engine` →
publish → `GET /api/v1/sandbox/challenges/{id}` — `structural_constraints` must
reference the same `src/*` files as `starter.files`.

**Product track:** expect `challenge_package: null` at Preview — HTML starter at publish.

**Regression tests:** `test_challenge_factory.py`, `test_scaffold_interpolate.py`

### Browser workspace sufficiency

Generated packages must be workable in the in-browser editor without opaque local
downloads. Spec-driven packages need `docs/SPEC.md`; sqlite archetypes also need
`docs/DATA.md`. **Run Public Tests** mounts the dataset server-side.
See `workspace_sufficiency.py` and `AGENTS.md`.

---

## Definition of done (documentation)

Documentation is in sync when:

- [ ] Module `DOCS.md` checked for every edited code folder
- [ ] Relevant `docs/` files updated if behavior, contracts, or architecture changed
- [ ] `README.md` updated if startup path or API reference changed
- [ ] Challenge brief ↔ starter edit targets checked if factory / Micro-PRD / scaffold code changed (`AGENTS.md`)
- [ ] Stale references removed (old paths, renamed fields, removed endpoints)
