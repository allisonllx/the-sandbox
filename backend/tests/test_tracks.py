"""Tests for tracks-001 and product-001: Multi-Track Innovation Hub."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm import relaxation as relaxation_module
from backend.ai_pm import store as backlog_store
from backend.ai_pm import track_router
from backend.ai_pm.models import BacklogStatus, ChallengeTrack, RelaxationConfig
from backend.main import app
from backend.sandbox import submission_store
from backend.sandbox.product_starter_scaffold import PRODUCT_STARTER_PATHS

client = TestClient(app)


def _publish(item_id: str, *, track: ChallengeTrack | None = None) -> dict:
    config = RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=True,
        noise_level=0.2,
        abstract_brand=True,
    )
    body: dict = {"config": config.model_dump()}
    if track is not None:
        body["track"] = track.value
    res = client.post(f"/api/v1/triage/publish/{item_id}", json=body)
    assert res.status_code == 200, res.text
    return res.json()


@pytest.fixture(autouse=True)
def _reset_submissions():
    submission_store.clear()
    yield
    submission_store.clear()


class TestTrackRouter:
    def test_demo_004_suggests_product_feature(self):
        item = backlog_store.get_item("demo-004")
        assert item is not None
        suggestion = track_router.suggest_track(
            item.metadata, item.source_label, item.scores.suggested_title if item.scores else ""
        )
        assert suggestion.track == ChallengeTrack.product_feature
        assert suggestion.brand_proxy == "EatsHub"

    def test_demo_003_suggests_technical(self):
        item = backlog_store.get_item("demo-003")
        assert item is not None
        suggestion = track_router.suggest_track(
            item.metadata, item.source_label, item.scores.suggested_title if item.scores else ""
        )
        assert suggestion.track == ChallengeTrack.technical


class TestAbstractBrand:
    def test_replaces_known_company_tokens(self):
        text = "Grab dine-in checkout latency vs Stripe billing"
        result = relaxation_module.abstract_brand_text(text, "EatsHub")
        assert "Grab" not in result
        assert "Stripe" not in result
        assert "EatsHub" in result


class TestProductPublish:
    def test_publish_demo_004_product_feature(self):
        body = _publish("demo-004")
        assert body["track"] == "product_feature"
        assert body["brand_proxy"] == "EatsHub"

        item = backlog_store.get_item("demo-004")
        assert item is not None
        assert item.status == BacklogStatus.published
        assert item.starter_files is not None
        assert set(item.starter_files.keys()) == set(PRODUCT_STARTER_PATHS)
        assert item.dataset_path is None
        assert "DESIGN.md" in item.starter_files

    def test_product_microprd_sections(self):
        _publish("demo-004")
        detail = client.get("/api/v1/sandbox/challenges/demo-004").json()
        prd = detail["microprd"]
        assert detail["track"] == "product_feature"
        assert prd["user_persona"]
        assert prd["problem_framing"]
        assert len(prd["design_considerations"]) >= 1
        assert "Grab" not in prd["context"]

    def test_technical_publish_unchanged(self):
        _publish("demo-003")
        detail = client.get("/api/v1/sandbox/challenges/demo-003").json()
        assert detail["track"] == "technical"
        assert detail["dataset_ready"] is True


class TestTrackFilter:
    def test_list_challenges_by_track(self):
        _publish("demo-003")
        _publish("demo-004")

        tech = client.get("/api/v1/sandbox/challenges?track=technical").json()
        product = client.get("/api/v1/sandbox/challenges?track=product_feature").json()

        tech_ids = {c["id"] for c in tech}
        product_ids = {c["id"] for c in product}

        assert "demo-003" in tech_ids
        assert "demo-004" not in tech_ids
        assert "demo-004" in product_ids
        assert "demo-003" not in product_ids


class TestProductSubmit:
    def test_submit_with_design_md_and_links(self):
        _publish("demo-004")
        files = {
            "DESIGN.md": "# Design\n\nTarget persona: mobile user.\n\nTrade-off: list vs map view.",
            "index.html": "<html><body>Merchants</body></html>",
            "src/app.js": "const cart = []; const merchants = [];",
            "src/styles.css": "@media (max-width: 768px) { .list { display: block; } }",
        }
        res = client.post(
            "/api/v1/sandbox/challenges/demo-004/submit",
            json={
                "mode": "inline",
                "files": files,
                "language": "html",
                "links": {"figma": "https://figma.com/file/demo", "deployment": "https://preview.example.com"},
            },
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["status"] == "assessed"
        assert body["scorecard"] is not None
        assert "Product Thinking" in body["scorecard"]["dimensions"]

        record = submission_store.get_submission(body["submission_id"])
        assert record is not None
        assert record.links.get("figma") == "https://figma.com/file/demo"

        scorecard = client.get(
            f"/api/v1/sandbox/submissions/{body['submission_id']}/scorecard"
        ).json()
        assert scorecard["track"] == "product_feature"
        assert scorecard["dimensions"]["Communication"] > 15
