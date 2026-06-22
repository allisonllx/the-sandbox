"""
Tests for factory-001: Dynamic Challenge Factory (Phase 1).
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm import store as backlog_store
from backend.ai_pm.llm_client import reset_default_client, set_default_client
from backend.ai_pm.models import BacklogStatus, RelaxationConfig
from backend.challenge_factory.builder import build_package, is_package_stale
from backend.challenge_factory.legacy_router import use_legacy_factory
from backend.challenge_factory.models import ChallengeBlueprint, DataPlane, TechnicalArchetype
from backend.challenge_factory.scaffold_technical import generate_template_scaffold
from backend.challenge_factory.validator import validate_package
from backend.main import app
from backend.privacy_proxy.models import (
    EventFrequency,
    FieldMetadata,
    InputFormat,
    SanitizedMetadata,
)
from backend.tests.test_triage import _make_metadata, _stub_llm

client = TestClient(app)


def _reward_payload():
    return {
        "reward_type": "cash_bounty",
        "amount_usd": 500,
        "interview_benchmark": 75,
        "locked": True,
    }


def _relax_config():
    return RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=False,
        noise_level=0.0,
    ).model_dump()


@pytest.fixture(autouse=True)
def _llm_stub():
    stub = _stub_llm()
    set_default_client(stub)
    yield
    reset_default_client()


@pytest.fixture(autouse=True)
def _cleanup_scored_items():
    """Remove backlog items created by factory tests so demo seed count stays stable."""
    before = {i.id for i in backlog_store.list_items()}
    yield
    for item in backlog_store.list_items():
        if item.id not in before:
            backlog_store.delete_item(item.id)


class TestLegacyRouter:
    def test_demo_items_use_legacy(self):
        assert use_legacy_factory("demo-003") is True

    def test_new_items_use_dynamic_in_auto_mode(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("CHALLENGE_FACTORY_MODE", raising=False)
        assert use_legacy_factory("custom-abc123") is False


class TestBlueprintTemplates:
    def test_algorithm_template_passes_validation(self):
        from backend.ai_pm.models import MicroPRD

        prd = MicroPRD(
            challenge_id="t-algo",
            title="Clamp values",
            context="Fix numeric clamping.",
            definition_of_success=["Clamp works"],
            structural_constraints=["Python"],
        )
        blueprint = ChallengeBlueprint(archetype=TechnicalArchetype.algorithm)
        starter, reference = generate_template_scaffold("t-algo", prd, blueprint)
        report = validate_package(starter, reference, blueprint)
        assert report.passed, report.errors

    def test_service_module_template_passes_validation(self):
        from backend.ai_pm.models import MicroPRD

        prd = MicroPRD(
            challenge_id="t-svc",
            title="Retry helper",
            context="Implement retries.",
            definition_of_success=["Retries work"],
            structural_constraints=["Python"],
        )
        blueprint = ChallengeBlueprint(archetype=TechnicalArchetype.service_module)
        starter, reference = generate_template_scaffold("t-svc", prd, blueprint)
        report = validate_package(starter, reference, blueprint)
        assert report.passed, report.errors


class TestDynamicPreviewPublish:
    def test_relax_generates_package_for_scored_item(self):
        metadata = _make_metadata(
            ["retry_count", "idempotency_key", "gateway_response_code"],
            row_scale=900,
        )
        score_res = client.post(
            "/api/v1/triage/score",
            json={"metadata": metadata.model_dump(), "source_label": "Factory test"},
        )
        assert score_res.status_code == 200
        item_id = score_res.json()["item_id"]
        assert not item_id.startswith("demo-")

        relax_res = client.post(
            f"/api/v1/triage/relax/{item_id}",
            json={"config": _relax_config()},
        )
        assert relax_res.status_code == 200, relax_res.text
        body = relax_res.json()
        assert body["challenge_package"] is not None
        assert body["challenge_blueprint"] is not None
        assert body["challenge_package"]["validation"]["passed"] is True
        assert "tests/test_public.py" in body["challenge_package"]["starter_files"]

        item = backlog_store.get_item(item_id)
        assert item is not None
        assert item.challenge_package is not None
        assert item.challenge_package.reference_solution  # stored internally

    def test_publish_requires_preview_package(self):
        metadata = _make_metadata(["worker_id", "task_status"], row_scale=200)
        item_id = client.post(
            "/api/v1/triage/score",
            json={"metadata": metadata.model_dump(), "source_label": "No preview"},
        ).json()["item_id"]

        pub = client.post(
            f"/api/v1/triage/publish/{item_id}",
            json={"config": _relax_config(), "reward": _reward_payload()},
        )
        assert pub.status_code == 422
        assert pub.json()["detail"]["code"] == "PACKAGE_MISSING"

    def test_publish_dynamic_after_preview(self):
        metadata = _make_metadata(["worker_id", "task_status"], row_scale=200)
        item_id = client.post(
            "/api/v1/triage/score",
            json={"metadata": metadata.model_dump(), "source_label": "Publish flow"},
        ).json()["item_id"]

        relax = client.post(
            f"/api/v1/triage/relax/{item_id}",
            json={"config": _relax_config(), "reward": _reward_payload()},
        )
        assert relax.status_code == 200

        pub = client.post(
            f"/api/v1/triage/publish/{item_id}",
            json={"config": _relax_config(), "reward": _reward_payload()},
        )
        assert pub.status_code == 200, pub.text
        item = backlog_store.get_item(item_id)
        assert item is not None
        assert item.status == BacklogStatus.published
        assert item.starter_files is not None
        assert "README.md" in item.starter_files

    def test_founder_blueprint_algorithm_archetype(self):
        metadata = _make_metadata(
            ["retry_count", "idempotency_key", "gateway_response_code"],
            row_scale=900,
        )
        item_id = client.post(
            "/api/v1/triage/score",
            json={"metadata": metadata.model_dump(), "source_label": "Blueprint override"},
        ).json()["item_id"]

        relax = client.post(
            f"/api/v1/triage/relax/{item_id}",
            json={
                "config": _relax_config(),
                "blueprint": {
                    "archetype": "algorithm",
                    "primary_focus": "Implement clamp_values correctly",
                    "data_plane": "none",
                    "starter_hints": "Keep src/solution.py as the main edit target.",
                },
            },
        )
        assert relax.status_code == 200
        pkg = relax.json()["challenge_package"]
        assert pkg["blueprint"]["archetype"] == "algorithm"
        assert "src/solution.py" in pkg["starter_files"]
        assert "src/solution.py" in pkg["blueprint"]["edit_targets"]
        readme = pkg["starter_files"]["README.md"]
        assert "src/solution.py" in readme
        assert "src/handler.py" not in readme

        item = backlog_store.get_item(item_id)
        assert item is not None
        assert item.microprd is not None
        joined = " ".join(item.microprd.structural_constraints + item.microprd.sandbox_instructions)
        assert "src/solution.py" in joined
        assert "src/queries.py" not in joined

        pub = client.post(
            f"/api/v1/triage/publish/{item_id}",
            json={"config": _relax_config(), "reward": _reward_payload()},
        )
        assert pub.status_code == 200, pub.text

        detail = client.get(f"/api/v1/sandbox/challenges/{item_id}").json()
        public_joined = " ".join(
            detail["microprd"]["structural_constraints"]
            + detail["microprd"]["sandbox_instructions"]
        )
        assert "src/solution.py" in public_joined
        assert "src/queries.py" not in public_joined
        assert "docs/DATA.md" not in public_joined
        starter = client.get(f"/api/v1/sandbox/challenges/{item_id}/starter").json()
        assert "src/solution.py" in starter["files"]


class TestStaleness:
    def test_package_stale_when_draft_changes(self):
        blueprint = ChallengeBlueprint(archetype=TechnicalArchetype.algorithm)
        from backend.ai_pm.models import MicroPRD, PublishDraft
        from backend.ai_pm.models import CompanyTechProfile

        prd = MicroPRD(
            challenge_id="stale-1",
            title="T",
            context="C",
            definition_of_success=["S"],
            structural_constraints=["Py"],
        )
        metadata = _make_metadata(["a"], row_scale=10)
        preview = backlog_store.get_item("demo-001").relaxed_preview  # type: ignore[union-attr]
        if preview is None:
            from backend.ai_pm import relaxation

            preview = relaxation.apply_relaxation(metadata, RelaxationConfig(), "stale-1")

        draft = PublishDraft(
            title="T",
            context="C",
            definition_of_success=["S"],
            company_profile=CompanyTechProfile(stage="Seed", team_size_range="1-10"),
        )
        package = build_package("stale-1", prd, preview, metadata, draft=draft, founder_blueprint=blueprint)
        assert not is_package_stale(package, draft, package.blueprint)

        changed = draft.model_copy(update={"context": "Changed context"})
        assert is_package_stale(package, changed, package.blueprint)


class TestBacklogApiStripsReference:
    def test_get_backlog_item_hides_reference_solution(self):
        metadata = _make_metadata(["x"], row_scale=50)
        item_id = client.post(
            "/api/v1/triage/score",
            json={"metadata": metadata.model_dump(), "source_label": "Strip ref"},
        ).json()["item_id"]
        client.post(f"/api/v1/triage/relax/{item_id}", json={"config": _relax_config()})

        res = client.get(f"/api/v1/triage/backlog/{item_id}")
        assert res.status_code == 200
        pkg = res.json().get("challenge_package")
        if pkg:
            assert "reference_solution" not in pkg
