"""Pydantic request and response models for the FastAPI layer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RetrieverName = Literal["bm25", "dense", "hybrid"]


class DatasetInfo(BaseModel):
    """Dataset metadata exposed by the API."""

    key: str
    name: str
    split: str
    description: str
    expected_size: int
    collection_name: str
    indexed_count: int | None = Field(
        default=None,
        description="Number of chunk objects stored in Weaviate, or None if unavailable.")


class DatasetsResponse(BaseModel):
    """Response containing all configured datasets."""

    datasets: list[DatasetInfo]


class RetrieveRequest(BaseModel):
    """Request for sparse, dense, or hybrid retrieval."""

    query: str = Field(..., min_length=1, description="Free-text query.")
    dataset: str = Field(..., description="Dataset key from /datasets.")
    retriever: RetrieverName = "hybrid"
    top_k: int = Field(default=5, ge=1, le=50)
    alpha: float | None = Field(default=None, ge=0.0, le=1.0, description="Hybrid alpha; ignored unless retriever='hybrid'.")


class Hit(BaseModel):
    """Single retrieved chunk."""

    rank: int
    chunk_id: str
    doc_id: str
    title: str
    text: str
    score: float


class RetrieveResponse(BaseModel):
    """Retrieval response with ranked hits."""

    query: str
    dataset: str
    retriever: RetrieverName
    top_k: int
    alpha: float | None
    hits: list[Hit]


class RagRequest(BaseModel):
    """Request for retrieval followed by local answer generation."""

    query: str = Field(..., min_length=1, description="Free-text query.")
    dataset: str = Field(..., description="Dataset key from /datasets.")
    retriever: RetrieverName = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    alpha: float | None = Field(default=None, ge=0.0, le=1.0, description="Hybrid alpha; ignored unless retriever='hybrid'.")
    model: str | None = Field(default=None, description="Optional Ollama model override; defaults to configs/rag.yaml.")


class RagResponse(BaseModel):
    """RAG response with answer, prompt, and retrieved evidence."""

    query: str
    dataset: str
    retriever: RetrieverName
    top_k: int
    alpha: float | None
    model: str
    answer: str
    prompt: str
    hits: list[Hit]


class HealthResponse(BaseModel):
    """Service health and dependency readiness."""

    status: Literal["ok", "degraded"]
    weaviate_ready: bool
    ollama_reachable: bool
    embedder_loaded: bool
    detail: str | None = None


class ConfigResponse(BaseModel):
    """Frontend defaults and available runtime options."""

    embedding_model: str
    default_retriever: RetrieverName
    default_top_k: int
    default_alpha: float
    default_dataset: str
    default_llm_model: str
    available_datasets: list[str]
