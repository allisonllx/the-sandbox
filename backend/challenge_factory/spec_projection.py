"""Project TechnicalChallengeSpec to student-facing artifacts."""

from __future__ import annotations

from ..ai_pm.models import ChallengeTrack, MicroPRD
from ..privacy_proxy.models import SanitizedMetadata
from ..sandbox.starter_scaffold import format_edit_targets, platform_sandbox_instructions
from .models import ChallengeBlueprint, DataPlane, TechnicalArchetype
from .spec_models import TechnicalChallengeSpec


def _field_summary(metadata: SanitizedMetadata | None, limit: int = 6) -> str:
    if not metadata or not metadata.fields:
        return ""
    return ", ".join(f"`{field.name}`" for field in metadata.fields[:limit])


def format_spec_examples(spec: TechnicalChallengeSpec) -> str:
    """Render typed I/O examples for the student brief."""
    if not spec.examples:
        return ""

    lines = ["**Examples:**"]
    for example in spec.examples[:4]:
        lines.append(f"- **{example.label.strip()}** — `{example.signature.strip()}`")
        if example.input_sample.strip():
            lines.append(f"  - Input: {example.input_sample.strip()}")
        if example.output_sample.strip():
            lines.append(f"  - Output: {example.output_sample.strip()}")
        if example.notes.strip():
            lines.append(f"  - Note: {example.notes.strip()}")
    return "\n".join(lines)


def format_spec_context(
    spec: TechnicalChallengeSpec,
    *,
    metadata: SanitizedMetadata | None = None,
) -> str:
    """Assignment-style brief: scenario, background, constraints, examples, and task."""
    parts: list[str] = [f"**Scenario:** {spec.scenario.strip()}"]

    pain = spec.startup_pain_point.strip()
    if pain and pain.lower() not in spec.scenario.lower():
        parts.extend(["", f"**Background:** {pain}"])

    fields = _field_summary(metadata)
    if fields:
        parts.extend(["", f"**Signals in the intake:** {fields}."])

    if spec.interface_contract.invariants:
        inv = "; ".join(spec.interface_contract.invariants[:4])
        parts.extend(["", f"**Constraints:** {inv}"])

    examples_block = format_spec_examples(spec)
    if examples_block:
        parts.extend(["", examples_block])

    if spec.definition_of_done:
        task = ". ".join(item.strip().rstrip(".") for item in spec.definition_of_done[:4])
    else:
        module = spec.interface_contract.primary_module
        task = f"Implement the required behaviour in `{module}` and pass all public tests"
    parts.extend(["", f"**Your task:** {task}."])

    return "\n".join(parts)


def spec_success_criteria(
    spec: TechnicalChallengeSpec,
    *,
    edit_targets: list[str] | None = None,
) -> list[str]:
    """Archetype-specific success criteria plus minimal platform checks."""
    targets = edit_targets or list(spec.starter_layout.edit_targets) or [
        spec.interface_contract.primary_module
    ]
    criteria: list[str] = []
    seen: set[str] = set()

    def add(line: str) -> None:
        key = line.strip().lower()
        if key and key not in seen:
            seen.add(key)
            criteria.append(line.strip())

    for item in spec.definition_of_done:
        add(item)
    for inv in spec.interface_contract.invariants:
        add(inv)

    add(f"Implement the required behaviour in {format_edit_targets(targets)}.")
    add("All public tests pass via Run Public Tests in the browser workspace.")
    return criteria


def spec_to_blueprint(spec: TechnicalChallengeSpec) -> ChallengeBlueprint:
    """Deterministic blueprint adapter — no LLM."""
    targets = list(spec.starter_layout.edit_targets) or [spec.interface_contract.primary_module]
    if spec.definition_of_done:
        focus = ". ".join(spec.definition_of_done[:2])
    else:
        focus = spec.startup_pain_point or spec.scenario
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
    example_lines: list[str] = []
    for example in spec.examples:
        example_lines.append(f"### {example.label}")
        example_lines.append(f"- Signature: `{example.signature}`")
        example_lines.append(f"- Input: {example.input_sample}")
        example_lines.append(f"- Output: {example.output_sample}")
        if example.notes.strip():
            example_lines.append(f"- Note: {example.notes}")
    examples_md = "\n\n".join(example_lines) if example_lines else "_No examples provided._"
    return f"""# Interface specification

## Scenario

{spec.scenario}

## Pain point

{spec.startup_pain_point}

## Examples

{examples_md}

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
    metadata: SanitizedMetadata | None = None,
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
        context=format_spec_context(spec, metadata=metadata),
        definition_of_success=spec_success_criteria(spec, edit_targets=targets),
        structural_constraints=constraints,
        stack_guidance=list(spec.stack_guidance),
        sandbox_instructions=platform_sandbox_instructions(
            targets,
            data_plane=spec.data_plane.value,
        ),
    )


def archetype_display_name(archetype: TechnicalArchetype) -> str:
    return archetype.value.replace("_", " ").title()
