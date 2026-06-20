from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from ..ai_pm import publish_draft as publish_draft_module
from ..ai_pm import company_profile as company_profile_module
from ..ai_pm import domain_obfuscator
from ..ai_pm import microprd as microprd_module
from ..ai_pm import relaxation as relaxation_module
from ..ai_pm import scope_guard
from ..ai_pm import scorer as scorer_module
from ..ai_pm import store
from ..ai_pm import track_router
from ..ai_pm.models import (
    BacklogItem,
    BacklogStatus,
    ChallengeTrack,
    DomainObfuscationPreview,
    PublishResponse,
    RelaxRequest,
    RelaxResponse,
    ScopeCheckResponse,
    ScoreRequest,
    ScoreResponse,
    SensitivityTag,
)
from ..sandbox.sponsor_matches import SponsorMatchesResponse, get_sponsor_matches
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


@router.get(
    "/backlog/{item_id}/scope",
    response_model=ScopeCheckResponse,
    summary="Estimate student scope for a backlog item",
)
def get_scope_check(item_id: str) -> ScopeCheckResponse:
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    result = scope_guard.check_scope(item)
    return ScopeCheckResponse(
        allowed=result.allowed,
        estimated_hours=result.estimated_hours,
        reason=result.reason,
        suggested_breakdown=result.suggested_breakdown,
    )


@router.get(
    "/backlog/{item_id}/matches",
    response_model=SponsorMatchesResponse,
    summary="Sponsor match radar — candidates for this challenge only (CTO)",
)
def get_sponsor_matches_for_item(item_id: str) -> SponsorMatchesResponse:
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if item.status != BacklogStatus.published:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "CHALLENGE_NOT_PUBLISHED",
                "message": "Match radar is available after this challenge is published.",
            },
        )
    title = item.microprd.title if item.microprd else None
    return get_sponsor_matches(item_id, challenge_title=title)


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


def _domain_preview_for(item: BacklogItem, config) -> DomainObfuscationPreview | None:
    if not config.obfuscate_domain:
        return None
    title = item.scores.suggested_title if item.scores else ""
    transform = domain_obfuscator.obfuscate_domain(
        item.metadata,
        item.source_label,
        title,
        brand_proxy=item.brand_proxy or "StealthCo",
        sensitivity_tag=item.tag,
        force=True,
    )
    if not transform:
        return None
    field_names = [f.name for f in item.metadata.fields]
    public_fields = [transform.field_map.get(n, n) for n in field_names]
    return DomainObfuscationPreview(
        domain_proxy=transform.domain_proxy,
        public_title=transform.public_title,
        public_narrative=transform.public_narrative,
        internal_intent=transform.internal_intent,
        transform_rationale=transform.transform_rationale,
        brand_proxy=transform.brand_proxy,
        field_map=transform.field_map,
        public_fields=public_fields,
    )


def _apply_domain_field_obfuscation(
    item: BacklogItem,
    config,
    preview,
):
    """When domain obfuscation is on, remap relaxed column names to match public domain."""
    if not config.obfuscate_domain:
        return preview, None
    title = item.scores.suggested_title if item.scores else ""
    transform = domain_obfuscator.obfuscate_domain(
        item.metadata,
        item.source_label,
        title,
        brand_proxy=item.brand_proxy or "StealthCo",
        sensitivity_tag=item.tag,
        force=True,
    )
    if not transform or not transform.field_map:
        return preview, transform
    return domain_obfuscator.apply_field_map_to_preview(preview, transform.field_map), transform


def _scope_response(item: BacklogItem) -> ScopeCheckResponse:
    result = scope_guard.check_scope(item)
    return ScopeCheckResponse(
        allowed=result.allowed,
        estimated_hours=result.estimated_hours,
        reason=result.reason,
        suggested_breakdown=result.suggested_breakdown,
    )


def _prepare_generation(item: BacklogItem, item_id: str, request: RelaxRequest):
    """Shared relaxation + Micro-PRD generation for preview and publish."""
    preview = relaxation_module.apply_relaxation(
        metadata=item.metadata,
        config=request.config,
        challenge_seed=item_id,
    )
    domain_preview = _domain_preview_for(item, request.config)
    preview, domain_transform = _apply_domain_field_obfuscation(item, request.config, preview)

    _ensure_track_suggestion(item)
    track = request.track or item.track or item.suggested_track or ChallengeTrack.technical
    brand_proxy = item.brand_proxy or track_router.suggest_track(
        item.metadata, item.source_label, item.scores.suggested_title if item.scores else ""
    ).brand_proxy
    raw_title = item.scores.suggested_title if item.scores else "Innovation Challenge"
    title = relaxation_module.abstract_brand_text(
        raw_title, brand_proxy, enabled=request.config.abstract_brand,
    )

    if domain_transform:
        title = domain_transform.public_title
        brand_proxy = domain_transform.brand_proxy

    prd = microprd_module.generate(
        challenge_id=item_id,
        title=title,
        preview=preview,
        metadata=item.metadata,
        track=track,
        brand_proxy=brand_proxy,
        abstract_brand=request.config.abstract_brand,
        domain_transform=domain_transform,
    )

    reward = request.reward or item.reward
    profile = company_profile_module.generate_profile(item, reward=reward)
    evaluation_focus = list(item.evaluation_focus or [])

    return {
        "preview": preview,
        "domain_preview": domain_preview,
        "domain_transform": domain_transform,
        "track": track,
        "brand_proxy": brand_proxy,
        "prd": prd,
        "profile": profile,
        "evaluation_focus": evaluation_focus,
        "reward": reward,
    }


def _resolve_challenge_draft(prepared: dict, request: RelaxRequest):
    """Build or reuse founder-editable draft from generated baseline."""
    baseline = publish_draft_module.build_publish_draft(
        prepared["prd"],
        company_profile=prepared["profile"],
        evaluation_focus=prepared["evaluation_focus"],
    )
    return request.draft or baseline


def _apply_draft_to_prepared(prepared: dict, draft) -> dict:
    """Merge founder draft onto generated artifacts."""
    prepared = dict(prepared)
    prepared["prd"] = publish_draft_module.apply_publish_draft(prepared["prd"], draft)
    prepared["profile"] = draft.company_profile
    prepared["evaluation_focus"] = publish_draft_module.draft_evaluation_focus(draft)
    prepared["draft"] = draft
    return prepared


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

    prepared = _prepare_generation(item, item_id, request)
    challenge_draft = _resolve_challenge_draft(prepared, request)

    item.relaxation_config = request.config
    item.relaxed_preview = prepared["preview"]
    item.domain_preview = prepared["domain_preview"]
    item.company_profile = challenge_draft.company_profile
    item.publish_draft = challenge_draft
    item.status = BacklogStatus.reviewing
    if request.track:
        item.track = prepared["track"]
    if request.reward is not None:
        item.reward = request.reward
    store.upsert_item(item)

    return RelaxResponse(
        item_id=item_id,
        preview=prepared["preview"],
        domain_preview=prepared["domain_preview"],
        company_profile=challenge_draft.company_profile,
        challenge_draft=challenge_draft,
        scope_check=_scope_response(item),
    )


@router.post(
    "/publish/{item_id}",
    response_model=PublishResponse,
    summary="Approve a challenge and generate its Micro-PRD",
)
def publish_item(item_id: str, request: RelaxRequest) -> PublishResponse:
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    reward = request.reward or item.reward
    if reward is None or not reward.locked:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "REWARD_NOT_LOCKED",
                "message": (
                    "Every challenge must have a guaranteed reward locked before publish. "
                    "Select cash bounty or interview pass and click Lock reward (demo)."
                ),
            },
        )

    scope_result = scope_guard.check_scope(item)
    if not scope_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "SCOPE_EXCEEDED",
                "message": scope_result.reason,
                "estimated_hours": scope_result.estimated_hours,
                "suggested_breakdown": scope_result.suggested_breakdown,
            },
        )

    prepared = _prepare_generation(item, item_id, request)
    draft = request.draft or item.publish_draft
    if draft is not None:
        prepared = _apply_draft_to_prepared(prepared, draft)
    else:
        prepared["draft"] = publish_draft_module.build_publish_draft(
            prepared["prd"],
            company_profile=prepared["profile"],
            evaluation_focus=prepared["evaluation_focus"],
        )

    prd = prepared["prd"]
    preview = prepared["preview"]
    domain_preview = prepared["domain_preview"]
    domain_transform = prepared["domain_transform"]
    track = prepared["track"]
    brand_proxy = prepared["brand_proxy"]
    reward = prepared["reward"]

    if track == ChallengeTrack.product_feature:
        starter_files = generate_product_starter_files(
            item_id, prd.title, brand_proxy, domain_proxy=domain_transform.domain_proxy if domain_transform else None
        )
        db_path = None
        anomalies: list[str] = []
    else:
        db_path, anomalies = generate_dataset(item_id, preview, item.metadata)
        starter_files = generate_starter_files(item_id, prd.title)

    item.relaxation_config = request.config
    item.relaxed_preview = preview
    item.domain_preview = domain_preview
    item.domain_proxy = domain_transform.domain_proxy if domain_transform else None
    item.microprd = prd
    item.track = track
    item.brand_proxy = brand_proxy
    item.company_profile = prepared["profile"]
    item.publish_draft = prepared["draft"]
    item.evaluation_focus = prepared["evaluation_focus"]
    item.reward = reward
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
        domain_proxy=item.domain_proxy,
        reward=reward,
    )
