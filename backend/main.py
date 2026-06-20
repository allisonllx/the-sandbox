from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as proxy_router
from .api.triage_routes import router as triage_router

app = FastAPI(
    title="The Sandbox — Backend API",
    description="Zero-trust privacy proxy and platform API for thesandbox.ai",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy_router)
app.include_router(triage_router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"message": "The Sandbox API — see /docs for the OpenAPI UI"}
