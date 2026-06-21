"""Shared prompt fragments for LLM call sites."""

JSON_ONLY = "Respond with ONLY a JSON object — no markdown fences or prose outside JSON."

BLIND_AUDITION = (
    "You do NOT know the sponsor company name. Never infer or mention real brands."
)

ANONYMIZED_METADATA_ONLY = (
    "You receive ONLY anonymized structural metadata — never raw content, PII values, "
    "or business-specific row data."
)
