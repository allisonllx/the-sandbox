"""Anonymous student workspace session (cookie-based, no auth)."""

from __future__ import annotations

import uuid

from fastapi import Request, Response

WORKSPACE_COOKIE = "sandbox_workspace_id"
WORKSPACE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


def get_or_create_workspace_id(request: Request, response: Response) -> str:
    """Read workspace id from cookie or issue a new one."""
    existing = request.cookies.get(WORKSPACE_COOKIE)
    if existing:
        return existing

    workspace_id = str(uuid.uuid4())
    response.set_cookie(
        key=WORKSPACE_COOKIE,
        value=workspace_id,
        httponly=True,
        samesite="lax",
        max_age=WORKSPACE_MAX_AGE,
        path="/",
    )
    return workspace_id


def read_workspace_id(request: Request) -> str | None:
    return request.cookies.get(WORKSPACE_COOKIE)
