"""
Relaxation controls — pure functions, no LLM, no network I/O.

Three controls:
  1. synthesize_variables  Map field names to deterministic abstract tokens
                           (e.g. "user_net_worth" → "node_weight_alpha").
                           Mapping is seeded by challenge_id so it is stable
                           across multiple calls for the same challenge.

  2. abstract_logic        Flag high-specificity field names (payment, auth,
                           health) and remap them to generic equivalents before
                           the variable synthesizer runs. This reduces the risk
                           of the synthesized names still hinting at the domain.

  3. noise_level (0.0–1.0) Perturb numeric metadata (row scale, event counts)
                           by a deterministic factor derived from the noise level
                           and the challenge seed. Same noise_level + seed always
                           produces the same numbers — demos are reproducible.
"""

from __future__ import annotations

import hashlib
import math
import random
import re

from ..privacy_proxy.models import FieldMetadata, SanitizedMetadata
from .models import RelaxationConfig, RelaxedPreview

# ---------------------------------------------------------------------------
# Variable name synthesis tables
# ---------------------------------------------------------------------------

_PREFIXES = [
    "node", "event", "stream", "vector", "weight", "score",
    "metric", "index", "tensor", "signal", "factor", "ratio",
    "density", "flux", "trace", "delta", "epoch", "batch",
]

_SUFFIXES = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta",
    "eta", "theta", "iota", "kappa", "lambda", "mu",
    "nu", "xi", "omicron", "pi", "rho", "sigma",
    "tau", "upsilon", "phi", "chi", "psi", "omega",
]

# Domain-specific terms that reveal business context → generic equivalents
_DOMAIN_ABSTRACTIONS: dict[str, str] = {
    "payment": "transaction",
    "price": "value",
    "revenue": "output_metric",
    "cost": "input_metric",
    "salary": "compensation_value",
    "net_worth": "aggregate_weight",
    "balance": "quantity",
    "invoice": "document_ref",
    "subscription": "recurring_event",
    "churn": "termination_event",
    "user": "entity",
    "customer": "entity",
    "patient": "entity",
    "employee": "entity",
    "member": "entity",
    "email": "contact_ref",
    "phone": "contact_ref",
    "address": "location_ref",
    "diagnosis": "classification_label",
    "medication": "treatment_ref",
    "ssn": "identity_ref",
    "dob": "temporal_ref",
    "credit_card": "instrument_ref",
    "auth": "access_event",
    "login": "access_event",
    "password": "credential_ref",
    "token": "access_token",
    "api_key": "access_token",
    "secret": "access_token",
}


def _synthesize_name(original: str, seed: str) -> str:
    """
    Map *original* to a stable abstract token using a deterministic hash.

    Same (original, seed) pair always produces the same output.
    """
    digest = hashlib.md5(f"{seed}:{original}".encode()).hexdigest()
    prefix = _PREFIXES[int(digest[:4], 16) % len(_PREFIXES)]
    suffix = _SUFFIXES[int(digest[4:8], 16) % len(_SUFFIXES)]
    return f"{prefix}_{suffix}"


def _abstract_field_name(name: str) -> str:
    """
    Replace known domain-specific substrings in *name* with generic equivalents.
    Applied BEFORE variable synthesis for maximum de-risking.
    """
    lower = name.lower()
    for term, replacement in _DOMAIN_ABSTRACTIONS.items():
        if term in lower:
            return replacement
    return name


_BRAND_TERMS = (
    "Grab",
    "Gojek",
    "Stripe",
    "Datadog",
    "CloudFront",
    "Intercom",
    "Shopify",
    "Uber",
    "Airbnb",
)


def abstract_brand_text(text: str, brand_proxy: str, *, enabled: bool = True) -> str:
    """Replace known company/product tokens with the public brand_proxy name."""
    if not enabled or not brand_proxy or not text:
        return text
    result = text
    for term in _BRAND_TERMS:
        result = re.sub(rf"\b{re.escape(term)}\b", brand_proxy, result, flags=re.IGNORECASE)
    return result


def _noise_factor(noise_level: float, seed: str, field: str) -> float:
    """
    Return a deterministic perturbation multiplier in [1-noise, 1+noise].
    noise_level=0.5 → multiplier somewhere in [0.5, 1.5].
    """
    if noise_level == 0.0:
        return 1.0
    digest = hashlib.md5(f"noise:{seed}:{field}".encode()).hexdigest()
    rng = random.Random(int(digest[:8], 16))
    delta = rng.uniform(-noise_level, noise_level)
    return max(0.1, 1.0 + delta)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def apply_relaxation(
    metadata: SanitizedMetadata,
    config: RelaxationConfig,
    challenge_seed: str = "default",
) -> RelaxedPreview:
    """
    Apply relaxation controls to *metadata* and return a before/after preview.

    Args:
        metadata:        Output of the privacy proxy.
        config:          Relaxation settings chosen by the founder.
        challenge_seed:  Stable identifier for this challenge (ensures
                         deterministic synthesis across preview calls).

    Returns:
        RelaxedPreview with original vs. relaxed field names and row scale.
    """
    original_names = [f.name for f in metadata.fields]
    variable_map: dict[str, str] = {}

    working_names = list(original_names)

    # --- Step 1: Abstract domain-specific logic ---
    if config.abstract_logic:
        working_names = [_abstract_field_name(n) for n in working_names]

    # --- Step 2: Synthesize variable names ---
    if config.synthesize_variables:
        synthesized: list[str] = []
        for orig, working in zip(original_names, working_names):
            token = _synthesize_name(working, challenge_seed)
            variable_map[orig] = token
            synthesized.append(token)
        working_names = synthesized

    # --- Step 3: Apply statistical noise to row scale ---
    original_scale = metadata.approximate_row_scale
    relaxed_scale: int | None = original_scale

    if original_scale is not None and config.noise_level > 0:
        factor = _noise_factor(config.noise_level, challenge_seed, "row_scale")
        relaxed_scale = max(1, math.floor(original_scale * factor))

    return RelaxedPreview(
        original_fields=original_names,
        relaxed_fields=working_names,
        original_row_scale=original_scale,
        relaxed_row_scale=relaxed_scale,
        noise_applied=config.noise_level,
        variable_map=variable_map,
    )
