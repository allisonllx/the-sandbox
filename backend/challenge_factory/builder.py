"""Orchestrate challenge package generation."""

from __future__ import annotations

import hashlib
import json
import logging

from ..ai_pm.models import MicroPRD, PublishDraft, RelaxedPreview
from ..privacy_proxy.models import SanitizedMetadata
from ..sandbox.synthesizer import generate_dataset
from .blueprint_planner import plan_blueprint
from .legacy_router import use_legacy_factory
from .models import ChallengeBlueprint, ChallengePackage, DataPlane, ValidationReport
from .scaffold_interpolate import generate_scaffold_from_spec, validate_contract_alignment
from .scaffold_technical import finalize_starter_package, generate_scaffold
from .spec_models import TechnicalChallengeSpec
from .spec_projection import spec_to_blueprint
from .validator import validate_package
from .workspace_sufficiency import check_browser_workspace_sufficiency

logger = logging.getLogger(__name__)


def config_hash(
    draft: PublishDraft | None,
    blueprint: ChallengeBlueprint | None,
    challenge_spec: TechnicalChallengeSpec | None = None,
) -> str:
    payload = {
        "draft": draft.model_dump() if draft else None,
        "blueprint": blueprint.model_dump() if blueprint else None,
        "challenge_spec": challenge_spec.model_dump(mode="json") if challenge_spec else None,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def is_package_stale(
    package: ChallengePackage | None,
    draft: PublishDraft | None,
    blueprint: ChallengeBlueprint | None,
    challenge_spec: TechnicalChallengeSpec | None = None,
) -> bool:
    if package is None:
        return True
    active_blueprint = blueprint or package.blueprint
    return package.source_config_hash != config_hash(draft, active_blueprint, challenge_spec)


def build_legacy_package(
    item_id: str,
    prd: MicroPRD,
    preview: RelaxedPreview,
    metadata: SanitizedMetadata,
    *,
    draft: PublishDraft | None = None,
    blueprint: ChallengeBlueprint | None = None,
    generate_product: bool = False,
) -> ChallengePackage | None:
    """Build a synthetic package record for legacy path (optional — demos skip this)."""
    return None


def build_package(
    item_id: str,
    prd: MicroPRD,
    preview: RelaxedPreview,
    metadata: SanitizedMetadata,
    *,
    draft: PublishDraft | None = None,
    founder_blueprint: ChallengeBlueprint | None = None,
    challenge_spec: TechnicalChallengeSpec | None = None,
    max_retries: int = 2,
) -> ChallengePackage:
    """Generate blueprint, scaffold, optional dataset, and validate."""
    if challenge_spec is not None:
        blueprint = spec_to_blueprint(challenge_spec)
        if founder_blueprint and founder_blueprint.starter_hints:
            blueprint.starter_hints = founder_blueprint.starter_hints
    else:
        blueprint = plan_blueprint(
            prd,
            metadata,
            draft=draft,
            founder_blueprint=founder_blueprint,
        )
        if founder_blueprint and founder_blueprint.starter_hints:
            blueprint.starter_hints = founder_blueprint.starter_hints

    dataset_path: str | None = None
    anomalies: list[str] = []
    fixture_files: dict[str, str] = dict(challenge_spec.fixtures) if challenge_spec else {}

    starter_files: dict[str, str] = {}
    reference_solution: dict[str, str] = {}
    validation = ValidationReport(passed=False, errors=["generation not started"])

    for attempt in range(max_retries + 1):
        if challenge_spec is not None:
            starter_files, reference_solution = generate_scaffold_from_spec(item_id, challenge_spec)
        else:
            starter_files, reference_solution = generate_scaffold(item_id, prd, blueprint)

        if blueprint.data_plane == DataPlane.sqlite:
            db_path, anomalies = generate_dataset(item_id, preview, metadata)
            dataset_path = str(db_path)
            from ..sandbox.synthesizer import sqlite_data_doc

            starter_files["docs/DATA.md"] = sqlite_data_doc(anomalies=anomalies)

        contract_errors: list[str] = []
        if challenge_spec is not None:
            contract_errors = validate_contract_alignment(challenge_spec, starter_files)

        sufficiency_errors = check_browser_workspace_sufficiency(starter_files, blueprint)
        all_preflight = contract_errors + sufficiency_errors
        if all_preflight:
            validation = ValidationReport(passed=False, errors=all_preflight)
            logger.warning("Package preflight failed: %s", all_preflight)
            if attempt >= max_retries:
                break
            continue

        validation = validate_package(
            starter_files,
            reference_solution,
            blueprint,
            dataset_path=dataset_path,
            fixture_files=fixture_files,
        )
        if validation.passed:
            break
        logger.warning(
            "Package validation failed (attempt %s/%s): %s",
            attempt + 1,
            max_retries + 1,
            validation.errors,
        )

    if challenge_spec is None:
        blueprint = finalize_starter_package(starter_files, prd, blueprint, draft=draft)

    cfg_hash = config_hash(draft, blueprint, challenge_spec)

    return ChallengePackage(
        blueprint=blueprint,
        starter_files=starter_files,
        reference_solution=reference_solution,
        dataset_path=dataset_path,
        fixture_files=fixture_files,
        dataset_anomalies=anomalies,
        validation=validation,
        generation_source="dynamic",
        source_config_hash=cfg_hash,
    )
