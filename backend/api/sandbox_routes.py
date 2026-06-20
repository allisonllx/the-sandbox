from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, Response as RawResponse

from ..ai_pm import store as backlog_store
from ..ai_pm.models import BacklogStatus, ChallengeTrack
from ..assessor.registry import assess_submission
from ..sandbox import draft_store, run_jobs, submission_store
from ..sandbox.archive import ArchiveError, build_zip, extract_zip
from ..sandbox.draft_store import DraftTooLargeError
from ..sandbox.models import (
    DraftPayload,
    DraftSaveRequest,
    DraftSaveResponse,
    JobStatusResponse,
    PublishedChallenge,
    RunJobRequest,
    RunJobResponse,
    ScorecardResponse,
    StarterResponse,
    SubmissionRecord,
    SubmitRequest,
    SubmitResponse,
    SubmissionStatus,
    ValidateRequest,
    ValidateResponse,
    WorkspaceBootstrapResponse,
)
from ..sandbox.run_jobs import RunAlreadyActiveError, RunnerBusyError
from ..sandbox.product_starter_scaffold import generate_product_starter_files
from ..sandbox.starter_scaffold import generate_starter_files, platform_sandbox_instructions
from ..sandbox.product_starter_scaffold import product_platform_instructions
from ..sandbox.leaderboard import LeaderboardResponse, get_demo_leaderboard
from ..sandbox.validate import validate_python
from ..sandbox.workspace import get_or_create_workspace_id, read_workspace_id

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])


def _get_published_item(challenge_id: str):
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
    return item


def _starter_files_for(item) -> dict[str, str]:
    if item.starter_files:
        return item.starter_files
    title = item.microprd.title if item.microprd else item.id
    brand = item.brand_proxy or "Sandbox"
    track = item.track or ChallengeTrack.technical
    if track == ChallengeTrack.product_feature:
        files = generate_product_starter_files(
            item.id, title, brand, domain_proxy=getattr(item, "domain_proxy", None)
        )
    else:
        files = generate_starter_files(item.id, title)
    item.starter_files = files
    backlog_store.upsert_item(item)
    return files


def _platform_instructions_for(item) -> list[str]:
    track = item.track or ChallengeTrack.technical
    if track == ChallengeTrack.product_feature:
        equipment = item.domain_proxy == "hyperlocal_equipment"
        return product_platform_instructions(equipment_mode=equipment)
    return platform_sandbox_instructions()


def _to_public(item) -> PublishedChallenge:
    if not item.microprd:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MICROPRD_MISSING", "message": "Challenge has no Micro-PRD"},
        )
    track = item.track or ChallengeTrack.technical
    microprd = item.microprd.model_copy(
        update={"sandbox_instructions": _platform_instructions_for(item)}
    )

    return PublishedChallenge(
        id=item.id,
        title=item.microprd.title,
        status=item.status.value,
        track=track,
        brand_proxy=item.brand_proxy,
        deliverable_types=item.deliverable_types or [],
        evaluation_focus=item.evaluation_focus or [],
        microprd=microprd,
        dataset_ready=item.dataset_path is not None and Path(item.dataset_path).exists(),
        starter_ready=bool(item.starter_files) or item.status == BacklogStatus.published,
        dataset_anomalies=item.dataset_anomalies,
        pool_label=item.pool_label,
        reward=item.reward,
        published_at=item.published_at,
    )


def _submit_and_assess(
    item,
    body: SubmitRequest,
    workspace_id: str | None,
    *,
    files: dict[str, str] | None = None,
    mode: str = "inline",
    archive_bytes: bytes | None = None,
) -> SubmissionRecord:
    track = item.track or ChallengeTrack.technical
    if files is None:
        if body.mode == "legacy" and body.code:
            files = {"solution.py": body.code}
        else:
            files = body.files or {}

    pending = SubmissionRecord(
        id="pending",
        challenge_id=item.id,
        workspace_id=workspace_id,
        track=track,
        files=files,
        links=body.links or {},
        language=body.language,
        status=SubmissionStatus.received,
        mode=mode,
    )
    scorecard = assess_submission(pending, track, reward=getattr(item, "reward", None))
    return submission_store.save_submission(
        challenge_id=item.id,
        code=body.code if body.mode == "legacy" else None,
        files=files,
        language=body.language,
        workspace_id=workspace_id,
        mode=mode,
        archive_bytes=archive_bytes,
        links=body.links,
        track=track,
        scorecard=scorecard,
    )


@router.get(
    "/challenges",
    response_model=list[PublishedChallenge],
    summary="List published public challenges",
)
def list_challenges(track: ChallengeTrack | None = None) -> list[PublishedChallenge]:
    items = [_to_public(item) for item in backlog_store.list_published()]
    if track is not None:
        items = [c for c in items if c.track == track]
    return items


@router.get(
    "/challenges/{challenge_id}",
    response_model=PublishedChallenge,
    summary="Get a published challenge with Micro-PRD",
)
def get_challenge(challenge_id: str) -> PublishedChallenge:
    return _to_public(_get_published_item(challenge_id))


@router.get(
    "/challenges/{challenge_id}/starter",
    response_model=StarterResponse,
    summary="Get the multi-file starter scaffold",
)
def get_starter(challenge_id: str) -> StarterResponse:
    item = _get_published_item(challenge_id)
    return StarterResponse(challenge_id=challenge_id, files=_starter_files_for(item))


@router.get(
    "/challenges/{challenge_id}/starter/download",
    summary="Download starter scaffold as ZIP",
)
def download_starter(challenge_id: str) -> RawResponse:
    item = _get_published_item(challenge_id)
    files = _starter_files_for(item)
    zip_bytes = build_zip(files)
    return RawResponse(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{challenge_id}_starter.zip"'
        },
    )


@router.get(
    "/challenges/{challenge_id}/workspace",
    response_model=WorkspaceBootstrapResponse,
    summary="Bootstrap anonymous workspace session and load server draft",
)
def bootstrap_workspace(
    challenge_id: str,
    request: Request,
    response: Response,
) -> WorkspaceBootstrapResponse:
    _get_published_item(challenge_id)
    workspace_id = get_or_create_workspace_id(request, response)

    raw_draft = draft_store.load_draft(workspace_id, challenge_id)
    draft: DraftPayload | None = None
    if raw_draft:
        draft = DraftPayload(
            files=raw_draft["files"],
            client_revision=raw_draft.get("client_revision", 0),
            updated_at=datetime.fromisoformat(raw_draft["updated_at"]),
            server_updated_at=(
                datetime.fromisoformat(raw_draft["server_updated_at"])
                if raw_draft.get("server_updated_at")
                else None
            ),
        )

    return WorkspaceBootstrapResponse(workspace_id=workspace_id, draft=draft)


@router.put(
    "/challenges/{challenge_id}/draft",
    response_model=DraftSaveResponse,
    summary="Save workspace draft to server",
)
def save_draft(
    challenge_id: str,
    body: DraftSaveRequest,
    request: Request,
) -> DraftSaveResponse:
    _get_published_item(challenge_id)
    workspace_id = read_workspace_id(request)
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "WORKSPACE_REQUIRED",
                "message": "Workspace session not found.",
                "hint": "Call GET /challenges/{id}/workspace first.",
            },
        )

    try:
        result = draft_store.save_draft(
            workspace_id=workspace_id,
            challenge_id=challenge_id,
            files=body.files,
            client_revision=body.client_revision,
            updated_at=body.updated_at,
        )
    except DraftTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "DRAFT_TOO_LARGE", "message": str(exc)},
        ) from exc

    return DraftSaveResponse(
        saved_at=datetime.fromisoformat(result["saved_at"]),
        revision=result["revision"],
    )


@router.delete(
    "/challenges/{challenge_id}/draft",
    summary="Clear workspace draft after successful submit",
)
def delete_draft(challenge_id: str, request: Request) -> dict:
    workspace_id = read_workspace_id(request)
    if workspace_id:
        draft_store.delete_draft(workspace_id, challenge_id)
    return {"ok": True}


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate Python syntax for Monaco diagnostics",
)
def validate_code(body: ValidateRequest) -> ValidateResponse:
    diagnostics = validate_python(body.path, body.content)
    return ValidateResponse(diagnostics=diagnostics)


@router.get(
    "/challenges/{challenge_id}/dataset",
    summary="Download the synthetic SQLite dataset for a challenge",
)
def download_dataset(challenge_id: str) -> FileResponse:
    item = _get_published_item(challenge_id)

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
    "/challenges/{challenge_id}/run",
    response_model=RunJobResponse,
    summary="Enqueue public test run (async)",
)
def run_public_tests(
    challenge_id: str,
    body: RunJobRequest,
    request: Request,
) -> RunJobResponse:
    _get_published_item(challenge_id)
    workspace_id = read_workspace_id(request)

    try:
        result = run_jobs.enqueue_run(
            challenge_id=challenge_id,
            files=body.files,
            workspace_id=workspace_id,
        )
    except RunAlreadyActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "RUN_ALREADY_ACTIVE", "message": str(exc)},
        ) from exc
    except RunnerBusyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "RUNNER_BUSY", "message": str(exc)},
        ) from exc

    return RunJobResponse(job_id=result["job_id"], status=result["status"])


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Poll run job status and output",
)
def get_job_status(job_id: str) -> JobStatusResponse:
    job = run_jobs.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": "Run job not found."},
        )

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        stdout=job.get("stdout", ""),
        stderr=job.get("stderr", ""),
        exit_code=job.get("exit_code"),
        started_at=(
            datetime.fromisoformat(job["started_at"]) if job.get("started_at") else None
        ),
        finished_at=(
            datetime.fromisoformat(job["finished_at"]) if job.get("finished_at") else None
        ),
    )


@router.post(
    "/challenges/{challenge_id}/submit",
    response_model=SubmitResponse,
    summary="Submit a student solution (received by assessor queue)",
)
def submit_solution(
    challenge_id: str,
    request: Request,
    body: SubmitRequest | None = None,
) -> SubmitResponse:
    item = _get_published_item(challenge_id)
    workspace_id = read_workspace_id(request)

    if body is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_SUBMIT", "message": "Request body required."},
        )

    record = _submit_and_assess(item, body, workspace_id)

    return SubmitResponse(
        submission_id=record.id,
        challenge_id=challenge_id,
        status=record.status,
        scorecard=record.scorecard,
        message=record.scorecard.get("summary", "Submission assessed.") if record.scorecard else "Submission received.",
    )


@router.post(
    "/challenges/{challenge_id}/submit/zip",
    response_model=SubmitResponse,
    summary="Submit a ZIP archive (raw application/zip body)",
)
async def submit_zip(
    challenge_id: str,
    request: Request,
) -> SubmitResponse:
    item = _get_published_item(challenge_id)
    workspace_id = read_workspace_id(request)

    data = await request.body()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ARCHIVE", "message": "Empty request body."},
        )

    try:
        files = extract_zip(data)
    except ArchiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ARCHIVE", "message": str(exc)},
        ) from exc

    body = SubmitRequest(mode="inline", files=files, language="python")
    record = _submit_and_assess(
        item, body, workspace_id, files=files, mode="archive", archive_bytes=data
    )

    return SubmitResponse(
        submission_id=record.id,
        challenge_id=challenge_id,
        status=record.status,
        scorecard=record.scorecard,
        message=record.scorecard.get("summary", "ZIP submission assessed.") if record.scorecard else "ZIP received.",
    )


@router.get(
    "/submissions/{submission_id}/scorecard",
    response_model=ScorecardResponse,
    summary="Get assessor scorecard for a submission",
)
def get_scorecard(submission_id: str) -> ScorecardResponse:
    record = submission_store.get_submission(submission_id)
    if not record or not record.scorecard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SCORECARD_NOT_FOUND", "message": "Scorecard not available."},
        )
    sc = record.scorecard
    return ScorecardResponse(
        submission_id=submission_id,
        track=record.track,
        dimensions=sc.get("dimensions", {}),
        summary=sc.get("summary", ""),
        notes=sc.get("notes", []),
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


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Demo execution points leaderboard (stub)",
)
def get_leaderboard() -> LeaderboardResponse:
    return get_demo_leaderboard()
