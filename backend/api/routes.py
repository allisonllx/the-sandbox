from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..privacy_proxy.models import SanitizeRequest, SanitizeResponse
from ..privacy_proxy.sanitizer import sanitize

router = APIRouter(prefix="/api/v1/proxy", tags=["privacy-proxy"])


@router.post(
    "/sanitize",
    response_model=SanitizeResponse,
    summary="Sanitize raw content and return structural metadata only",
    description=(
        "Runs the full local privacy pipeline: zero-leak guardrail → PII masking "
        "→ NER entity counting → structural metadata extraction. "
        "Returns structural descriptors only — no raw content or PII values are "
        "included in the response."
    ),
)
def sanitize_content(request: SanitizeRequest) -> SanitizeResponse:
    try:
        metadata = sanitize(
            raw_text=request.content,
            fmt=request.format,
            guardrail_keywords=request.guardrail_keywords,
        )
        return SanitizeResponse(ok=True, metadata=metadata)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/health",
    summary="Health check",
)
def health() -> dict[str, str]:
    from ..privacy_proxy.ner_engine import is_available

    return {
        "status": "ok",
        "ner_model": "available" if is_available() else "unavailable (regex-only mode)",
    }
