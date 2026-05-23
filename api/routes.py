"""HTTP routes for the RAG API."""

from __future__ import annotations

from time import perf_counter
from typing import Any

import requests
from fastapi import APIRouter, HTTPException, Request

from api.schemas import (
    ConfigResponse,
    DatasetInfo,
    DatasetsResponse,
    HealthResponse,
    Hit,
    RagRequest,
    RagResponse,
    RetrieveRequest,
    RetrieveResponse,
)
from src.rag.prompt_builder import build_prompt
from src.utils.logging import get_logger
from src.utils.paths import ROOT
from src.weaviate_io.indexer import collection_size

logger = get_logger(__name__)
router = APIRouter()


def get_context(request: Request) -> Any:
    """Return the application context stored on FastAPI state."""
    ctx = getattr(request.app.state, "ctx", None)
    if ctx is not None:
        return ctx

    raise HTTPException(503, "API context not initialized.")


def read_prompt_template(ctx: Any) -> str:
    """Read the prompt template from Markdown or fall back to rag.yaml."""
    prompt_path = ROOT / "prompts" / "rag_prompt.md"
    if not prompt_path.exists():
        return ctx.rag_cfg["prompt_template"]

    text = prompt_path.read_text(encoding="utf-8")
    block = first_fenced_block(text)
    return text if block is None else strip_fence_language(block).strip() + "\n"


def first_fenced_block(text: str) -> str | None:
    """Return the first fenced Markdown block body, if present."""
    if "```" not in text:
        return None

    parts = text.split("```")
    return parts[1] if len(parts) >= 3 else None


def strip_fence_language(block: str) -> str:
    """Remove a leading Markdown fence language tag."""
    lines = block.splitlines()

    if not lines:
        return block

    first = lines[0].strip()
    if first.startswith("{") or first.startswith("You"):
        return block

    return "\n".join(lines[1:])


def request_info(request: Request) -> dict[str, Any]:
    """Return compact request metadata for logs and debug endpoints."""
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")}


def hit_to_schema(hit: Any) -> Hit:
    """Convert a retriever hit to an API schema object."""
    return Hit(
        rank=hit.rank, chunk_id=hit.chunk_id, doc_id=hit.doc_id,
        title=hit.title, text=hit.text, score=hit.score)


def hit_debug(hit: Any) -> dict[str, Any]:
    """Return compact hit metadata for debug logs."""
    return {
        "rank": hit.rank, "chunk_id": hit.chunk_id, "doc_id": hit.doc_id,
        "title": hit.title, "score": round(float(hit.score), 6),
        "text_chars": len(hit.text or "")}


def collection_indexed_count(ctx: Any, collection: str) -> int | None:
    """Return the Weaviate collection size when available."""
    try:
        if ctx.weaviate.collections.exists(collection):
            return collection_size(ctx.weaviate, collection)
    except Exception as exc:
        logger.warning("Could not count collection %s: %s", collection, exc)

    return None


def check_weaviate_ready(ctx: Any) -> bool:
    """Check whether Weaviate is reachable."""
    try:
        return bool(ctx.weaviate.is_ready())
    except Exception as exc:
        logger.warning("Weaviate readiness check failed: %s", exc)
        return False


def check_llm_ready(ctx: Any) -> bool:
    """Check whether Ollama is reachable."""
    llm_cfg = ctx.rag_cfg.get("llm", {})
    if not llm_cfg:
        return False

    host = str(llm_cfg.get("host", "http://localhost:11434")).rstrip("/")

    try:
        response = requests.get(f"{host}/api/tags", timeout=2)
        return response.ok
    except Exception as exc:
        logger.warning("LLM reachability check failed: %s", exc)
        return False


def run_retrieval(ctx: Any, payload: RetrieveRequest | RagRequest) -> list[Any]:
    """Run the selected retriever for a request payload."""
    retriever = ctx.make_retriever(payload.dataset, payload.retriever, payload.alpha)
    return retriever.search(payload.query, top_k=payload.top_k)


def generate_answer(ctx: Any, prompt: str, model: str | None) -> tuple[str, str]:
    """Generate an answer while temporarily honoring a model override."""
    original_model = ctx.llm.model
    try:
        if model:
            ctx.llm.model = model
        return ctx.llm.generate(prompt), ctx.llm.model
    finally:
        ctx.llm.model = original_model


@router.get("/health", response_model=HealthResponse, tags=["system"], summary="Check backend readiness", description="Returns readiness information for Weaviate, Ollama, and the embedder.")
def health(request: Request) -> HealthResponse:
    """Return dependency readiness for the web app."""
    ctx = getattr(request.app.state, "ctx", None)

    if ctx is None:
        return HealthResponse(
            status="degraded",
            weaviate_ready=False, llm_reachable=False, embedder_loaded=False,
            detail="AppContext not initialised.")

    weaviate_ready = check_weaviate_ready(ctx)
    llm_ready = check_llm_ready(ctx)
    embedder_loaded = ctx.embedder is not None

    status = "ok" if weaviate_ready and llm_ready and embedder_loaded else "degraded"
    detail = None if status == "ok" else "One or more backends are unavailable."

    logger.info(
        "health status=%s weaviate=%s llm=%s embedder=%s",
        status, weaviate_ready, llm_ready, embedder_loaded)

    return HealthResponse(
        status=status, weaviate_ready=weaviate_ready,
        llm_reachable=llm_ready, embedder_loaded=embedder_loaded,
        detail=detail)


@router.get("/datasets", response_model=DatasetsResponse, tags=["system"], summary="List available datasets", description="Returns registered BEIR datasets together with their Weaviate collection names and indexed object counts.")
def list_datasets(request: Request) -> DatasetsResponse:
    """Return registered datasets and indexed object counts."""
    ctx = get_context(request)
    datasets = [DatasetInfo(
        key=key, name=spec.name, split=spec.split,
        description=spec.description, expected_size=spec.expected_size,
        collection_name=ctx.collection_for(key),
        indexed_count=collection_indexed_count(ctx, ctx.collection_for(key)))
    for key, spec in ctx.datasets.items()]

    logger.info("datasets returned=%d keys=%s", len(datasets), [dataset.key for dataset in datasets])
    return DatasetsResponse(datasets=datasets)


@router.get("/config", response_model=ConfigResponse, tags=["system"], summary="Return frontend defaults", description="Returns default dataset, retriever, top-k, alpha, embedding model, and LLM model.")
def get_config(request: Request) -> ConfigResponse:
    """Return frontend defaults and available options."""
    ctx = get_context(request)
    rag_cfg = ctx.rag_cfg["rag"]
    retrieval_cfg = ctx.retrieval_cfg["retrieval"]

    return ConfigResponse(
        embedding_model=ctx.retrieval_cfg["embedding"]["model_name"],
        default_retriever=rag_cfg["retriever"], default_top_k=int(rag_cfg["top_k"]),
        default_alpha=float(retrieval_cfg["hybrid_alpha"]),
        default_dataset=rag_cfg["dataset"],
        default_llm_model=ctx.rag_cfg["llm"]["model"],
        available_datasets=list(ctx.datasets.keys()))


@router.get("/docs-info", tags=["debug"], summary="Return API documentation links", description="Returns useful local documentation and debug URLs for the frontend.")
def docs_info(request: Request) -> dict[str, Any]:
    """Return useful API documentation links."""
    base = str(request.base_url).rstrip("/")
    return {
        "swagger": f"{base}/docs",
        "redoc": f"{base}/redoc",
        "openapi_json": f"{base}/openapi.json",
        "health": f"{base}/api/health",
        "datasets": f"{base}/api/datasets",
        "config": f"{base}/api/config",
        "retrieve": f"{base}/api/retrieve",
        "rag": f"{base}/api/rag"}


@router.get("/debug/context", tags=["debug"], summary="Inspect API context", description="Returns loaded config keys, dataset keys, collection names, and backend readiness.")
def debug_context(request: Request) -> dict[str, Any]:
    """Return detailed context diagnostics."""
    ctx = get_context(request)

    return {
        "request": request_info(request),
        "datasets": {
            key: {
                "name": spec.name,
                "split": spec.split,
                "collection": ctx.collection_for(key),
                "indexed_count": collection_indexed_count(ctx, ctx.collection_for(key))}
            for key, spec in ctx.datasets.items()},
        "retrieval": {
            "embedding_model": ctx.retrieval_cfg["embedding"]["model_name"],
            "top_k": ctx.retrieval_cfg["retrieval"]["top_k"],
            "hybrid_alpha": ctx.retrieval_cfg["retrieval"]["hybrid_alpha"],
            "target_vector": ctx.retrieval_cfg["retrieval"].get("target_vector", "default")},
        "rag": {
            "dataset": ctx.rag_cfg["rag"]["dataset"],
            "retriever": ctx.rag_cfg["rag"]["retriever"],
            "top_k": ctx.rag_cfg["rag"]["top_k"],
            "llm_provider": ctx.rag_cfg["llm"]["provider"],
            "llm_model": ctx.rag_cfg["llm"]["model"],
            "llm_host": ctx.rag_cfg["llm"]["host"]},
        "ready": {
            "weaviate": check_weaviate_ready(ctx),
            "llm": check_llm_ready(ctx),
            "embedder": ctx.embedder is not None}}


@router.post("/debug/request", tags=["debug"], summary="Echo a POST request", description="Echoes request metadata and JSON body. Useful for debugging frontend POST payloads.")
async def debug_request(request: Request) -> dict[str, Any]:
    """Echo request metadata and body."""
    try:
        body = await request.json()
    except Exception:
        body = None

    logger.info("debug request info=%s body=%s", request_info(request), body)
    return {"request": request_info(request), "body": body}


@router.post("/retrieve", response_model=RetrieveResponse, tags=["retrieval"], summary="Run retrieval", description="Runs BM25, dense, or hybrid retrieval for one query and returns ranked chunks.")
def retrieve(payload: RetrieveRequest, request: Request) -> RetrieveResponse:
    """Run the selected retriever and return ranked hits."""
    ctx = get_context(request)
    started = perf_counter()

    logger.info(
        "retrieve request dataset=%s retriever=%s top_k=%d alpha=%s query=%r", 
        payload.dataset, payload.retriever, payload.top_k, payload.alpha, payload.query)

    try:
        ctx.get_spec(payload.dataset)
        hits = run_retrieval(ctx, payload)
    except KeyError as exc:
        logger.warning("retrieve unknown dataset=%s available=%s", payload.dataset, list(ctx.datasets.keys()))
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        logger.exception("retrieve failed payload=%s", payload.model_dump())
        raise HTTPException(500, f"Retrieval failed: {exc}") from exc

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    logger.info(
        "retrieve response dataset=%s retriever=%s hits=%d elapsed_ms=%.2f top_hits=%s",
        payload.dataset, payload.retriever, len(hits), elapsed_ms, [hit_debug(hit) for hit in hits[:5]])

    return RetrieveResponse(
        query=payload.query, dataset=payload.dataset, retriever=payload.retriever,
        top_k=payload.top_k, alpha=payload.alpha, hits=[hit_to_schema(hit) for hit in hits])


@router.post("/rag", response_model=RagResponse, tags=["rag"], summary="Run generation", description="Runs retrieval, builds the prompt, calls Ollama, and returns the generated answer plus retrieved chunks.")
def rag(payload: RagRequest, request: Request) -> RagResponse:
    """Run retrieval, prompt construction, and local answer generation."""
    ctx = get_context(request)
    started = perf_counter()

    logger.info(
        "rag request dataset=%s retriever=%s top_k=%d alpha=%s model=%s query=%r", 
        payload.dataset, payload.retriever, payload.top_k, payload.alpha, payload.model, payload.query)

    try:
        spec = ctx.get_spec(payload.dataset)
        hits = run_retrieval(ctx, payload)

        prompt = build_prompt(
            template=read_prompt_template(ctx), query=payload.query, hits=hits,
            dataset_name=spec.name, max_chunk_chars=ctx.rag_cfg["rag"]["max_chunk_chars"])

        logger.info(
            "rag prompt dataset=%s hits=%d prompt_chars=%d top_hits=%s",
            payload.dataset, len(hits), len(prompt), [hit_debug(hit) for hit in hits[:5]])

        answer_text, model = generate_answer(ctx, prompt, payload.model)

    except KeyError as exc:
        logger.warning("rag unknown dataset=%s available=%s", payload.dataset, list(ctx.datasets.keys()))
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        logger.exception("rag failed payload=%s", payload.model_dump())
        raise HTTPException(500, f"RAG failed: {exc}") from exc

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    logger.info(
        "rag response dataset=%s retriever=%s model=%s answer_chars=%d elapsed_ms=%.2f",
        payload.dataset, payload.retriever, model, len(answer_text), elapsed_ms)

    return RagResponse(
        query=payload.query, dataset=payload.dataset, retriever=payload.retriever,
        top_k=payload.top_k, alpha=payload.alpha, model=model,
        answer=answer_text, prompt=prompt, hits=[hit_to_schema(hit) for hit in hits])
