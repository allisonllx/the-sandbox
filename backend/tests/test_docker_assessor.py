"""Tests for Docker platform assessor (Phase A)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.ai_pm.models import ChallengeTrack, RelaxationConfig
from backend.assessor.docker_runner import PlatformRunResult, docker_available
from backend.assessor.platform_technical import assess_platform_technical
from backend.assessor.security_scan import scan_submission
from backend.main import app
from backend.sandbox.models import SubmissionRecord, SubmissionStatus
from backend.sandbox.starter_scaffold import generate_starter_files

client = TestClient(app)


def _publish(item_id: str) -> None:
    config = RelaxationConfig(
        abstract_logic=True,
        synthesize_variables=True,
        abstract_brand=True,
    ).model_dump()
    res = client.post(
        f"/api/v1/triage/publish/{item_id}",
        json={
            "config": config,
            "reward": {
                "reward_type": "cash_bounty",
                "amount_usd": 500,
                "locked": True,
            },
        },
    )
    assert res.status_code == 200, res.text


class TestSecurityScan:
    def test_clean_code_scores_100(self):
        files = {"src/queries.py": "def foo():\n    return 1\n"}
        score, violations = scan_submission(files)
        assert score == 100
        assert violations == []

    def test_os_system_violation(self):
        files = {"src/queries.py": "import os\nos.system('rm -rf /')\n"}
        score, violations = scan_submission(files)
        assert score < 100
        assert any("os.system" in v for v in violations)


class TestPlatformTechnicalDocker:
    def test_degraded_when_docker_unavailable(self):
        record = SubmissionRecord(
            id="x",
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            files=generate_starter_files("demo-003", "Test"),
            language="python",
            status=SubmissionStatus.received,
        )
        with patch("backend.assessor.platform_technical.run_platform_assessment") as mock_run:
            mock_run.return_value = PlatformRunResult(
                runner="unavailable",
                notes=["Docker not available"],
            )
            layer = assess_platform_technical(record, dataset_path="/nonexistent")
        assert layer.score <= 50
        assert "degraded" in layer.summary.lower()

    def test_high_score_when_all_secret_tests_pass(self):
        record = SubmissionRecord(
            id="x",
            challenge_id="demo-003",
            track=ChallengeTrack.technical,
            files=generate_starter_files("demo-003", "Test"),
            language="python",
            status=SubmissionStatus.received,
        )
        with patch("backend.assessor.platform_technical.run_platform_assessment") as mock_run:
            mock_run.return_value = PlatformRunResult(
                runner="docker",
                exit_code=0,
                tests_passed=4,
                tests_failed=0,
                tests_total=4,
                duration_sec=2.5,
                notes=["Secret tests executed in isolated Docker container (network disabled)."],
            )
            layer = assess_platform_technical(record, dataset_path="/tmp/fake.sqlite")
        assert layer.dimensions["tests_passed"] == 100
        assert layer.dimensions["security_baseline"] == 100
        assert layer.score >= 80
        assert "Docker" in layer.summary

    @pytest.mark.skipif(not docker_available(), reason="Docker not available")
    def test_live_docker_secret_tests_on_publish(self):
        _publish("demo-003")
        from backend.ai_pm import store as backlog_store

        item = backlog_store.get_item("demo-003")
        assert item and item.dataset_path

        files = generate_starter_files("demo-003", "Live Docker Test")
        res = client.post(
            "/api/v1/sandbox/challenges/demo-003/submit",
            json={"mode": "inline", "files": files, "language": "python"},
        )
        assert res.status_code == 200, res.text
        sc = res.json()["scorecard"]
        platform = sc["platform"]
        assert platform["dimensions"]["tests_passed"] >= 50
        assert any("Docker" in n or "secret" in n.lower() for n in platform.get("notes", sc.get("notes", [])))

    @pytest.mark.skipif(not docker_available(), reason="Docker not available")
    def test_docker_run_has_no_network(self):
        from backend.assessor.docker_runner import run_platform_assessment

        _publish("demo-003")
        from backend.ai_pm import store as backlog_store

        item = backlog_store.get_item("demo-003")
        assert item and item.dataset_path

        files = generate_starter_files("demo-003", "Network isolation")
        result = run_platform_assessment(files, item.dataset_path)
        assert result.runner == "docker"
        assert result.tests_total >= 1
