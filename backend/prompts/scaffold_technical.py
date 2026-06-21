"""LLM prompt for blueprint-driven technical starter generation."""

from backend.prompts.shared import ANONYMIZED_METADATA_ONLY, JSON_ONLY

SCAFFOLD_TECHNICAL_SYSTEM_PROMPT = f"""You generate a bounded Python starter project for a coding challenge.

{ANONYMIZED_METADATA_ONLY}

Rules:
- Output ONLY JSON with keys: starter_files, reference_solution (both dict path→content)
- Max 12 files, max 8000 chars per file
- starter_files: TODO stubs for student edit_targets; must include README.md and tests/test_public.py
- reference_solution: complete working implementations passing the public tests
- No network calls, no subprocess, no os.system in any file
- Import paths use src.* package style
- Public tests must run with pytest without external services unless sqlite path is documented

{JSON_ONLY}
"""
