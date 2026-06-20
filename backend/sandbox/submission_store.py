"""Disk-backed submission store with in-memory index."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..ai_pm.models import ChallengeTrack
from .models import SubmissionRecord, SubmissionStatus

_SUBMISSION_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "submissions"
_submissions: dict[str, SubmissionRecord] = {}


def _submission_dir(submission_id: str) -> Path:
    return _SUBMISSION_ROOT / submission_id


def _normalize_files(
    code: str | None = None,
    files: dict[str, str] | None = None,
) -> dict[str, str]:
    if files:
        return dict(files)
    if code:
        return {"solution.py": code}
    raise ValueError("Submission requires code or files")


def save_submission(
    challenge_id: str,
    code: str | None = None,
    files: dict[str, str] | None = None,
    language: str = "python",
    workspace_id: str | None = None,
    mode: str = "inline",
    archive_bytes: bytes | None = None,
    links: dict[str, str] | None = None,
    track: ChallengeTrack = ChallengeTrack.technical,
    scorecard: dict | None = None,
) -> SubmissionRecord:
    file_tree = _normalize_files(code=code, files=files)
    link_map = dict(links or {})
    submission_id = str(uuid.uuid4())
    submitted_at = datetime.now(timezone.utc)
    status = SubmissionStatus.assessed if scorecard else SubmissionStatus.received

    dest = _submission_dir(submission_id)
    files_dir = dest / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    for rel_path, content in file_tree.items():
        target = files_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    if archive_bytes is not None:
        (dest / "archive.zip").write_bytes(archive_bytes)

    manifest = {
        "id": submission_id,
        "challenge_id": challenge_id,
        "workspace_id": workspace_id,
        "track": track.value,
        "language": language,
        "mode": mode,
        "status": status.value,
        "submitted_at": submitted_at.isoformat(),
        "files": list(file_tree.keys()),
        "links": link_map,
        "scorecard": scorecard,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    record = SubmissionRecord(
        id=submission_id,
        challenge_id=challenge_id,
        workspace_id=workspace_id,
        track=track,
        files=file_tree,
        links=link_map,
        language=language,
        status=status,
        submitted_at=submitted_at,
        mode=mode,
        scorecard=scorecard,
    )
    _submissions[record.id] = record
    return record


def get_submission(submission_id: str) -> SubmissionRecord | None:
    if submission_id in _submissions:
        return _submissions[submission_id]

    manifest_path = _submission_dir(submission_id) / "manifest.json"
    if not manifest_path.exists():
        return None

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files_dir = _submission_dir(submission_id) / "files"
    file_tree: dict[str, str] = {}
    for rel in manifest.get("files", []):
        file_tree[rel] = (files_dir / rel).read_text(encoding="utf-8")

    record = SubmissionRecord(
        id=manifest["id"],
        challenge_id=manifest["challenge_id"],
        workspace_id=manifest.get("workspace_id"),
        track=ChallengeTrack(manifest.get("track", ChallengeTrack.technical.value)),
        files=file_tree,
        links=manifest.get("links", {}),
        language=manifest.get("language", "python"),
        status=SubmissionStatus(manifest.get("status", SubmissionStatus.received.value)),
        submitted_at=datetime.fromisoformat(manifest["submitted_at"]),
        mode=manifest.get("mode", "inline"),
        scorecard=manifest.get("scorecard"),
    )
    _submissions[submission_id] = record
    return record


def list_for_challenge(challenge_id: str) -> list[SubmissionRecord]:
    results: list[SubmissionRecord] = []
    if _SUBMISSION_ROOT.exists():
        for entry in _SUBMISSION_ROOT.iterdir():
            if not entry.is_dir():
                continue
            record = get_submission(entry.name)
            if record and record.challenge_id == challenge_id:
                results.append(record)
    for record in _submissions.values():
        if record.challenge_id == challenge_id and record.id not in {r.id for r in results}:
            results.append(record)
    return results


def count_for_challenge(challenge_id: str) -> int:
    return len(list_for_challenge(challenge_id))


def clear() -> None:
    """Test helper."""
    _submissions.clear()
    if _SUBMISSION_ROOT.exists():
        shutil.rmtree(_SUBMISSION_ROOT)
