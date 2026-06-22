"""Project TechnicalChallengeSpec to student-facing artifacts."""

from __future__ import annotations

from ..ai_pm.models import ChallengeTrack, MicroPRD
from ..sandbox.starter_scaffold import format_edit_targets, platform_sandbox_instructions
from .models import ChallengeBlueprint, DataPlane, TechnicalArchetype
from .spec_models import TechnicalChallengeSpec


def spec_to_blueprint(spec: TechnicalChallengeSpec) -> ChallengeBlueprint:
    """Deterministic blueprint adapter — no LLM."""
    targets = list(spec.starter_layout.edit_targets) or [spec.interface_contract.primary_module]
    focus = spec.definition_of_done[0] if spec.definition_of_done else spec.startup_pain_point
    return ChallengeBlueprint(
        archetype=spec.classification.archetype,
        primary_focus=focus[:500],
        data_plane=spec.data_plane,
        languages=["python"],
        stack_guidance=list(spec.stack_guidance),
        edit_targets=targets,
    )


def spec_to_spec_md(spec: TechnicalChallengeSpec) -> str:
    api_lines = "\n".join(
        f"- `{entry.signature}`" for entry in spec.interface_contract.public_api
    )
    invariants = "\n".join(f"- {inv}" for inv in spec.interface_contract.invariants)
    dod = "\n".join(f"- {item}" for item in spec.definition_of_done)
    return f"""# Interface specification

## Scenario

{spec.scenario}

## Pain point

{spec.startup_pain_point}

## Primary module

`{spec.interface_contract.primary_module}`

## Public API

{api_lines}

## Invariants

{invariants}

## Definition of done

{dod}

## Onboarding budget

~{spec.onboarding_budget_minutes} minutes
"""


def spec_to_readme(spec: TechnicalChallengeSpec, *, challenge_id: str = "") -> str:
    targets = ", ".join(f"`{t}`" for t in spec.starter_layout.edit_targets) or f"`{spec.interface_contract.primary_module}`"
    stack = ", ".join(spec.stack_guidance) if spec.stack_guidance else "Python 3.11"
    cid = f"\n\nChallenge ID: `{challenge_id}`" if challenge_id else ""
    return f"""# {spec.title}{cid}

## Scenario

{spec.scenario}

## What you build

{spec.startup_pain_point}

## Edit targets

Focus your changes on: {targets}

See `docs/SPEC.md` for the full interface contract.

## Stack

{stack}

## Setup

1. Read `docs/SPEC.md` for the interface contract.
2. Run public tests: `pytest tests/ -v`
3. Implement the TODO sections in the edit targets.
4. Submit from the browser workspace or upload a ZIP.
"""


def spec_to_microprd(
    spec: TechnicalChallengeSpec,
    *,
    challenge_id: str,
    brand_proxy: str = "DataStream",
) -> MicroPRD:
    """Deterministic Micro-PRD projection from spec."""
    targets = list(spec.starter_layout.edit_targets) or [spec.interface_contract.primary_module]
    constraint = f"Edit the provided starter files only (main target: {format_edit_targets(targets)})"
    constraints = list(spec.stack_guidance) + [constraint]
    if spec.data_plane == DataPlane.sqlite:
        constraints.append("Use the provided SQLite dataset — see docs/DATA.md for schema reference")

    return MicroPRD(
        challenge_id=challenge_id,
        title=spec.title,
        track=ChallengeTrack.technical,
        brand_proxy=brand_proxy,
        context=spec.scenario,
        definition_of_success=list(spec.definition_of_done),
        structural_constraints=constraints,
        stack_guidance=list(spec.stack_guidance),
        sandbox_instructions=platform_sandbox_instructions(
            targets,
            data_plane=spec.data_plane.value,
        ),
    )


def archetype_display_name(archetype: TechnicalArchetype) -> str:
    return archetype.value.replace("_", " ").title()
