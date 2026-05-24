"""Hybrid retrieval via rank-based BM25/vector fusion."""

from __future__ import annotations

from typing import Any

from weaviate.classes.query import MetadataQuery

from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.retrieval.base import RetrievedHit, Retriever

TARGET_VECTOR = "default"


class HybridRetriever(Retriever):
    """Retrieve chunks with weighted reciprocal-rank fusion.

    The retriever combines two independent ranked lists: one from BM25 and one
    from dense vector search. Instead of mixing raw scores, it uses Reciprocal
    Rank Fusion (RRF), which is safer because BM25 scores and dense scores are
    not directly comparable.

    RRF computes a contribution from each ranking position:

        score = weight / (rrf_k + rank)

    A chunk that appears high in both BM25 and dense rankings receives
    contributions from both lists and is promoted in the final ranking.

    The alpha parameter controls the fusion weights:

        BM25 weight  = 1.0 - alpha
        Dense weight = alpha

    Therefore, alpha=0.0 behaves like BM25 retrieval, alpha=1.0 behaves
    like Dense retrieval, and alpha=0.5 gives equal weight to both lists.

    The rrf_k parameter controls how strongly top ranks dominate the fused
    score. A larger value makes rank differences smoother, while a smaller value
    gives more importance to the first few results. The default value 60 is a
    common robust choice.

    The candidate_multiplier parameter controls how many candidates are fetched
    before fusion. For example, with top_k=10 and candidate_multiplier=5, the
    retriever fetches 50 BM25 candidates and 50 dense candidates, fuses them,
    and returns the final top 10. This gives the fusion step enough candidates
    to recover useful results that may not appear in the first top_k positions
    of both individual retrievers.
    """

    name = "hybrid"

    def __init__(self, client: Any, collection_name: str, embedder: MiniLMEmbedder, alpha: float, rrf_k: int = 60, candidate_multiplier: int = 5):
        super().__init__(client, collection_name)

        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be in [0, 1]")
        if rrf_k < 1:
            raise ValueError("rrf_k must be at least 1")
        if candidate_multiplier < 1:
            raise ValueError("candidate_multiplier must be at least 1")

        self.embedder = embedder
        self.alpha = alpha
        self.rrf_k = rrf_k
        self.candidate_multiplier = candidate_multiplier

    def candidate_limit(self, top_k: int) -> int:
        """Return the number of candidates fetched before fusion."""
        return max(top_k, top_k * self.candidate_multiplier)

    def bm25_hits(self, query: str, limit: int) -> list[RetrievedHit]:
        """Return BM25 candidates."""
        result = self.collection.query.bm25(
            query=query, limit=limit,
            return_metadata=MetadataQuery(score=True, explain_score=False))

        return self.objects_to_hits(result.objects)

    def dense_hits(self, query: str, limit: int) -> list[RetrievedHit]:
        """Return dense-vector candidates."""
        qvec = self.embedder.encode_query(query).tolist()
        result = self.collection.query.near_vector(
            near_vector=qvec, target_vector=TARGET_VECTOR,
            limit=limit, return_metadata=MetadataQuery(distance=True))

        return self.objects_to_hits(result.objects)

    @staticmethod
    def hit_key(hit: RetrievedHit) -> str:
        """Return a stable key for one retrieved chunk."""
        return hit.chunk_id or f"{hit.doc_id}:{hit.rank}:{hit.title}"

    def rrf_score(self, rank: int, weight: float) -> float:
        """Return the weighted reciprocal-rank contribution."""
        return weight / float(self.rrf_k + rank)

    def add_hits(self, hits: list[RetrievedHit], weight: float, scores: dict[str, float], objects: dict[str, RetrievedHit]):
        """Add one ranked list to the fused score dictionaries."""
        for rank, hit in enumerate(hits, start=1):
            key = self.hit_key(hit)
            scores[key] = scores.get(key, 0.0) + self.rrf_score(rank, weight)
            objects.setdefault(key, hit)

    def fused_hits(self, bm25_hits: list[RetrievedHit], dense_hits: list[RetrievedHit], top_k: int) -> list[RetrievedHit]:
        """Fuse BM25 and dense hits into one ranked result list."""
        scores: dict[str, float] = {}
        objects: dict[str, RetrievedHit] = {}

        self.add_hits(bm25_hits, 1.0 - self.alpha, scores, objects)
        self.add_hits(dense_hits, self.alpha, scores, objects)

        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        return [RetrievedHit(
            chunk_id=objects[key].chunk_id, doc_id=objects[key].doc_id,
            title=objects[key].title, text=objects[key].text,
            score=score, rank=rank)
        for rank, (key, score) in enumerate(ordered[:top_k], start=1)]

    def search(self, query: str, top_k: int) -> list[RetrievedHit]:
        """Return top-k hybrid hits using BM25 and dense RRF fusion."""
        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        limit = self.candidate_limit(top_k)
        bm25 = self.bm25_hits(query, limit)
        dense = self.dense_hits(query, limit)

        return [] if not bm25 and not dense else self.fused_hits(bm25, dense, top_k)
