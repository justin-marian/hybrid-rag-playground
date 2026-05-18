"""Build comparative retrieval tables for retriever and dataset metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.evaluation.evaluator import EvalResult
from src.utils.logging import get_logger
from src.utils.paths import resolve

logger = get_logger(__name__)


METRIC_COLUMNS = ["recall@10", "mrr", "ndcg@10"]
EMBEDDING_METHOD = ["bm25", "dense", "hybrid"]


def results_to_long_df(results: list[EvalResult]) -> pd.DataFrame:
    """Convert evaluation results into a long-format DataFrame."""
    return pd.DataFrame([result.as_row() for result in results])


def ordered_datasets(long_df: pd.DataFrame) -> list[str]:
    """Return deterministic dataset order for table columns."""
    return sorted(str(dataset) for dataset in long_df["dataset"].dropna().unique())


def ordered_retrievers(long_df: pd.DataFrame) -> list[str]:
    """Return deterministic retriever order while keeping known retrievers first."""
    present = [str(retriever) for retriever in long_df["retriever"].dropna().unique()]
    ordered = [retriever for retriever in EMBEDDING_METHOD if retriever in present]
    ordered.extend(sorted(retriever for retriever in present if retriever not in EMBEDDING_METHOD))
    return ordered


def results_to_wide_df(results: list[EvalResult]) -> pd.DataFrame:
    """Pivot results into a flat, GitHub-friendly comparison table."""
    long_df = results_to_long_df(results)
    if long_df.empty:
        return pd.DataFrame()

    rows: list[dict[str, float | str]] = []
    datasets = ordered_datasets(long_df)

    for retriever in ordered_retrievers(long_df):
        row: dict[str, float | str] = {"retriever": retriever}
        retriever_df = long_df[long_df["retriever"] == retriever]

        for dataset in datasets:
            dataset_df = retriever_df[retriever_df["dataset"] == dataset]

            for metric in METRIC_COLUMNS:
                column = f"{dataset}_{metric}"
                row[column] = float("nan") if dataset_df.empty else float(dataset_df.iloc[0][metric])

        rows.append(row)

    return pd.DataFrame(rows)


def write_markdown_table(results: list[EvalResult], md_path: str | Path) -> Path:
    """Write a flat markdown comparison table and return its resolved path."""
    md_p = resolve(md_path)
    md_p.parent.mkdir(parents=True, exist_ok=True)

    wide_df = results_to_wide_df(results)

    with md_p.open("w", encoding="utf-8-sig") as handle:
        handle.write("# Retrieval Comparison\n\n")
        handle.write("Metrics are reported per retriever and dataset. Higher is better for all metrics.\n\n")
        handle.write(wide_df.to_markdown(index=False, floatfmt=".4f"))
        handle.write("\n")

    logger.info("Wrote markdown results table: %s", md_p)
    return md_p


def save_results(
    results: list[EvalResult], csv_path: str | Path,
    md_path: str | Path | None = None,
    wide_csv_path: str | Path | None = None) -> tuple[Path, Path | None]:
    """Save long-format CSV, optional markdown table, and optional flat wide CSV."""
    csv_p = resolve(csv_path)
    csv_p.parent.mkdir(parents=True, exist_ok=True)

    results_to_long_df(results).to_csv(csv_p, index=False)
    logger.info("Wrote long-format results CSV: %s", csv_p)

    if wide_csv_path:
        wide_csv_p = resolve(wide_csv_path)
        wide_csv_p.parent.mkdir(parents=True, exist_ok=True)
        results_to_wide_df(results).to_csv(wide_csv_p, index=False)
        logger.info("Wrote wide-format results CSV: %s", wide_csv_p)

    md_p = write_markdown_table(results, md_path) if md_path else None
    return csv_p, md_p
