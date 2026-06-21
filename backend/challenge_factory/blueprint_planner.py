"""Infer ChallengeBlueprint from Micro-PRD and metadata."""

from __future__ import annotations

import json
import logging

from ..ai_pm.llm_client import LLMClientProtocol, LLMTier, LLMUnavailableError, get_default_client
from ..ai_pm.models import MicroPRD, PublishDraft, RelaxedPreview
from ..privacy_proxy.models import SanitizedMetadata
from backend.prompts.blueprint_planner import BLUEPRINT_SYSTEM_PROMPT
from .models import ChallengeBlueprint, DataPlane, TechnicalArchetype

logger = logging.getLogger(__name__)

_DB_FIELD_HINTS = frozenset(
    {"query_hash", "execution_time_ms", "table_name", "rows_scanned", "index_hit"}
)
_RETRY_FIELD_HINTS = frozenset({"retry_count", "idempotency_key", "gateway_response_code"})


def _field_names(metadata: SanitizedMetadata) -> set[str]:
    return {f.name for f in metadata.fields}


def infer_blueprint_heuristic(
    prd: MicroPRD,
    metadata: SanitizedMetadata,
    *,
    draft: PublishDraft | None = None,
) -> ChallengeBlueprint:
    """Deterministic blueprint when LLM is unavailable or for tests."""
    names = _field_names(metadata)
    stack = list(draft.stack_guidance if draft and draft.stack_guidance else prd.stack_guidance)
    if not stack:
        stack = ["Python 3.11"]

    if names & _DB_FIELD_HINTS:
        return ChallengeBlueprint(
            archetype=TechnicalArchetype.data_core,
            primary_focus="Optimize query lookups against the provided SQLite dataset",
            data_plane=DataPlane.sqlite,
            languages=["python"],
            stack_guidance=stack,
            edit_targets=["src/queries.py"],
        )

    if names & _RETRY_FIELD_HINTS:
        return ChallengeBlueprint(
            archetype=TechnicalArchetype.integration,
            primary_focus="Implement idempotent retry handling for flaky gateway responses",
            data_plane=DataPlane.none,
            languages=["python"],
            stack_guidance=stack,
            edit_targets=["src/handler.py", "src/idempotency.py"],
        )

    if metadata.approximate_row_scale and metadata.approximate_row_scale > 5000:
        return ChallengeBlueprint(
            archetype=TechnicalArchetype.algorithm,
            primary_focus="Implement efficient batch processing logic for large event streams",
            data_plane=DataPlane.none,
            languages=["python"],
            stack_guidance=stack,
            edit_targets=["src/solution.py"],
        )

    focus = (
        draft.definition_of_success[0]
        if draft and draft.definition_of_success
        else (prd.definition_of_success[0] if prd.definition_of_success else "Implement the core module")
    )
    return ChallengeBlueprint(
        archetype=TechnicalArchetype.service_module,
        primary_focus=focus[:500],
        data_plane=DataPlane.none,
        languages=["python"],
        stack_guidance=stack,
        edit_targets=["src/service.py"],
    )


def default_edit_targets(archetype: TechnicalArchetype) -> list[str]:
    mapping = {
        TechnicalArchetype.algorithm: ["src/solution.py"],
        TechnicalArchetype.service_module: ["src/service.py"],
        TechnicalArchetype.integration: ["src/handler.py", "src/idempotency.py"],
        TechnicalArchetype.data_core: ["src/queries.py"],
        TechnicalArchetype.data_adjacent: ["src/service.py"],
    }
    return list(mapping.get(archetype, ["src/service.py"]))


def _merge_founder_blueprint(
    inferred: ChallengeBlueprint,
    founder: ChallengeBlueprint | None,
) -> ChallengeBlueprint:
    if founder is None:
        return inferred
    data = inferred.model_dump()
    overrides = founder.model_dump(exclude_unset=True)
    if "archetype" in overrides:
        new_archetype = TechnicalArchetype(overrides["archetype"])
        if new_archetype != inferred.archetype and (
            "edit_targets" not in overrides or not overrides["edit_targets"]
        ):
            overrides["edit_targets"] = default_edit_targets(new_archetype)
    data.update(overrides)
    return ChallengeBlueprint.model_validate(data)


def plan_blueprint(
    prd: MicroPRD,
    metadata: SanitizedMetadata,
    *,
    draft: PublishDraft | None = None,
    founder_blueprint: ChallengeBlueprint | None = None,
    llm: LLMClientProtocol | None = None,
) -> ChallengeBlueprint:
    """Infer blueprint via LLM with heuristic fallback; founder overrides win."""
    heuristic = infer_blueprint_heuristic(prd, metadata, draft=draft)

    if founder_blueprint is not None and _founder_provided_blueprint(founder_blueprint):
        return _merge_founder_blueprint(heuristic, founder_blueprint)

    client = llm or get_default_client()
    payload = {
        "title": prd.title,
        "context": prd.context,
        "definition_of_success": prd.definition_of_success,
        "structural_constraints": prd.structural_constraints,
        "stack_guidance": draft.stack_guidance if draft else prd.stack_guidance,
        "heuristic_suggestion": heuristic.model_dump(),
    }
    try:
        result = client.chat(
            system=BLUEPRINT_SYSTEM_PROMPT,
            user=json.dumps(payload, indent=2),
            temperature=0.2,
            tier=LLMTier.sensitive,
        )
        archetype = TechnicalArchetype(result.get("archetype", heuristic.archetype.value))
        data_plane = DataPlane(result.get("data_plane", heuristic.data_plane.value))
        inferred = ChallengeBlueprint(
            archetype=archetype,
            primary_focus=str(result.get("primary_focus", heuristic.primary_focus))[:500],
            data_plane=data_plane,
            languages=list(result.get("languages", ["python"])),
            stack_guidance=list(result.get("stack_guidance", heuristic.stack_guidance)),
            edit_targets=list(result.get("edit_targets", heuristic.edit_targets)),
            starter_hints=founder_blueprint.starter_hints if founder_blueprint else None,
        )
    except (LLMUnavailableError, KeyError, ValueError, TypeError) as exc:
        logger.info("Blueprint LLM unavailable or invalid response — heuristic fallback: %s", exc)
        inferred = heuristic

    return _merge_founder_blueprint(inferred, founder_blueprint)


def _founder_provided_blueprint(blueprint: ChallengeBlueprint) -> bool:
    """True when founder explicitly set fields beyond defaults."""
    default = ChallengeBlueprint()
    return (
        blueprint.archetype != default.archetype
        or blueprint.data_plane != default.data_plane
        or blueprint.starter_hints
        or blueprint.example_files
        or blueprint.edit_targets != default.edit_targets
        or blueprint.primary_focus != default.primary_focus
    )
