"""Run a retriever over BEIR queries and compute aggregate IR metrics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from tqdm import tqdm

from src.evaluation.metrics import collapse_chunks_to_docs, mean, ndcg_at_k, recall_at_k, reciprocal_rank
from src.retrieval.base import Retriever
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvalResult:
    """Aggregate retrieval metrics for one retriever and one dataset."""

    retriever: str
    dataset: str
    num_queries: int
    recall_at_10: float
    mrr: float
    ndcg_at_10: float

    def as_row(self) -> dict[str, float | int | str]:
        """Return a compact table row with rounded metrics."""
        return {
            "retriever": self.retriever, "dataset": self.dataset, "num_queries": self.num_queries, 
            "recall@10": round(self.recall_at_10, 4), "ndcg@10": round(self.ndcg_at_10, 4), "mrr": round(self.mrr, 4)}


def valid_query_ids(queries: dict[str, str], qrels: dict[str, dict[str, int]], query_ids: Iterable[str] | None = None) -> list[str]:
    """Return query IDs that exist in both queries and qrels."""
    if query_ids is None:
        return [qid for qid in queries if qid in qrels]
    return [qid for qid in query_ids if qid in queries and qid in qrels]


def evaluate_retriever(
    retriever: Retriever, queries: dict[str, str],
    qrels: dict[str, dict[str, int]], dataset_name: str,
    top_k: int = 10, query_ids: Iterable[str] | None = None) -> EvalResult:
    """Run a retriever over queries and compute mean Recall@10, MRR, and nDCG@10."""
    selected_query_ids = valid_query_ids(queries, qrels, query_ids)
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcgs: list[float] = []

    for qid in tqdm(selected_query_ids, desc=f"Eval {retriever.name} on {dataset_name}"):
        relevant = qrels.get(qid, {})
        if not relevant:
            continue

        hits = retriever.search(queries[qid], top_k=top_k)
        ranked_doc_ids = collapse_chunks_to_docs(hit.doc_id for hit in hits)
        recalls.append(recall_at_k(ranked_doc_ids, relevant, k=10))
        reciprocal_ranks.append(reciprocal_rank(ranked_doc_ids, relevant))
        ndcgs.append(ndcg_at_k(ranked_doc_ids, relevant, k=10))

    result = EvalResult(
        retriever=retriever.name, dataset=dataset_name,
        num_queries=len(recalls), recall_at_10=mean(recalls),
        mrr=mean(reciprocal_ranks), ndcg_at_10=mean(ndcgs))
    logger.info(
        "[%s/%s] Recall@10=%.4f  MRR=%.4f  nDCG@10=%.4f  (n=%d)",
        retriever.name, dataset_name, result.recall_at_10, result.mrr,
        result.ndcg_at_10, result.num_queries)
    return result
