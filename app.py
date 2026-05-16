"""FastAPI entry point for the Hybrid RAG BEIR API.

Run locally with:                       uvicorn app:app --reload --host 0.0.0.0 --port 8000
Or via the convenience launcher::       ./run_api.sh

The server expects the Weaviate Docker container to be running and Ollama
to be reachable at the host configured in ``configs/rag.yaml``.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import build_context
from api.routes import router
from src.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"]


def read_allowed_origins() -> list[str]:
    """Read CORS origins from MDAD_CORS_ORIGINS."""
    raw = os.environ.get("MDAD_CORS_ORIGINS", ",".join(DEFAULT_CORS_ORIGINS))
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build dependencies on startup and close them on shutdown."""
    logger.info("Starting Hybrid RAG API...")
    try:
        app.state.ctx = build_context()
        logger.info("API ready, uppy!")
    except Exception as exc:
        logger.error("Failed to build API context: %s", exc)
        app.state.ctx = None

    yield

    ctx = getattr(app.state, "ctx", None)
    if ctx is None:
        return

    ctx.close()
    logger.info("API context closed.")


def create_app() -> FastAPI:
    app = FastAPI(title="Hybrid RAG BIER API", version="0.1.0", description=("Endpoints: `/health`, `/datasets`, `/config`, `/retrieve`, `/rag`."), lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=read_allowed_origins(), allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])
    app.include_router(router, prefix="/api")
    return app


app_rag_ep = create_app()


@app_rag_ep.get("/")
def root() -> dict[str, str]:
    """Return service metadata for browser access."""
    return {"name": "Hybrid RAG - IR based on BEIR", "docs": "/docs", "openapi": "/openapi.json", "api_prefix": "/api"}
