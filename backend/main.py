from __future__ import annotations

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as proxy_router
from .api.sandbox_routes import router as sandbox_router
from .api.triage_routes import router as triage_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm assessor Docker image in background when the daemon is up."""
    from .assessor.docker_runner import ensure_runner_image

    threading.Thread(target=ensure_runner_image, daemon=True, name="docker-runner-warmup").start()
    yield


app = FastAPI(
    title="The Sandbox — Backend API",
    description="Zero-trust privacy proxy and platform API for thesandbox.ai",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy_router)
app.include_router(triage_router)
app.include_router(sandbox_router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"message": "The Sandbox API — see /docs for the OpenAPI UI"}
