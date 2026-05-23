"""
Singleton dependencies shared across requests.

Weaviate clients, the embedder, and the Ollama client lazily and
hold them on the FastAPI ``app.state`` so each request reuses them.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

import weaviate

from src.data.dataset_registry import DatasetSpec, load_datasets
from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.rag.ollama_client import OllamaClient
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.utils.io import load_yaml
from src.utils.logging import get_logger
from src.weaviate_io.client import connect_local
from src.weaviate_io.schema import collection_name

logger = get_logger(__name__)
context_lock = Lock()


@dataclass
class AppContext:
    """Container for dependencies reused by API routes."""

    retrieval_cfg: dict[str, Any]
    rag_cfg: dict[str, Any]
    datasets: dict[str, DatasetSpec]

    embedder: MiniLMEmbedder
    weaviate: weaviate.WeaviateClient
    llm: OllamaClient

    @property
    def get_llm(self) -> dict[str, Any]:
        return self.rag_cfg.get("llm", {})

    def get_spec(self, dataset_key: str) -> DatasetSpec:
        """Return the dataset spec for a registry key."""
        if dataset_key in self.datasets:
            return self.datasets[dataset_key]
        raise KeyError(f"Unknown dataset {dataset_key!r}. Known: {sorted(self.datasets)}")

    def collection_for(self, dataset_key: str) -> str:
        """Return the Weaviate collection name for a dataset."""
        spec = self.get_spec(dataset_key)
        prefix = self.retrieval_cfg["weaviate"]["collection_prefix"]
        return collection_name(prefix, spec.key)

    def make_retriever(self, dataset_key: str, retriever: str, alpha: float | None = None):
        """Build a retriever bound to one dataset collection."""
        coll = self.collection_for(dataset_key)
        retriever_name = retriever.lower()

        if retriever_name == "bm25":
            return BM25Retriever(self.weaviate, coll)

        if retriever_name == "dense":
            return DenseRetriever(self.weaviate, coll, self.embedder)

        if retriever_name == "hybrid":
            hybrid_alpha = (alpha if alpha is not None else self.retrieval_cfg["retrieval"]["hybrid_alpha"])
            return HybridRetriever(self.weaviate, coll, self.embedder, alpha=float(hybrid_alpha))

        raise ValueError(f"Unknown retriever: {retriever!r}")

    def close(self):
        """Close reusable network clients."""
        try:
            self.weaviate.close()
        except Exception as exc:
            logger.debug("Ignoring Weaviate close failure: %s", exc)


def build_embedder(cfg: dict[str, Any]) -> MiniLMEmbedder:
    """Build the shared MiniLM embedder."""
    emb = cfg["embedding"]
    max_seq_length = emb.get("max_seq_length", emb.get("max_seq_legth", 512))
    return MiniLMEmbedder(
        model_name=emb["model_name"], batch_size=emb["batch_size"],
        normalize=emb["normalize"], cache_dir=emb["cache_dir"],
        max_seq_length=int(max_seq_length))


def connect_weaviate(cfg: dict[str, Any]) -> weaviate.WeaviateClient:
    """Connect to the configured local Weaviate instance."""
    wv = cfg["weaviate"]
    return connect_local(host=wv["host"], http_port=wv["http_port"], grpc_port=wv["grpc_port"])


def build_llm(cfg: dict[str, Any]) -> OllamaClient:
    """Build the shared Ollama client."""
    llm_cfg = cfg["llm"]
    return OllamaClient(model=llm_cfg["model"], host=llm_cfg["host"], options=llm_cfg.get("options", {}))


def build_context() -> AppContext:
    """Construct an AppContext from YAML configs."""
    with context_lock:
        retrieval_cfg = load_yaml("retrieval.yaml")
        rag_cfg = load_yaml("rag.yaml")
        datasets = load_datasets("datasets.yaml")

        embedder = build_embedder(retrieval_cfg)
        client = connect_weaviate(retrieval_cfg)
        llm = build_llm(rag_cfg)

        logger.info(
            "AppContext ready: embedder=%s, weaviate=%s:%d, llm=%s",
            embedder.model_name, retrieval_cfg["weaviate"]["host"],
            retrieval_cfg["weaviate"]["http_port"], llm.model)

        return AppContext(
            retrieval_cfg=retrieval_cfg, rag_cfg=rag_cfg, datasets=datasets,
            embedder=embedder, weaviate=client, llm=llm)
