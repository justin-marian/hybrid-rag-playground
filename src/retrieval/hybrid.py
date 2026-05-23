"""Hybrid retrieval via Weaviate's built-in hybrid endpoint."""

from __future__ import annotations

from typing import Any

from weaviate.classes.query import MetadataQuery

from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.retrieval.base import RetrievedHit, Retriever

TARGET_VECTOR = "default"


class HybridRetriever(Retriever):
    """Retrieve chunks with Weaviate hybrid BM25/vector search."""

    name = "hybrid"

    def __init__(self, client: Any, collection_name: str, embedder: MiniLMEmbedder, alpha: float):
        super().__init__(client, collection_name)
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be in [0, 1]")
        self.embedder = embedder
        self.alpha = alpha

    def search(self, query: str, top_k: int) -> list[RetrievedHit]:
        """Return top-k hybrid retrieval hits for a query."""
        qvec = self.embedder.encode_query(query).tolist()
        result = self.collection.query.hybrid(
            query=query, vector=qvec, target_vector=TARGET_VECTOR,
            alpha=self.alpha, limit=top_k,
            return_metadata=MetadataQuery(score=True, explain_score=False))

        return self.objects_to_hits(result.objects)
