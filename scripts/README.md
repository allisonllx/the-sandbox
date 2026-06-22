# Scripts

Operational scripts for end-to-end pipeline verification. Require backend on `http://localhost:8000` and `jq`.

| Script | Purpose |
|---|---|
| [`factory_intake.sh`](factory_intake.sh) | Founder brief → `POST /triage/intake` → relax → publish → verify starter |
| [`factory_pipeline.sh`](factory_pipeline.sh) | Log sanitize → score → relax → publish → verify (legacy two-step ingest) |

## Usage

```bash
# Founder problem statement (default payment-retry brief)
./scripts/factory_intake.sh

# Custom brief + archetype
PROBLEM="Our queue workers drop tasks under load..." ARCHETYPE=service_module ./scripts/factory_intake.sh

# Log-based ingest (sanitize + score explicitly)
./scripts/factory_pipeline.sh
ARCHETYPE=integration ./scripts/factory_pipeline.sh
```

## Environment variables

| Variable | Scripts | Default |
|---|---|---|
| `BASE_URL` | positional arg `[base_url]` | `http://localhost:8000` |
| `PROBLEM` | `factory_intake.sh` | Payment retry brief |
| `SOURCE_LABEL` | both | Script-specific default |
| `ARCHETYPE` | both | `integration` / `algorithm` |

## Related UI

- **Upload:** http://localhost:3000/startup/upload — same sanitize → score flow with loading page
- **Dashboard:** http://localhost:3000/startup — Preview / Publish after item appears in backlog

See [`samples/demo_solutions/`](../samples/demo_solutions/) for `demo-*` publish → submit flows.
