"""Tests for browser workspace sufficiency checks."""

from __future__ import annotations

from backend.challenge_factory.models import ChallengeBlueprint, DataPlane, TechnicalArchetype
from backend.challenge_factory.workspace_sufficiency import check_browser_workspace_sufficiency
from backend.sandbox.starter_scaffold import generate_starter_files


class TestWorkspaceSufficiency:
    def test_sqlite_requires_data_doc(self):
        blueprint = ChallengeBlueprint(
            archetype=TechnicalArchetype.data_core,
            data_plane=DataPlane.sqlite,
            edit_targets=["src/queries.py"],
        )
        starter = {"README.md": "# x", "tests/test_public.py": "def test_ok(): pass"}
        errors = check_browser_workspace_sufficiency(starter, blueprint)
        assert any("docs/DATA.md" in e for e in errors)

    def test_sqlite_legacy_starter_passes(self):
        blueprint = ChallengeBlueprint(
            archetype=TechnicalArchetype.data_core,
            data_plane=DataPlane.sqlite,
            edit_targets=["src/queries.py"],
        )
        starter = generate_starter_files("demo-003", "Test")
        assert not check_browser_workspace_sufficiency(starter, blueprint)

    def test_algorithm_rejects_sqlite_skip_tests(self):
        blueprint = ChallengeBlueprint(
            archetype=TechnicalArchetype.algorithm,
            data_plane=DataPlane.none,
            edit_targets=["src/solution.py"],
        )
        starter = {
            "README.md": "# x",
            "src/db.py": "import sqlite3",
            "tests/test_public.py": "pytest.skip('sandbox.sqlite not available')",
        }
        errors = check_browser_workspace_sufficiency(starter, blueprint)
        assert errors
