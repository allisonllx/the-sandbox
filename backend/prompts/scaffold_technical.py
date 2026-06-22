"""LLM prompt for blueprint-driven technical starter generation.

LEGACY / OFF HOT PATH — dynamic Preview uses `scaffold_interpolate.generate_scaffold_from_spec()`
(deterministic stubs/tests from `TechnicalChallengeSpec`). This prompt is used only when
`build_package()` is called without `challenge_spec` and `generate_scaffold()` tries LLM
before template fallback.

The LLM receives the Micro-PRD + ChallengeBlueprint JSON in one payload — not chained
output from a prior LLM call. Signatures come from the spec on the hot path instead.
"""

from backend.prompts.shared import ANONYMIZED_METADATA_ONLY, JSON_ONLY

SCAFFOLD_TECHNICAL_SYSTEM_PROMPT = f"""You generate a bounded Python starter project for a coding challenge.

{ANONYMIZED_METADATA_ONLY}

Rules:
- Output ONLY JSON with keys: starter_files, reference_solution (both dict path→content)
- Max 12 files, max 8000 chars per file
- starter_files: TODO stubs for student edit_targets; must include README.md, docs/SPEC.md, tests/test_public.py
- reference_solution: complete working implementations passing the public tests
- No network calls, no subprocess, no os.system in any file
- Import paths use src.* package style
- Public tests must run with pytest without external services unless sqlite path is documented
- Do NOT hardcode function names in tests that are not declared in blueprint edit_targets

{JSON_ONLY}
"""
