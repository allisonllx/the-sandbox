"""Build and apply founder-editable publish drafts before challenge release."""

from __future__ import annotations

from .models import ChallengeTrack, CompanyTechProfile, MicroPRD, PublishDraft


def build_publish_draft(
    prd: MicroPRD,
    *,
    company_profile: CompanyTechProfile,
    evaluation_focus: list[str],
) -> PublishDraft:
    """Assemble an editable draft from generated Micro-PRD + profile metadata."""
    return PublishDraft(
        title=prd.title,
        context=prd.context,
        definition_of_success=list(prd.definition_of_success),
        structural_constraints=list(prd.structural_constraints),
        evaluation_focus=list(evaluation_focus),
        company_profile=company_profile,
        user_persona=prd.user_persona,
        problem_framing=prd.problem_framing,
        design_considerations=list(prd.design_considerations),
        stack_guidance=list(prd.stack_guidance),
        deliverable_requirements=list(prd.deliverable_requirements),
    )


def apply_publish_draft(prd: MicroPRD, draft: PublishDraft) -> MicroPRD:
    """Merge founder edits onto a generated Micro-PRD before publish."""
    return prd.model_copy(
        update={
            "title": draft.title.strip(),
            "context": draft.context.strip(),
            "definition_of_success": [s.strip() for s in draft.definition_of_success if s.strip()],
            "structural_constraints": [s.strip() for s in draft.structural_constraints if s.strip()],
            "user_persona": draft.user_persona.strip() if draft.user_persona else None,
            "problem_framing": draft.problem_framing.strip() if draft.problem_framing else None,
            "design_considerations": [s.strip() for s in draft.design_considerations if s.strip()],
            "stack_guidance": [s.strip() for s in draft.stack_guidance if s.strip()],
            "deliverable_requirements": [s.strip() for s in draft.deliverable_requirements if s.strip()],
        }
    )


def draft_evaluation_focus(draft: PublishDraft) -> list[str]:
    return [s.strip() for s in draft.evaluation_focus if s.strip()]


def is_product_draft(draft: PublishDraft, track: ChallengeTrack) -> bool:
    return track == ChallengeTrack.product_feature
