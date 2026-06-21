# Sample demo solutions

Reference submissions for testing publish → submit → scorecard → Match Radar without writing code from scratch.

## Prerequisites

```bash
# Terminal 1 — backend
python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — optional frontend
cd frontend && npm run dev

# Optional — full platform secret tests on demo-003
docker build -t the-sandbox-runner docker/sandbox-runner
```

## Samples included

| Folder | Track | What it demonstrates |
|---|---|---|
| `demo-003/` | Technical | Optimized `src/queries.py` (passes Docker secret tests) + README trade-offs |
| `demo-004/` | Product | Filled `DESIGN.md` + merchant discovery starter prototype |
| `demo-005/` | Product | Equipment-locker variant (`mock/inventory.json`) — use after publishing with domain obfuscation |

`demo-006/` uses the same technical pattern as `demo-003` — run `submit_sample.py demo-003` against a published `demo-006` if needed, or copy the folder.

`demo-007` cannot be published (scope-cap demo).

## Quick test (one command)

Publish + submit in one shot:

```bash
chmod +x samples/demo_solutions/*.sh
./samples/demo_solutions/test_sample.sh demo-003
./samples/demo_solutions/test_sample.sh demo-004
./samples/demo_solutions/test_sample.sh demo-005   # publishes with obfuscate_domain
```

## Step by step

```bash
# 1. Publish (locks reward, sets track / obfuscation as needed)
./samples/demo_solutions/publish_sample.sh demo-003

# 2. Submit sample files
./samples/demo_solutions/submit_sample.sh demo-003

# 3. Open Match Radar (startup)
open http://localhost:3000/startup/matches/demo-003
```

Or paste files from `demo-003/` into the Monaco workspace in the browser and click **Submit Project**.

## Verify locally (demo-003)

After downloading the challenge dataset to `samples/demo_solutions/demo-003/sandbox.sqlite`:

```bash
cd samples/demo_solutions/demo-003
pytest tests/test_public.py -v
```

## API responses

Scripts print JSON including `submission_id`. Fetch the scorecard:

```bash
curl -s http://localhost:8000/api/v1/sandbox/submissions/<submission_id>/scorecard | python -m json.tool
```

Match radar (live after submit):

```bash
curl -s http://localhost:8000/api/v1/triage/backlog/demo-003/matches | python -m json.tool
```
