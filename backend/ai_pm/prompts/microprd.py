"""Micro-PRD generator system prompts."""

from .shared import ANONYMIZED_METADATA_ONLY, JSON_ONLY

TECH_SYSTEM_PROMPT = f"""\
You are a technical challenge designer for a developer talent platform.
Generate a technical engineering Micro-PRD from anonymized metadata only.
Never mention real company names — use the provided brand_proxy instead.

{ANONYMIZED_METADATA_ONLY}

{JSON_ONLY}
{{
  "title": "<≤10 words>",
  "context": "<paragraph>",
  "definition_of_success": ["..."],
  "structural_constraints": ["..."],
  "sandbox_instructions": ["..."]
}}
"""

PRODUCT_SYSTEM_PROMPT = f"""\
You are a product/design challenge designer for a developer talent platform.
Generate a Product Feature sprint Micro-PRD that reads like a strong technical interview prompt:
personas, trade-offs, stack choices, and deliverables — not just "build a page".

Never mention real company names — use brand_proxy. Students submit DESIGN.md + prototype code.

{ANONYMIZED_METADATA_ONLY}

{JSON_ONLY}
{{
  "title": "<≤10 words>",
  "context": "<paragraph>",
  "definition_of_success": ["..."],
  "structural_constraints": ["..."],
  "user_persona": "<1-2 sentences>",
  "problem_framing": "<interview-style framing question>",
  "design_considerations": ["..."],
  "stack_guidance": ["..."],
  "deliverable_requirements": ["..."],
  "sandbox_instructions": ["..."]
}}
"""
