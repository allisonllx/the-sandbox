"""In-memory submission store — assessor-001 will consume from here."""

from __future__ import annotations

import uuid

from .models import SubmissionRecord, SubmissionStatus

_submissions: dict[str, SubmissionRecord] = {}


def save_submission(
    challenge_id: str,
    code: str,
    language: str = "python",
) -> SubmissionRecord:
    record = SubmissionRecord(
        id=str(uuid.uuid4()),
        challenge_id=challenge_id,
        code=code,
        language=language,
        status=SubmissionStatus.received,
    )
    _submissions[record.id] = record
    return record


def get_submission(submission_id: str) -> SubmissionRecord | None:
    return _submissions.get(submission_id)


def list_for_challenge(challenge_id: str) -> list[SubmissionRecord]:
    return [s for s in _submissions.values() if s.challenge_id == challenge_id]


def count_for_challenge(challenge_id: str) -> int:
    return len(list_for_challenge(challenge_id))


def clear() -> None:
    """Test helper."""
    _submissions.clear()
