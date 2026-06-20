"""
Thin, injectable wrapper around the OpenAI chat completion API.

Design goals:
  - Single point of substitution for tests (replace with a stub via dependency injection)
  - Only accepts JSON-mode responses — callers always get a parsed dict back
  - Raises LLMUnavailableError when OPENAI_API_KEY is absent, so callers can
    fall back to heuristic scoring gracefully

Usage:
    client = LLMClient()                          # production
    client = LLMClient(api_key="sk-test-...")     # explicit key
    result  = client.chat(system=..., user=...)   # returns dict
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Protocol

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gpt-4o-mini"


class LLMUnavailableError(RuntimeError):
    """Raised when the LLM cannot be reached (missing key, network error, etc.)."""


class LLMClientProtocol(Protocol):
    """Interface every LLM client must satisfy — makes the real client mockable."""

    def chat(self, *, system: str, user: str, temperature: float = 0.2) -> dict[str, Any]: ...


class LLMClient:
    """
    Concrete OpenAI-backed client.

    Sends a single-turn chat with JSON mode enabled.
    Falls back gracefully if openai is not installed.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
    ) -> None:
        self._model = model
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")

    def _get_client(self):
        try:
            import openai
        except ImportError as exc:
            raise LLMUnavailableError(
                "openai package is not installed. Run: pip install openai"
            ) from exc

        if not self._api_key:
            raise LLMUnavailableError(
                "OPENAI_API_KEY environment variable is not set. "
                "The triage scorer will use heuristic fallback."
            )

        return openai.OpenAI(api_key=self._api_key)

    def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """
        Send a chat completion request and return the parsed JSON body.

        Args:
            system:      System prompt.
            user:        User message (should contain only anonymized metadata).
            temperature: Sampling temperature (low = more deterministic).

        Returns:
            Parsed JSON dict from the model's response.

        Raises:
            LLMUnavailableError: API key missing or openai not installed.
            ValueError:          Model returned non-JSON or malformed JSON.
        """
        client = self._get_client()

        response = client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        raw = response.choices[0].message.content or ""
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned non-JSON: {raw[:200]}") from exc


# ---------------------------------------------------------------------------
# Module-level singleton — tests can replace this with a stub
# ---------------------------------------------------------------------------

_default_client: LLMClientProtocol = LLMClient()


def get_default_client() -> LLMClientProtocol:
    return _default_client


def set_default_client(client: LLMClientProtocol) -> None:
    """Replace the default client — intended for testing only."""
    global _default_client
    _default_client = client
