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
from .scaffold_technical import finalize_starter_package, generate_scaffold
from .validator import validate_package

logger = logging.getLogger(__name__)


def config_hash(draft: PublishDraft | None, blueprint: ChallengeBlueprint | None) -> str:
    payload = {
        "draft": draft.model_dump() if draft else None,
        "blueprint": blueprint.model_dump() if blueprint else None,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def is_package_stale(
    package: ChallengePackage | None,
    draft: PublishDraft | None,
    blueprint: ChallengeBlueprint | None,
) -> bool:
    if package is None:
        return True
    active_blueprint = blueprint or package.blueprint
    return package.source_config_hash != config_hash(draft, active_blueprint)


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
    max_retries: int = 2,
) -> ChallengePackage:
    """Generate blueprint, scaffold, optional dataset, and validate."""
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
    fixture_files: dict[str, str] = {}

    starter_files: dict[str, str] = {}
    reference_solution: dict[str, str] = {}
    validation = ValidationReport(passed=False, errors=["generation not started"])

    for attempt in range(max_retries + 1):
        starter_files, reference_solution = generate_scaffold(item_id, prd, blueprint)
        if blueprint.data_plane == DataPlane.sqlite:
            db_path, anomalies = generate_dataset(item_id, preview, metadata)
            dataset_path = str(db_path)

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

    blueprint = finalize_starter_package(starter_files, prd, blueprint, draft=draft)

    cfg_hash = config_hash(draft, blueprint)

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
