"""Build comparative retrieval tables for retriever and dataset metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.evaluation.evaluator import EvalResult
from src.utils.logging import get_logger
from src.utils.paths import resolve

logger = get_logger(__name__)


METRIC_COLUMNS = ["recall@10", "mrr", "ndcg@10"]


def results_to_long_df(results: list[EvalResult]) -> pd.DataFrame:
    """Convert evaluation results into a long-format DataFrame."""
    return pd.DataFrame([result.as_row() for result in results])


def ordered_datasets(long_df: pd.DataFrame) -> list[str]:
    """Return deterministic dataset order for table columns."""
    return sorted(str(dataset) for dataset in long_df["dataset"].dropna().unique())


def results_to_wide_df(results: list[EvalResult]) -> pd.DataFrame:
    """Pivot results into rows by retriever and columns by dataset and metric."""
    long_df = results_to_long_df(results)
    if long_df.empty:
        return pd.DataFrame()

    pivoted = long_df.pivot_table(index="retriever", columns="dataset", values=METRIC_COLUMNS)
    pivoted = pivoted.swaplevel(axis=1).sort_index(axis=1, level=0)

    columns = pd.MultiIndex.from_product([ordered_datasets(long_df), METRIC_COLUMNS], names=["dataset", "metric"])
    return pivoted.reindex(columns=columns)


def write_markdown_table(results: list[EvalResult], md_path: str | Path) -> Path:
    """Write the wide-format markdown table and return its resolved path."""
    md_p = resolve(md_path)
    md_p.parent.mkdir(parents=True, exist_ok=True)

    with md_p.open("w", encoding=" utf-8-sig") as handle:
        handle.write("# Retrieval Comparison: Recall@10, MRR, nDCG@10\n\n")
        handle.write(results_to_wide_df(results).to_markdown(floatfmt=".4f"))
        handle.write("\n")

    logger.info("Wrote markdown results table: %s", md_p)
    return md_p


def save_results(
    results: list[EvalResult], csv_path: str | Path,
    md_path: str | Path | None = None) -> tuple[Path, Path | None]:
    """Save long-format CSV and optionally a wide-format markdown table."""
    csv_p = resolve(csv_path)
    csv_p.parent.mkdir(parents=True, exist_ok=True)

    results_to_long_df(results).to_csv(csv_p, index=False)
    logger.info("Wrote long-format results CSV: %s", csv_p)

    md_p = write_markdown_table(results, md_path) if md_path else None
    return csv_p, md_p
