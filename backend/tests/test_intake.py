"""
Tests for founder intake: problem statement → local sanitize → sensitivity score.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm import store as backlog_store
from backend.ai_pm.llm_client import reset_default_client, set_default_client
from backend.main import app
from backend.tests.test_triage import _stub_llm

client = TestClient(app)


@pytest.fixture(autouse=True)
def _llm_stub():
    stub = _stub_llm()
    set_default_client(stub)
    yield
    reset_default_client()


@pytest.fixture(autouse=True)
def _cleanup_intake_items():
    before = {i.id for i in backlog_store.list_items()}
    yield
    for item in backlog_store.list_items():
        if item.id not in before:
            backlog_store.delete_item(item.id)


class TestFounderIntake:
    def test_intake_sanitizes_and_scores(self):
        res = client.post(
            "/api/v1/triage/intake",
            json={
                "problem_statement": (
                    "Our payment webhook retries duplicate charges when Stripe returns 502. "
                    "Contact lead@acme.com for context. retry_count spikes nightly."
                ),
                "source_label": "Founder brief — payment retries",
                "format": "text",
            },
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["item_id"]
        assert body["scores"]["severity"] is not None
        assert body["tag"] in ("red", "yellow", "green")
        assert body["suggested_track"] == "technical"
        assert "email" not in str(body["metadata"]).lower() or body["pii_types_stripped"]

        item = backlog_store.get_item(body["item_id"])
        assert item is not None
        assert item.status == "pending"

    def test_intake_rejects_invalid_format(self):
        res = client.post(
            "/api/v1/triage/intake",
            json={"problem_statement": "Hello", "format": "not-a-format"},
        )
        assert res.status_code == 422
        assert res.json()["detail"]["code"] == "INVALID_FORMAT"

    def test_intake_requires_non_empty_statement(self):
        res = client.post(
            "/api/v1/triage/intake",
            json={"problem_statement": ""},
        )
        assert res.status_code == 422
