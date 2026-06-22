# Scripts

Operational scripts for end-to-end pipeline verification. Require backend on `http://localhost:8000` and `jq`.

| Script | Purpose |
|---|---|
| [`factory_intake.sh`](factory_intake.sh) | Founder brief → `POST /triage/intake` → relax → publish → verify starter |
| [`factory_pipeline.sh`](factory_pipeline.sh) | Log sanitize → score → relax → publish → verify |
| [`factory_common.sh`](factory_common.sh) | Shared helpers (sourced by factory scripts) |
| [`samples/run_archetype.sh`](samples/run_archetype.sh) | **Per-archetype samples** — log or intake mode |
| [`samples/run_all_previews.sh`](samples/run_all_previews.sh) | Preview-only smoke for all 10 archetypes |

Full archetype catalog: [`samples/DOCS.md`](samples/DOCS.md).

## Usage

```bash
# Default payment-retry log (auto → idempotency_engine)
./scripts/factory_pipeline.sh

# Per-archetype samples
./scripts/samples/run_archetype.sh webhook_handler
./scripts/samples/run_archetype.sh data_core intake
PREVIEW_ONLY=1 ./scripts/samples/run_all_previews.sh

# Custom log line
LOG_CONTENT='ERROR tenant_id=t1 org_id=o1' ./scripts/factory_pipeline.sh

# Custom founder brief
PROBLEM="..." ./scripts/factory_intake.sh
```

## Environment variables

| Variable | Scripts | Default |
|---|---|---|
| `BASE_URL` | positional arg `[base_url]` | `http://localhost:8000` |
| `LOG_CONTENT` | `factory_pipeline.sh` | Payment-retry log line |
| `PROBLEM` | `factory_intake.sh` | Payment retry brief |
| `SOURCE_LABEL` | all | Script-specific default |
| `ARCHETYPE` | all | `auto` (`algorithm` sample forces `algorithm`) |
| `PREVIEW_ONLY` | all | `0` — set `1` to skip publish |

## Related UI

- **Upload:** http://localhost:3000/startup/upload — same sanitize → score flow with loading page
- **Dashboard:** http://localhost:3000/startup — Preview / Publish after item appears in backlog

See [`samples/demo_solutions/DOCS.md`](../samples/demo_solutions/DOCS.md) for `demo-*` publish → submit flows.
