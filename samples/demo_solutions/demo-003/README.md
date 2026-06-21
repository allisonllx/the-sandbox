# Optimise CDN cache-hit ratio for static assets

Challenge ID: `demo-003` · Sample reference solution

## Trade-offs

- Replaced N per-`event_id` queries with one `IN (...)` batch — fewer round-trips, predictable latency on large id lists.
- Kept `count_events_over_threshold` as a parameterized aggregate; an index on `execution_time_ms` would be the next production step.
- Empty input list returns `[]` without hitting SQLite.

## Setup

1. Download the challenge dataset to `./sandbox.sqlite`.
2. Run public tests: `pytest tests/test_public.py -v`
3. Submit via UI or `samples/demo_solutions/submit_sample.sh demo-003`
