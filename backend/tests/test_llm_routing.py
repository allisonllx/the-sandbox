"""Tests for local vLLM + OpenAI routing in llm_client."""

from __future__ import annotations

from typing import Any

import pytest

from backend.ai_pm.llm_client import (
    LLMClient,
    LLMTier,
    LLMUnavailableError,
    RoutingLLMClient,
)


class _RecordingClient:
    def __init__(self, label: str, payload: dict[str, Any] | None = None) -> None:
        self.label = label
        self.calls: list[dict[str, Any]] = []
        self._payload = payload or {"ok": True}

    def chat(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return self._payload


def test_sensitive_prefers_local_when_cloud_blocked():
    local = _RecordingClient("local")
    cloud = _RecordingClient("cloud")
    router = RoutingLLMClient(local=local, cloud=cloud, allow_cloud_sensitive=False)

    result = router.chat(system="s", user="u", tier=LLMTier.sensitive)

    assert result == {"ok": True}
    assert len(local.calls) == 1
    assert cloud.calls == []


def test_sensitive_uses_cloud_when_only_cloud_configured():
    cloud = _RecordingClient("cloud")
    router = RoutingLLMClient(local=None, cloud=cloud)

    result = router.chat(system="s", user="u", tier=LLMTier.sensitive)

    assert result == {"ok": True}
    assert len(cloud.calls) == 1


def test_sensitive_falls_back_to_cloud_when_allowed():
    class FailingLocal:
        def chat(self, **kwargs: Any) -> dict[str, Any]:
            raise LLMUnavailableError("local down")

    cloud = _RecordingClient("cloud")
    router = RoutingLLMClient(
        local=FailingLocal(),  # type: ignore[arg-type]
        cloud=cloud,
        allow_cloud_sensitive=True,
    )

    result = router.chat(system="s", user="u", tier=LLMTier.sensitive)

    assert result == {"ok": True}
    assert len(cloud.calls) == 1


def test_standard_tier_tries_local_then_cloud():
    local = _RecordingClient("local")

    class FailingLocal:
        def chat(self, **kwargs: Any) -> dict[str, Any]:
            raise LLMUnavailableError("local down")

    cloud = _RecordingClient("cloud")
    router = RoutingLLMClient(local=FailingLocal(), cloud=cloud)  # type: ignore[arg-type]

    result = router.chat(system="s", user="u", tier=LLMTier.standard)

    assert result == {"ok": True}
    assert len(cloud.calls) == 1


def test_no_backends_raises():
    router = RoutingLLMClient(local=None, cloud=None)
    with pytest.raises(LLMUnavailableError):
        router.chat(system="s", user="u")


def test_llm_client_without_key_raises():
    client = LLMClient(api_key=None)
    with pytest.raises(LLMUnavailableError):
        client.chat(system="s", user="u")
