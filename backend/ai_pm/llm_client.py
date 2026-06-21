"""
Injectable LLM clients with local (vLLM) + cloud (OpenAI) routing.

Routing policy:
  - sensitive (default): local vLLM when LLM_BASE_URL is set; optional cloud if
    LLM_ALLOW_CLOUD_SENSITIVE=1; otherwise callers use heuristics.
  - standard: local vLLM → OpenAI → error (for non-sensitive future use).

vLLM serves an OpenAI-compatible API — set LLM_BASE_URL=http://localhost:8000/v1
"""

from __future__ import annotations

import json
import logging
import os
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)

_DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
_DEFAULT_LOCAL_API_KEY = "local"


class LLMUnavailableError(RuntimeError):
    """Raised when no configured LLM backend can serve the request."""


class LLMTier(str, Enum):
    """Data sensitivity tier for routing."""

    sensitive = "sensitive"
    standard = "standard"


class LLMClientProtocol(Protocol):
    def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        tier: LLMTier = LLMTier.sensitive,
    ) -> dict[str, Any]: ...


class LLMClient:
    """Single OpenAI-compatible backend (OpenAI cloud or vLLM local)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        label: str = "llm",
    ) -> None:
        self._label = label
        self._base_url = base_url
        self._model = model or (
            os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
            if base_url
            else os.getenv("OPENAI_MODEL", _DEFAULT_OPENAI_MODEL)
        )
        if api_key is not None:
            self._api_key = api_key
        elif base_url:
            self._api_key = os.getenv("LLM_API_KEY", _DEFAULT_LOCAL_API_KEY)
        else:
            self._api_key = os.getenv("OPENAI_API_KEY")

    def _get_client(self):
        try:
            import openai
        except ImportError as exc:
            raise LLMUnavailableError(
                "openai package is not installed. Run: pip install openai"
            ) from exc

        if not self._api_key and not self._base_url:
            raise LLMUnavailableError(
                "OPENAI_API_KEY is not set and no LLM_BASE_URL configured."
            )

        kwargs: dict[str, Any] = {"api_key": self._api_key or _DEFAULT_LOCAL_API_KEY}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return openai.OpenAI(**kwargs)

    def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        tier: LLMTier = LLMTier.sensitive,
    ) -> dict[str, Any]:
        del tier  # single-backend client ignores tier
        client = self._get_client()

        try:
            response = client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as exc:
            raise LLMUnavailableError(f"{self._label} request failed: {exc}") from exc

        raw = response.choices[0].message.content or ""
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{self._label} returned non-JSON: {raw[:200]}") from exc


class RoutingLLMClient:
    """Try local vLLM first; fall back to OpenAI per tier policy."""

    def __init__(
        self,
        *,
        local: LLMClient | None = None,
        cloud: LLMClient | None = None,
        allow_cloud_sensitive: bool = False,
    ) -> None:
        self._local = local
        self._cloud = cloud
        self._allow_cloud_sensitive = allow_cloud_sensitive

    def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        tier: LLMTier = LLMTier.sensitive,
    ) -> dict[str, Any]:
        chain = self._chain_for(tier)
        if not chain:
            raise LLMUnavailableError("No LLM backend configured (set LLM_BASE_URL and/or OPENAI_API_KEY).")

        last_error: Exception | None = None
        for name, client in chain:
            try:
                result = client.chat(
                    system=system,
                    user=user,
                    temperature=temperature,
                    tier=tier,
                )
                if name == "openai" and tier == LLMTier.sensitive:
                    logger.warning(
                        "Sensitive LLM request served by OpenAI cloud fallback "
                        "(set LLM_BASE_URL for local-only privacy)."
                    )
                return result
            except (LLMUnavailableError, ValueError) as exc:
                logger.info("%s LLM unavailable: %s", name, exc)
                last_error = exc

        raise last_error or LLMUnavailableError("All LLM backends failed.")

    def _chain_for(self, tier: LLMTier) -> list[tuple[str, LLMClient]]:
        chain: list[tuple[str, LLMClient]] = []
        if self._local:
            chain.append(("local", self._local))
        if self._cloud:
            if tier == LLMTier.standard:
                chain.append(("openai", self._cloud))
            elif self._allow_cloud_sensitive:
                chain.append(("openai", self._cloud))
        return chain


def build_routing_client() -> RoutingLLMClient:
    local: LLMClient | None = None
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    if base_url:
        local = LLMClient(base_url=base_url, label="local/vLLM")

    cloud: LLMClient | None = None
    if os.getenv("OPENAI_API_KEY"):
        cloud = LLMClient(label="openai")

    allow_cloud_sensitive = os.getenv("LLM_ALLOW_CLOUD_SENSITIVE", "").lower() in (
        "1",
        "true",
        "yes",
    )
    return RoutingLLMClient(
        local=local,
        cloud=cloud,
        allow_cloud_sensitive=allow_cloud_sensitive,
    )


_default_client: LLMClientProtocol = build_routing_client()


def get_default_client() -> LLMClientProtocol:
    return _default_client


def set_default_client(client: LLMClientProtocol) -> None:
    """Replace the default client — intended for testing only."""
    global _default_client
    _default_client = client


def reset_default_client() -> None:
    """Rebuild routing client from current environment."""
    global _default_client
    _default_client = build_routing_client()
