"""Checks that a generated package is usable in the in-browser workspace."""

from __future__ import annotations

from .models import ChallengeBlueprint, DataPlane

_DATA_DOC_PATHS = ("docs/DATA.md", "docs/data.md", "DATA.md", "schema.md", "docs/SCHEMA.md")


def check_browser_workspace_sufficiency(
    starter_files: dict[str, str],
    blueprint: ChallengeBlueprint,
) -> list[str]:
    """
    Return validation errors when students would need opaque local downloads
    to understand or test their work in the browser editor.
    """
    errors: list[str] = []
    test_blob = starter_files.get("tests/test_public.py", "")

    if blueprint.data_plane == DataPlane.sqlite:
        if not any(path in starter_files for path in _DATA_DOC_PATHS):
            errors.append(
                "sqlite data_plane requires docs/DATA.md (schema reference) in starter_files "
                "so students can work in the browser without downloading the database first"
            )
        return errors

    if blueprint.data_plane == DataPlane.none:
        if "sandbox.sqlite" in test_blob and "pytest.skip" in test_blob:
            errors.append(
                "data_plane=none but public tests skip without sandbox.sqlite — "
                "browser Run Public Tests will not execute real assertions"
            )
        if any(
            path.endswith("db.py") and "sqlite3" in content
            for path, content in starter_files.items()
        ):
            errors.append(
                "data_plane=none but starter includes SQLite db helper — "
                "use in-memory tests or set data_plane=sqlite with docs/DATA.md"
            )

    return errors
