"""
Thin wrapper around a local spaCy NER model.

The model runs entirely offline — no data leaves this process.
Entities of interest are counted and then the caller decides how to
handle them. We never return entity spans or values to the caller.

Supported labels:
  PERSON   → human names
  ORG      → company / organisation names
  GPE      → countries, cities, states
  PRODUCT  → product names that may reveal internal code-names

The engine degrades gracefully: if spaCy or the model is not installed
(e.g. during CI without the model downloaded), it returns empty counts
rather than raising.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import spacy as spacy_type  # noqa: F401

logger = logging.getLogger(__name__)

_LABELS_OF_INTEREST = {"PERSON", "ORG", "GPE", "PRODUCT"}
_MODEL_NAME = "en_core_web_sm"


@dataclass(frozen=True)
class NERResult:
    """Outcome of a local NER pass."""

    counts: dict[str, int]
    model_available: bool


@lru_cache(maxsize=1)
def _load_model() -> "spacy_type.Language | None":
    try:
        import spacy

        nlp = spacy.load(_MODEL_NAME, disable=["parser", "tagger", "lemmatizer"])
        logger.info("spaCy model '%s' loaded.", _MODEL_NAME)
        return nlp
    except ImportError:
        logger.warning("spaCy not installed — NER pass will be skipped.")
        return None
    except OSError:
        logger.warning(
            "spaCy model '%s' not found. Run: python -m spacy download %s",
            _MODEL_NAME,
            _MODEL_NAME,
        )
        return None


def analyze_entities(text: str) -> NERResult:
    """
    Run NER on *text* and return entity type counts plus model availability.

    Does NOT return any entity text — only type counts.
    """
    nlp = _load_model()
    if nlp is None:
        return NERResult(counts={}, model_available=False)

    doc = nlp(text)
    counts: dict[str, int] = {}
    for ent in doc.ents:
        if ent.label_ in _LABELS_OF_INTEREST:
            counts[ent.label_] = counts.get(ent.label_, 0) + 1
    return NERResult(counts=counts, model_available=True)


def count_entities(text: str) -> dict[str, int]:
    """Backward-compatible wrapper — returns counts only."""
    return analyze_entities(text).counts


def is_available() -> bool:
    return _load_model() is not None
