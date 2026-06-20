"""
Tests for workspace draft persistence.
"""

from __future__ import annotations

import pytest

from backend.sandbox import draft_store


@pytest.fixture(autouse=True)
def _clear_drafts():
    draft_store.clear_all()
    yield
    draft_store.clear_all()


class TestDraftStore:
    def test_save_and_load_draft(self):
        files = {"src/queries.py": "x = 1\n"}
        draft_store.save_draft("ws-1", "demo-003", files, client_revision=1)
        loaded = draft_store.load_draft("ws-1", "demo-003")
        assert loaded is not None
        assert loaded["files"]["src/queries.py"] == "x = 1\n"

    def test_delete_draft(self):
        draft_store.save_draft("ws-1", "demo-003", {"a.py": "pass"}, client_revision=0)
        assert draft_store.delete_draft("ws-1", "demo-003") is True
        assert draft_store.load_draft("ws-1", "demo-003") is None

    def test_rejects_oversized_draft(self):
        huge = {"big.py": "x" * 600_000}
        with pytest.raises(draft_store.DraftTooLargeError):
            draft_store.save_draft("ws-1", "demo-003", huge, client_revision=0)
