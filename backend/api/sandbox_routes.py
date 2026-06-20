from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from ..ai_pm import store as backlog_store
from ..ai_pm.models import BacklogStatus
from ..sandbox import submission_store
from ..sandbox.models import PublishedChallenge, SubmitRequest, SubmitResponse, SubmissionStatus

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])


def _to_public(item) -> PublishedChallenge:
    if not item.microprd:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MICROPRD_MISSING", "message": "Challenge has no Micro-PRD"},
        )
    return PublishedChallenge(
        id=item.id,
        title=item.microprd.title,
        status=item.status.value,
        microprd=item.microprd,
        dataset_ready=item.dataset_path is not None,
        dataset_anomalies=item.dataset_anomalies,
        published_at=item.published_at,
    )


@router.get(
    "/challenges",
    response_model=list[PublishedChallenge],
    summary="List published public challenges",
)
def list_challenges() -> list[PublishedChallenge]:
    return [_to_public(item) for item in backlog_store.list_published()]


@router.get(
    "/challenges/{challenge_id}",
    response_model=PublishedChallenge,
    summary="Get a published challenge with Micro-PRD",
)
def get_challenge(challenge_id: str) -> PublishedChallenge:
    item = backlog_store.get_item(challenge_id)
    if not item or item.status != BacklogStatus.published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CHALLENGE_NOT_FOUND",
                "message": "Published challenge not found.",
                "hint": "Publish a challenge from the CTO dashboard first.",
            },
        )
    return _to_public(item)


@router.get(
    "/challenges/{challenge_id}/dataset",
    summary="Download the synthetic SQLite dataset for a challenge",
)
def download_dataset(challenge_id: str) -> FileResponse:
    item = backlog_store.get_item(challenge_id)
    if not item or item.status != BacklogStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    if not item.dataset_path or not Path(item.dataset_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DATASET_NOT_READY",
                "message": "Synthetic dataset has not been generated for this challenge.",
            },
        )

    return FileResponse(
        path=item.dataset_path,
        filename=f"{challenge_id}_sandbox.sqlite",
        media_type="application/x-sqlite3",
    )


@router.post(
    "/challenges/{challenge_id}/submit",
    response_model=SubmitResponse,
    summary="Submit a student solution (received by assessor queue)",
)
def submit_solution(challenge_id: str, request: SubmitRequest) -> SubmitResponse:
    item = backlog_store.get_item(challenge_id)
    if not item or item.status != BacklogStatus.published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CHALLENGE_NOT_FOUND", "message": "Published challenge not found."},
        )

    record = submission_store.save_submission(
        challenge_id=challenge_id,
        code=request.code,
        language=request.language,
    )

    return SubmitResponse(
        submission_id=record.id,
        challenge_id=challenge_id,
        status=SubmissionStatus.received,
        message=(
            "Submission received and queued for assessment. "
            "The AI Assessor will evaluate your solution in a later step."
        ),
    )


@router.get(
    "/challenges/{challenge_id}/submissions/count",
    summary="Count submissions for a challenge (debug/demo)",
)
def submission_count(challenge_id: str) -> dict[str, int | str]:
    return {
        "challenge_id": challenge_id,
        "count": submission_store.count_for_challenge(challenge_id),
    }
