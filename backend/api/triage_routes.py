from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from ..ai_pm import microprd as microprd_module
from ..ai_pm import relaxation as relaxation_module
from ..ai_pm import scorer as scorer_module
from ..ai_pm import store
from ..ai_pm import track_router
from ..ai_pm.models import (
    BacklogItem,
    BacklogStatus,
    ChallengeTrack,
    PublishResponse,
    RelaxRequest,
    RelaxResponse,
    ScoreRequest,
    ScoreResponse,
    SensitivityTag,
)
from ..sandbox.product_starter_scaffold import generate_product_starter_files
from ..sandbox.starter_scaffold import generate_starter_files
from ..sandbox.synthesizer import generate_dataset

router = APIRouter(prefix="/api/v1/triage", tags=["triage"])


@router.get(
    "/backlog",
    response_model=list[BacklogItem],
    summary="List all backlog items, sorted by severity descending",
)
def get_backlog() -> list[BacklogItem]:
    items = store.list_items()
    for item in items:
        _ensure_track_suggestion(item)
    return items


@router.get(
    "/backlog/{item_id}",
    response_model=BacklogItem,
    summary="Get a single backlog item by ID",
)
def get_item(item_id: str) -> BacklogItem:
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    _ensure_track_suggestion(item)
    return item


def _ensure_track_suggestion(item: BacklogItem) -> None:
    if item.suggested_track is not None:
        return
    title = item.scores.suggested_title if item.scores else ""
    suggestion = track_router.suggest_track(item.metadata, item.source_label, title)
    item.suggested_track = suggestion.track
    if not item.brand_proxy:
        item.brand_proxy = suggestion.brand_proxy
    if not item.evaluation_focus:
        item.evaluation_focus = suggestion.evaluation_focus
    if not item.deliverable_types:
        item.deliverable_types = suggestion.deliverable_types


@router.post(
    "/score",
    response_model=ScoreResponse,
    summary="Score a SanitizedMetadata blob and add it to the backlog",
)
def score_metadata(request: ScoreRequest) -> ScoreResponse:
    scores = scorer_module.score(request.metadata)
    tag = scores.tag
    suggestion = track_router.suggest_track(
        request.metadata, request.source_label, scores.suggested_title
    )

    item = BacklogItem(
        source_label=request.source_label,
        metadata=request.metadata,
        scores=scores,
        tag=tag,
        status=BacklogStatus.pending,
        suggested_track=suggestion.track,
        brand_proxy=suggestion.brand_proxy,
        deliverable_types=suggestion.deliverable_types,
        evaluation_focus=suggestion.evaluation_focus,
    )
    store.upsert_item(item)

    return ScoreResponse(item_id=item.id, scores=scores, tag=tag)


@router.post(
    "/relax/{item_id}",
    response_model=RelaxResponse,
    summary="Apply relaxation controls and return a before/after preview",
)
def relax_item(item_id: str, request: RelaxRequest) -> RelaxResponse:
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    preview = relaxation_module.apply_relaxation(
        metadata=item.metadata,
        config=request.config,
        challenge_seed=item_id,
    )

    item.relaxation_config = request.config
    item.relaxed_preview = preview
    item.status = BacklogStatus.reviewing
    if request.track:
        item.track = request.track
    store.upsert_item(item)

    return RelaxResponse(item_id=item_id, preview=preview)


@router.post(
    "/publish/{item_id}",
    response_model=PublishResponse,
    summary="Approve a challenge and generate its Micro-PRD",
)
def publish_item(item_id: str, request: RelaxRequest) -> PublishResponse:
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    preview = relaxation_module.apply_relaxation(
        metadata=item.metadata,
        config=request.config,
        challenge_seed=item_id,
    )

    _ensure_track_suggestion(item)
    track = request.track or item.track or item.suggested_track or ChallengeTrack.technical
    brand_proxy = item.brand_proxy or track_router.suggest_track(
        item.metadata, item.source_label, item.scores.suggested_title if item.scores else ""
    ).brand_proxy
    raw_title = item.scores.suggested_title if item.scores else "Innovation Challenge"
    title = relaxation_module.abstract_brand_text(
        raw_title, brand_proxy, enabled=request.config.abstract_brand,
    )

    prd = microprd_module.generate(
        challenge_id=item_id,
        title=title,
        preview=preview,
        metadata=item.metadata,
        track=track,
        brand_proxy=brand_proxy,
        abstract_brand=request.config.abstract_brand,
    )

    if track == ChallengeTrack.product_feature:
        starter_files = generate_product_starter_files(item_id, prd.title, brand_proxy)
        db_path = None
        anomalies: list[str] = []
    else:
        db_path, anomalies = generate_dataset(item_id, preview, item.metadata)
        starter_files = generate_starter_files(item_id, prd.title)

    item.relaxation_config = request.config
    item.relaxed_preview = preview
    item.microprd = prd
    item.track = track
    item.brand_proxy = brand_proxy
    item.dataset_path = str(db_path) if db_path else None
    item.dataset_anomalies = anomalies
    item.starter_files = starter_files
    item.published_at = datetime.now(timezone.utc)
    item.status = BacklogStatus.published
    store.upsert_item(item)

    return PublishResponse(
        item_id=item_id,
        microprd=prd,
        status=BacklogStatus.published,
        track=track,
        brand_proxy=brand_proxy,
    )
