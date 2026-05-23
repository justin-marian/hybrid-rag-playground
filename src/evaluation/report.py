"""Generate an evaluation report for Hybrid RAG experiments.

Reads retrieval metrics, calibration sweeps, and RAG demo traces, then writes a
human-readable Markdown report.

Run from the repository root:
    python -m src.evaluation.report
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import path_or_default, read_csv_if_exists, read_json_if_exists
from src.utils.logging import get_logger
from src.utils.paths import DOCS_DIR, RESULTS_DIR

logger = get_logger(__name__)

DEFAULT_RETRIEVAL_CSV = RESULTS_DIR / "retrieval_metrics.csv"
DEFAULT_SWEEP_CSV = RESULTS_DIR / "sweep_results.csv"
DEFAULT_RAG_JSON = RESULTS_DIR / "rag" / "rag_demo.json"
DEFAULT_SUMMARY_CSV = RESULTS_DIR / "evaluation_report.csv"

# Final Calibration Report for Hyperparameters in IR (Index Retrieval)
DEFAULT_REPORT_MD = DOCS_DIR / "EVALUATION_REPORT.md"

METRIC_COLUMNS = ("recall@10", "mrr", "ndcg@10")


@dataclass(frozen=True)
class ReportPaths:
    """Resolved input and output paths used by the report generator."""

    retrieval_csv: Path
    sweep_csv: Path
    rag_json: Path
    report_md: Path
    summary_csv: Path


def normalize_metric_columns(df: pd.DataFrame) -> list[str]:
    """Convert available metric columns to numeric values."""
    columns = [column for column in METRIC_COLUMNS if column in df.columns]
    for column in columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return columns


def metric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Average metrics by retriever."""
    if df.empty or "retriever" not in df.columns:
        return pd.DataFrame()

    work = df.copy()
    if metrics := normalize_metric_columns(work):
        return (work.groupby("retriever", dropna=False)[metrics]
                .mean().reset_index().sort_values(metrics[-1], ascending=False))
    else:
        return pd.DataFrame()


def best_rows(df: pd.DataFrame, metric: str = "ndcg@10") -> pd.DataFrame:
    """Best row per dataset according to the selected metric."""
    if df.empty or "dataset" not in df.columns or metric not in df.columns:
        return pd.DataFrame()

    work = df.copy()
    work[metric] = pd.to_numeric(work[metric], errors="coerce")
    work = work.dropna(subset=[metric])
    if work.empty:
        return pd.DataFrame()

    idx = work.groupby("dataset", sort=True)[metric].idxmax()
    return work.loc[idx].sort_values(["dataset", metric], ascending=[True, False])


def sweep_summary(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Top sweep rows sorted by the strongest available metric."""
    if df.empty:
        return pd.DataFrame()

    work = df.copy()
    metrics = normalize_metric_columns(work)
    sort_col = "ndcg@10" if "ndcg@10" in metrics else (metrics[-1] if metrics else None)
    if sort_col is None:
        return work.head(limit)

    return work.sort_values(sort_col, ascending=False).head(limit)


def normalize_rag_records(raw: Any) -> list[dict[str, Any]]:
    """Normalize the RAG JSON artifact into a list of dictionaries."""
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        for key in ("records", "results", "answers", "items"):
            value = raw.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [raw]
    return []


def rag_summary(records: list[dict[str, Any]], max_examples: int = 5) -> pd.DataFrame:
    """Compact summary of saved RAG traces."""
    rows: list[dict[str, Any]] = []

    for record in records[:max_examples]:
        hits = record.get("hits") or record.get("chunks") or []
        answer = str(record.get("answer", "")).replace("\n", " ").strip()
        prompt = str(record.get("prompt", "")).replace("\n", " ").strip()
        rows.append({
            "query_id": record.get("query_id", ""),
            "dataset": record.get("dataset", ""),
            "retriever": record.get("retriever", ""),
            "top_k": record.get("top_k", ""),
            "num_hits": len(hits) if isinstance(hits, list) else "",
            "answer_preview": answer[:180] + ("..." if len(answer) > 180 else ""),
            "prompt_chars": len(prompt)
        })

    return pd.DataFrame(rows)


def dataframe_to_markdown(df: pd.DataFrame, floatfmt: str = ".4f") -> str:
    """Render a DataFrame as Markdown or return a clear placeholder."""
    if df.empty:
        return "_No data available._"
    return df.to_markdown(index=False, floatfmt=floatfmt)


def write_summary_csv(summary: pd.DataFrame, path: Path) -> Path | None:
    """Write retriever-level summary metrics when available."""
    if summary.empty:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(path, index=False)
    logger.info("Wrote summary CSV: %s", path)
    return path


def build_report(
    retrieval_df: pd.DataFrame,
    sweep_df: pd.DataFrame,
    rag_records: list[dict[str, Any]],
    paths: ReportPaths) -> str:
    """Build the Markdown report body."""
    sections = [
        ("Retrieval summary", "Average retrieval metrics by retriever. Higher values are better.", metric_summary(retrieval_df)),
        ("Best retriever per dataset", "Best rows are selected by `ndcg@10`, because it captures top-rank quality.", best_rows(retrieval_df)),
        ("Calibration highlights", "Top sweep rows sorted by the strongest available ranking metric.", sweep_summary(sweep_df)),
        ("RAG trace samples", "Compact view of saved RAG demo traces. Use the JSON artifact for full details.", rag_summary(rag_records))]

    body = [
        "# Hybrid RAG Evaluation Report",
        "",
        "This report summarizes retrieval quality, calibration behavior, and sample RAG traces generated by the local evaluation pipeline.",
        "",
        "## Input artifacts",
        "",
        f"- Retrieval metrics: `{paths.retrieval_csv}`",
        f"- Sweep results: `{paths.sweep_csv}`",
        f"- RAG demo traces: `{paths.rag_json}`"]

    for title, description, dataframe in sections:
        body.extend(["", f"## {title}", "", description, "", dataframe_to_markdown(dataframe)])

    body.extend([
        "",
        "## How to read this report",
        "",
        "- Start with retrieval metrics before judging generated answers.",
        "- Low Recall@10 means relevant documents are missing.",
        "- Low MRR means useful evidence appears too late.",
        "- Low nDCG@10 means ranking quality needs tuning.",
        "- Unsupported RAG answers require prompt and chunk inspection."])

    return "\n".join(body)


def generate_report(paths: ReportPaths) -> Path:
    """Read artifacts, generate Markdown, and write outputs."""
    retrieval_df = read_csv_if_exists(paths.retrieval_csv)
    sweep_df = read_csv_if_exists(paths.sweep_csv)
    rag_records = normalize_rag_records(read_json_if_exists(paths.rag_json))

    write_summary_csv(metric_summary(retrieval_df), paths.summary_csv)

    report = build_report(retrieval_df, sweep_df, rag_records, paths)
    paths.report_md.parent.mkdir(parents=True, exist_ok=True)
    paths.report_md.write_text(report, encoding="utf-8")
    logger.info("Wrote evaluation report: %s", paths.report_md)
    return paths.report_md


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate a Hybrid RAG evaluation report.")
    parser.add_argument("--retrieval-csv", default=None, help="Path to retrieval_metrics.csv.")
    parser.add_argument("--sweep-csv", default=None, help="Path to sweep_results.csv.")
    parser.add_argument("--rag-json", default=None, help="Path to rag_demo.json.")
    parser.add_argument("--out", default=None, help="Output Markdown report path.")
    parser.add_argument("--summary-csv", default=None, help="Output summary CSV path.")
    return parser.parse_args()


def main():
    """CLI entry point."""
    args = parse_args()
    paths = ReportPaths(
        retrieval_csv=path_or_default(args.retrieval_csv, DEFAULT_RETRIEVAL_CSV),
        sweep_csv=path_or_default(args.sweep_csv, DEFAULT_SWEEP_CSV),
        rag_json=path_or_default(args.rag_json, DEFAULT_RAG_JSON),
        report_md=path_or_default(args.out, DEFAULT_REPORT_MD),
        summary_csv=path_or_default(args.summary_csv, DEFAULT_SUMMARY_CSV))
    generate_report(paths)


if __name__ == "__main__":
    main()
