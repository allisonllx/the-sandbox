from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..ai_pm import microprd as microprd_module
from ..ai_pm import relaxation as relaxation_module
from ..ai_pm import scorer as scorer_module
from ..ai_pm import store
from ..ai_pm.models import (
    BacklogItem,
    BacklogStatus,
    PublishRequest,
    PublishResponse,
    RelaxRequest,
    RelaxResponse,
    ScoreRequest,
    ScoreResponse,
    SensitivityTag,
)
from datetime import datetime, timezone

from ..sandbox.synthesizer import generate_dataset

router = APIRouter(prefix="/api/v1/triage", tags=["triage"])


@router.get(
    "/backlog",
    response_model=list[BacklogItem],
    summary="List all backlog items, sorted by severity descending",
)
def get_backlog() -> list[BacklogItem]:
    return store.list_items()


@router.get(
    "/backlog/{item_id}",
    response_model=BacklogItem,
    summary="Get a single backlog item by ID",
)
def get_item(item_id: str) -> BacklogItem:
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post(
    "/score",
    response_model=ScoreResponse,
    summary="Score a SanitizedMetadata blob and add it to the backlog",
    description=(
        "Accepts output from POST /api/v1/proxy/sanitize. "
        "Calls the LLM scorer (or heuristic fallback) with the anonymized metadata only. "
        "The scored item is saved to the in-memory backlog and its ID is returned."
    ),
)
def score_metadata(request: ScoreRequest) -> ScoreResponse:
    scores = scorer_module.score(request.metadata)
    tag = scores.tag

    item = BacklogItem(
        source_label=request.source_label,
        metadata=request.metadata,
        scores=scores,
        tag=tag,
        status=BacklogStatus.pending,
    )
    store.upsert_item(item)

    return ScoreResponse(item_id=item.id, scores=scores, tag=tag)


@router.post(
    "/relax/{item_id}",
    response_model=RelaxResponse,
    summary="Apply relaxation controls and return a before/after preview",
    description=(
        "Pure transformation — no LLM call. "
        "Returns relaxed field names and perturbed row scale for the founder to review. "
        "Does NOT publish the challenge."
    ),
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
    store.upsert_item(item)

    return RelaxResponse(item_id=item_id, preview=preview)


@router.post(
    "/publish/{item_id}",
    response_model=PublishResponse,
    summary="Approve a challenge and generate its Micro-PRD",
    description=(
        "Founder explicitly approves this item for publication. "
        "Applies the final relaxation config, calls the LLM to generate the Micro-PRD "
        "using ONLY the relaxed (de-risked) metadata, and marks the item as approved. "
        "This is the ONLY point at which an LLM call is made with challenge content."
    ),
)
def publish_item(item_id: str, request: RelaxRequest) -> PublishResponse:
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Apply final relaxation
    preview = relaxation_module.apply_relaxation(
        metadata=item.metadata,
        config=request.config,
        challenge_seed=item_id,
    )

    # Generate Micro-PRD — LLM receives only the relaxed metadata
    title = item.scores.suggested_title if item.scores else "Engineering Challenge"
    prd = microprd_module.generate(
        challenge_id=item_id,
        title=title,
        preview=preview,
        metadata=item.metadata,
    )

    db_path, anomalies = generate_dataset(item_id, preview, item.metadata)

    item.relaxation_config = request.config
    item.relaxed_preview = preview
    item.microprd = prd
    item.dataset_path = str(db_path)
    item.dataset_anomalies = anomalies
    item.published_at = datetime.now(timezone.utc)
    item.status = BacklogStatus.published
    store.upsert_item(item)

    return PublishResponse(
        item_id=item_id,
        microprd=prd,
        status=BacklogStatus.published,
    )
