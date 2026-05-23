"""BM25 retrieval via Weaviate's built-in inverted index."""

from __future__ import annotations

from weaviate.classes.query import MetadataQuery

from src.retrieval.base import RetrievedHit, Retriever


class BM25Retriever(Retriever):
    """Retrieve chunks using Weaviate BM25 over the indexed text field."""

    name = "bm25"

    def search(self, query: str, top_k: int) -> list[RetrievedHit]:
        """Return top-k BM25 hits for a query."""
        result = self.collection.query.bm25(
            query=query, limit=top_k, 
            return_metadata=MetadataQuery(score=True, explain_score=True))

        return self.objects_to_hits(result.objects)
