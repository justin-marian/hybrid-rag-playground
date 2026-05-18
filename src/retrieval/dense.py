"""Dense vector retrieval via Weaviate ``near_vector`` queries."""

from __future__ import annotations

from typing import Any

from weaviate.classes.query import MetadataQuery

from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.retrieval.base import RetrievedHit, Retriever


class DenseRetriever(Retriever):
    """Retriever that searches Weaviate with MiniLM query embeddings."""

    name = "dense"

    def __init__(self, client: Any, collection_name: str, embedder: MiniLMEmbedder):
        super().__init__(client, collection_name)
        self.embedder = embedder

    def search(self, query: str, top_k: int = 10) -> list[RetrievedHit]:
        """Return the top-k nearest chunks for the embedded query."""
        qvec = self.embedder.encode_query(query).tolist()
        result = self.collection.query.near_vector(
            near_vector=qvec, limit=top_k,
            return_metadata=MetadataQuery(distance=True, score=True))
        return self.objects_to_hits(result.objects)
