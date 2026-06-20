"""File-backed workspace drafts — survives server restart."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_DRAFT_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "drafts"
MAX_FILES = 50
MAX_TOTAL_BYTES = 500_000


class DraftTooLargeError(ValueError):
    pass


def _draft_path(workspace_id: str, challenge_id: str) -> Path:
    return _DRAFT_ROOT / workspace_id / f"{challenge_id}.json"


def _validate_size(files: dict[str, str]) -> None:
    if len(files) > MAX_FILES:
        raise DraftTooLargeError(f"Draft exceeds {MAX_FILES} files")
    total = sum(len(content.encode("utf-8")) for content in files.values())
    if total > MAX_TOTAL_BYTES:
        raise DraftTooLargeError(f"Draft exceeds {MAX_TOTAL_BYTES} bytes")


def save_draft(
    workspace_id: str,
    challenge_id: str,
    files: dict[str, str],
    client_revision: int,
    updated_at: datetime | None = None,
) -> dict:
    _validate_size(files)
    path = _draft_path(workspace_id, challenge_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    saved_at = datetime.now(timezone.utc)
    payload = {
        "workspace_id": workspace_id,
        "challenge_id": challenge_id,
        "files": files,
        "client_revision": client_revision,
        "updated_at": (updated_at or saved_at).isoformat(),
        "server_updated_at": saved_at.isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"saved_at": saved_at.isoformat(), "revision": client_revision}


def load_draft(workspace_id: str, challenge_id: str) -> dict | None:
    path = _draft_path(workspace_id, challenge_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def delete_draft(workspace_id: str, challenge_id: str) -> bool:
    path = _draft_path(workspace_id, challenge_id)
    if not path.exists():
        return False
    path.unlink()
    return True


def clear_all() -> None:
    """Test helper — remove all drafts."""
    if _DRAFT_ROOT.exists():
        import shutil

        shutil.rmtree(_DRAFT_ROOT)
