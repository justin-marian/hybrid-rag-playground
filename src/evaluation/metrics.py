"""Document-level IR metrics for BEIR retrieval evaluation."""

from __future__ import annotations

import math
from collections.abc import Iterable


def positive_doc_ids(relevant_docs: dict[str, int]) -> set[str]:
    """Return document IDs with positive relevance."""
    return {doc_id for doc_id, relevance in relevant_docs.items() if relevance > 0}


def collapse_chunks_to_docs(ranked_chunk_doc_ids: Iterable[str]) -> list[str]:
    """Collapse chunk-level results to a deduplicated document-level ranking."""
    seen: set[str] = set()
    ranked_docs: list[str] = []

    for doc_id in ranked_chunk_doc_ids:
        if doc_id in seen:
            continue
        seen.add(doc_id)
        ranked_docs.append(doc_id)

    return ranked_docs


def recall_at_k(ranked_docs: list[str], relevant_docs: dict[str, int], k: int) -> float:
    """Return the fraction of positive relevant documents retrieved in top-k."""
    if relevant := positive_doc_ids(relevant_docs):
        return len(set(ranked_docs[:k]) & relevant) / len(relevant)
    else:
        return 0.0


def reciprocal_rank(ranked_docs: list[str], relevant_docs: dict[str, int]) -> float:
    """Return reciprocal rank of the first positive relevant document."""
    if relevant := positive_doc_ids(relevant_docs):
        return next((1.0 / rank for rank, doc_id in enumerate(ranked_docs, start=1) if doc_id in relevant), 0.0)
    else:
        return 0.0


def dcg(gains: Iterable[float]) -> float:
    """Return discounted cumulative gain with log2 discount."""
    return sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))


def ndcg_at_k(ranked_docs: list[str], relevant_docs: dict[str, int], k: int) -> float:
    """Return normalized DCG@k using graded relevance labels."""
    gains = [float(relevant_docs.get(doc_id, 0)) for doc_id in ranked_docs[:k]]
    ideal_gains = sorted((gain for gain in relevant_docs.values() if gain > 0), reverse=True)[:k]
    idcg = dcg(float(gain) for gain in ideal_gains)
    return 0.0 if idcg == 0.0 else dcg(gains) / idcg


def mean(values: list[float]) -> float:
    """Return the arithmetic mean, or 0.0 for an empty list."""
    return sum(values) / len(values) if values else 0.0
