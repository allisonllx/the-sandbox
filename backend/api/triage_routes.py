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
    IntakeRequest,
    IntakeResponse,
    PublishResponse,
    RelaxRequest,
    RelaxResponse,
    ScopeCheckResponse,
    ScoreRequest,
    ScoreResponse,
    SensitivityTag,
)
from ..challenge_factory.builder import build_package, is_package_stale
from ..challenge_factory.legacy_router import use_legacy_factory
from ..challenge_factory.models import ChallengeBlueprint, ChallengePackage, ChallengePackagePreview
from ..privacy_proxy.models import InputFormat
from ..privacy_proxy.sanitizer import sanitize
from ..sandbox.product_starter_scaffold import generate_product_starter_files
from ..sandbox.sponsor_matches import SponsorMatchesResponse, get_sponsor_matches
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


def _resolve_blueprint(item: BacklogItem, request: RelaxRequest) -> ChallengeBlueprint | None:
    if request.blueprint is not None:
        return request.blueprint
    return item.challenge_blueprint


def _generate_challenge_package(
    item: BacklogItem,
    item_id: str,
    prepared: dict,
    challenge_draft,
    request: RelaxRequest,
) -> tuple[ChallengeBlueprint | None, ChallengePackage | None, ChallengePackagePreview | None]:
    track = prepared["track"]
    if use_legacy_factory(item_id, track):
        return None, None, None

    founder_blueprint = _resolve_blueprint(item, request)
    package = build_package(
        item_id,
        prepared["prd"],
        prepared["preview"],
        item.metadata,
        draft=challenge_draft,
        founder_blueprint=founder_blueprint,
    )
    blueprint = package.blueprint
    stale = is_package_stale(package, challenge_draft, blueprint)
    preview = ChallengePackagePreview.from_package(package, stale=stale)
    return blueprint, package, preview


def _package_preview_response(
    item: BacklogItem,
    challenge_draft,
    blueprint: ChallengeBlueprint | None,
    package_preview: ChallengePackagePreview | None,
) -> tuple[ChallengeBlueprint | None, ChallengePackagePreview | None]:
    if package_preview is None and item.challenge_package is not None:
        stale = is_package_stale(item.challenge_package, challenge_draft, blueprint or item.challenge_blueprint)
        package_preview = ChallengePackagePreview.from_package(item.challenge_package, stale=stale)
    return blueprint, package_preview


    return blueprint, package_preview


def _create_backlog_item(metadata, source_label: str) -> BacklogItem:
    """Score sanitized metadata and persist a new backlog item."""
    scores = scorer_module.score(metadata)
    tag = scores.tag
    suggestion = track_router.suggest_track(metadata, source_label, scores.suggested_title)
    item = BacklogItem(
        source_label=source_label,
        metadata=metadata,
        scores=scores,
        tag=tag,
        status=BacklogStatus.pending,
        suggested_track=suggestion.track,
        brand_proxy=suggestion.brand_proxy,
        deliverable_types=suggestion.deliverable_types,
        evaluation_focus=suggestion.evaluation_focus,
    )
    store.upsert_item(item)
    return item


@router.post(
    "/intake",
    response_model=IntakeResponse,
    summary="Ingest a founder problem statement (local sanitize → sensitivity score)",
)
def intake_problem_statement(request: IntakeRequest) -> IntakeResponse:
    """
    Founder path: paste an internal problem brief without log files.

    Runs the privacy proxy locally, then scores the resulting SanitizedMetadata.
    Raw prose never leaves the process boundary.
    """
    try:
        fmt = InputFormat(request.format)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_FORMAT", "message": f"Unknown format: {request.format}"},
        ) from exc

    metadata = sanitize(request.problem_statement, fmt=fmt)

    if metadata.processing_notes and any("All content was blocked" in n for n in metadata.processing_notes):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "CONTENT_BLOCKED",
                "message": "Problem statement was fully blocked by the zero-leak guardrail.",
                "processing_notes": metadata.processing_notes,
            },
        )

    item = _create_backlog_item(metadata, request.source_label)
    assert item.scores is not None and item.suggested_track is not None

    return IntakeResponse(
        item_id=item.id,
        scores=item.scores,
        tag=item.tag or SensitivityTag.green,
        suggested_track=item.suggested_track,
        metadata=metadata,
        pii_types_stripped=[d.pii_type for d in metadata.pii_detections],
        processing_notes=list(metadata.processing_notes),
    )


@router.post(
    "/score",
    response_model=ScoreResponse,
    summary="Score a SanitizedMetadata blob and add it to the backlog",
)
def score_metadata(request: ScoreRequest) -> ScoreResponse:
    item = _create_backlog_item(request.metadata, request.source_label)
    assert item.scores is not None and item.tag is not None
    return ScoreResponse(item_id=item.id, scores=item.scores, tag=item.tag)


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
    blueprint, package, package_preview = _generate_challenge_package(
        item, item_id, prepared, challenge_draft, request
    )

    item.relaxation_config = request.config
    item.relaxed_preview = prepared["preview"]
    item.domain_preview = prepared["domain_preview"]
    item.company_profile = challenge_draft.company_profile
    item.publish_draft = challenge_draft
    item.microprd = prepared["prd"]
    item.status = BacklogStatus.reviewing
    if request.track:
        item.track = prepared["track"]
    if request.reward is not None:
        item.reward = request.reward
    if blueprint is not None:
        item.challenge_blueprint = blueprint
    if package is not None:
        item.challenge_package = package
    store.upsert_item(item)

    blueprint, package_preview = _package_preview_response(
        item, challenge_draft, blueprint, package_preview
    )

    return RelaxResponse(
        item_id=item_id,
        preview=prepared["preview"],
        domain_preview=prepared["domain_preview"],
        company_profile=challenge_draft.company_profile,
        challenge_draft=challenge_draft,
        scope_check=_scope_response(item),
        challenge_blueprint=blueprint,
        challenge_package=package_preview,
    )


@router.post(
    "/regenerate/{item_id}",
    response_model=RelaxResponse,
    summary="Re-run challenge factory after founder edits blueprint or draft",
)
def regenerate_package(item_id: str, request: RelaxRequest) -> RelaxResponse:
    """Same as relax but explicitly re-generates the challenge package."""
    return relax_item(item_id, request)


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
    draft = prepared["draft"]

    legacy = use_legacy_factory(item_id, track)

    if not legacy:
        package = item.challenge_package
        blueprint = item.challenge_blueprint or (package.blueprint if package else None)
        if package is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PACKAGE_MISSING",
                    "message": "Run Preview to generate a challenge package before publish.",
                },
            )
        if is_package_stale(package, draft, blueprint):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PACKAGE_STALE",
                    "message": "Challenge package is stale — click Regenerate after editing draft or blueprint.",
                },
            )
        if not package.validation.passed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PACKAGE_INVALID",
                    "message": "Challenge package failed validation — fix or regenerate before publish.",
                    "errors": package.validation.errors,
                },
            )
        starter_files = package.starter_files
        db_path = package.dataset_path
        anomalies = package.dataset_anomalies
    elif track == ChallengeTrack.product_feature:
        starter_files = generate_product_starter_files(
            item_id, prd.title, brand_proxy, domain_proxy=domain_transform.domain_proxy if domain_transform else None
        )
        db_path = None
        anomalies = []
    else:
        db_path, anomalies = generate_dataset(item_id, preview, item.metadata)
        starter_files = generate_starter_files(item_id, prd.title)
        db_path = str(db_path)

    item.relaxation_config = request.config
    item.relaxed_preview = preview
    item.domain_preview = domain_preview
    item.domain_proxy = domain_transform.domain_proxy if domain_transform else None
    item.microprd = prd
    item.track = track
    item.brand_proxy = brand_proxy
    item.company_profile = prepared["profile"]
    item.publish_draft = draft
    item.evaluation_focus = prepared["evaluation_focus"]
    item.reward = reward
    item.dataset_path = db_path if db_path else None
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
