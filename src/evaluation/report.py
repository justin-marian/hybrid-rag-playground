"""Generate an evaluation report for Hybrid RAG experiments.

Reads retrieval metrics, calibration sweeps, RAG demo traces, and configuration
files, then writes a human-readable Markdown report that explicitly documents
the hyperparameters used to obtain the results.

Run from the repository root:
    python -m src.evaluation.report
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import (
    path_or_default,
    read_csv_if_exists,
    read_json_if_exists,
    read_yaml_if_exists,
)
from src.utils.logging import get_logger
from src.utils.paths import DOCS_DIR, RESULTS_DIR, ROOT

logger = get_logger(__name__)

DEFAULT_RETRIEVAL_CSV = RESULTS_DIR / "retrieval_metrics.csv"
DEFAULT_SWEEP_CSV = RESULTS_DIR / "sweep_results.csv"
DEFAULT_RAG_JSON = RESULTS_DIR / "rag" / "rag_demo.json"
DEFAULT_SUMMARY_CSV = RESULTS_DIR / "evaluation_report.csv"

DEFAULT_RETRIEVAL_CONFIG = ROOT / "configs" / "retrieval.yaml"
DEFAULT_RAG_CONFIG = ROOT / "configs" / "rag.yaml"
DEFAULT_DATASETS_CONFIG = ROOT / "configs" / "datasets.yaml"
DEFAULT_AUTO_RESEARCH_CONFIG = ROOT / "configs" / "auto_research.yml"

DEFAULT_REPORT_MD = DOCS_DIR / "EVALUATION_REPORT.md"

METRIC_COLUMNS = ("recall@10", "mrr", "ndcg@10")

RESULT_PARAMETER_COLUMNS = (
    "dataset", "retriever", "top_k", "alpha", "hybrid_alpha",
    "embedding_model", "target_vector", "chunk_size", "chunk_overlap",
    "max_chunk_chars", "bm25_k1", "bm25_b", "split", "num_queries"
)

CONFIG_PARAMETER_PATHS = (
    ("embedding.model_name", "Embedding model used by dense and hybrid retrieval."),
    ("retrieval.top_k", "Number of retrieved chunks/documents evaluated per query."),
    ("retrieval.hybrid_alpha", "Hybrid retrieval blend weight."),
    ("retrieval.target_vector", "Weaviate target vector name."),
    ("retrieval.bm25.k1", "BM25 term-frequency saturation parameter."),
    ("retrieval.bm25.b", "BM25 document-length normalization parameter."),
    ("chunking.chunk_size", "Maximum chunk size used before indexing."),
    ("chunking.chunk_overlap", "Overlap between consecutive chunks."),
    ("rag.dataset", "Default dataset used by the RAG pipeline."),
    ("rag.retriever", "Default retriever used by the RAG pipeline."),
    ("rag.top_k", "Default number of hits used by generation."),
    ("rag.max_chunk_chars", "Maximum characters copied from each retrieved chunk into the prompt."),
    ("llm.provider", "LLM provider used for generation."),
    ("llm.model", "LLM model used for generation."),
    ("llm.host", "LLM host endpoint.")
)


@dataclass(frozen=True)
class ReportPaths:
    """Resolved input and output paths used by the report generator."""

    summary_csv: Path
    retrieval_csv: Path
    sweep_csv: Path

    rag_json: Path

    report_md: Path

    retrieval_config: Path
    rag_config: Path
    datasets_config: Path
    auto_research_config: Path


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


def nested_get(data: dict[str, Any], dotted_path: str) -> Any:
    """Return a nested value from a dictionary using a dotted path."""
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def config_hyperparameters(paths: ReportPaths) -> pd.DataFrame:
    """Build a table with the hyperparameter names and values found in configs."""
    config_files = {
        "retrieval.yaml": read_yaml_if_exists(paths.retrieval_config),
        "rag.yaml": read_yaml_if_exists(paths.rag_config),
        "datasets.yaml": read_yaml_if_exists(paths.datasets_config),
        "auto_research.yml": read_yaml_if_exists(paths.auto_research_config)
    }

    rows: list[dict[str, Any]] = []
    for source, config in config_files.items():
        if not config:
            rows.append({
                "source": source, "hyperparameter": "_file_", "value": "not found",
                "meaning": "Configuration file was not available when the report was generated."})
            continue

        for dotted_path, meaning in CONFIG_PARAMETER_PATHS:
            value = nested_get(config, dotted_path)
            if value is not None:
                rows.append({"source": source, "hyperparameter": dotted_path, "value": value, "meaning": meaning})

    return pd.DataFrame(rows)


def observed_result_parameters(retrieval_df: pd.DataFrame, sweep_df: pd.DataFrame) -> pd.DataFrame:
    """Return the hyperparameter columns that are recorded in result artifacts."""
    rows: list[dict[str, Any]] = []
    for artifact_name, dataframe in (("retrieval_metrics.csv", retrieval_df), ("sweep_results.csv", sweep_df)):
        if dataframe.empty:
            rows.append({
                "artifact": artifact_name,
                "recorded_hyperparameters": "none",
                "missing_recommended_hyperparameters": ", ".join(RESULT_PARAMETER_COLUMNS)
            })
            continue

        recorded = [column for column in RESULT_PARAMETER_COLUMNS if column in dataframe.columns]
        missing = [column for column in RESULT_PARAMETER_COLUMNS if column not in dataframe.columns]
        rows.append({
            "artifact": artifact_name,
            "recorded_hyperparameters": ", ".join(recorded) if recorded else "none",
            "missing_recommended_hyperparameters": ", ".join(missing) if missing else "none"
        })

    return pd.DataFrame(rows)


def result_runs_with_hyperparameters(retrieval_df: pd.DataFrame, sweep_df: pd.DataFrame) -> pd.DataFrame:
    """Create a run-level table that keeps metrics together with hyperparameter columns."""
    source_df = retrieval_df if sweep_df.empty else sweep_df
    if source_df.empty:
        return pd.DataFrame()

    columns = [column for column in RESULT_PARAMETER_COLUMNS if column in source_df.columns]
    columns += [column for column in METRIC_COLUMNS if column in source_df.columns]
    return source_df[columns].copy() if columns else pd.DataFrame()


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
            "alpha": record.get("alpha", ""),
            "model": record.get("model", ""),
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


def build_report(retrieval_df: pd.DataFrame, sweep_df: pd.DataFrame, rag_records: list[dict[str, Any]], paths: ReportPaths) -> str:
    """Build the Markdown report body."""
    sections = [
        ("Hyperparameters from configuration files", "Configured hyperparameter names and values available when the report was generated.", config_hyperparameters(paths)),
        ("Hyperparameters recorded in result artifacts", "Which hyperparameter columns are stored together with the metrics.", observed_result_parameters(retrieval_df, sweep_df)),
        ("Run-level results with recorded hyperparameters", "Available hyperparameters shown next to the reported metrics.", result_runs_with_hyperparameters(retrieval_df, sweep_df)),
        ("Retrieval summary", "Average retrieval metrics by retriever. Higher values are better.", metric_summary(retrieval_df)),
        ("Best retriever per dataset", "Best rows are selected by `ndcg@10`, because it captures top-rank quality.", best_rows(retrieval_df)),
        ("Calibration highlights", "Top sweep rows sorted by the strongest available ranking metric.", sweep_summary(sweep_df)),
        ("RAG trace samples", "Compact view of saved RAG demo traces. Use the JSON artifact for full details.", rag_summary(rag_records))
    ]

    body = [
        "# Hybrid RAG Evaluation Report", "",
        "This report summarizes retrieval quality, calibration behavior, sample RAG traces, and the hyperparameters used to obtain the results.", "",
        "## Input artifacts", "",
        f"- Retrieval metrics: `{paths.retrieval_csv}`",
        f"- Sweep results: `{paths.sweep_csv}`",
        f"- RAG demo traces: `{paths.rag_json}`",
        f"- Retrieval config: `{paths.retrieval_config}`",
        f"- RAG config: `{paths.rag_config}`",
        f"- Dataset config: `{paths.datasets_config}`",
        f"- Auto research config: `{paths.auto_research_config}`"
    ]

    for title, description, dataframe in sections:
        body.extend(["", f"## {title}", "", description, "", dataframe_to_markdown(dataframe)])

    body.extend([
        "", "## Recommended hyperparameters to store in every experiment CSV", "",
        "- `dataset`: BEIR dataset key, for example `nfcorpus`, `scifact`, or `fiqa`.",
        "- `retriever`: retrieval mode, for example `bm25`, `dense`, or `hybrid`.",
        "- `top_k`: number of retrieved candidates used for evaluation.",
        "- `alpha` or `hybrid_alpha`: dense/sparse interpolation weight used by hybrid retrieval.",
        "- `embedding_model`: sentence-transformer or embedding model used by dense retrieval.",
        "- `target_vector`: Weaviate target vector name.",
        "- `chunk_size` and `chunk_overlap`: chunking parameters used before indexing.",
        "- `bm25_k1` and `bm25_b`: BM25 scoring parameters, if customized.",
        "- `split`: dataset split evaluated.",
        "- `num_queries`: number of evaluated queries.",
        "", "## How to read this report", "",
        "- Start with retrieval metrics before judging generated answers.",
        "- Low Recall@10 means relevant documents are missing.",
        "- Low MRR means useful evidence appears too late.",
        "- Low nDCG@10 means ranking quality needs tuning.",
        "- If a hyperparameter is listed as missing, the current result artifact did not record it and the value must be taken from the config files or experiment command.",
    ])

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
    parser.add_argument("--retrieval-config", default=None, help="Path to retrieval.yaml.")
    parser.add_argument("--rag-config", default=None, help="Path to rag.yaml.")
    parser.add_argument("--datasets-config", default=None, help="Path to datasets.yaml.")
    parser.add_argument("--auto-research-config", default=None, help="Path to auto_research.yml.")
    return parser.parse_args()


def main():
    """CLI entry point."""
    args = parse_args()
    paths = ReportPaths(
        retrieval_csv=path_or_default(args.retrieval_csv, DEFAULT_RETRIEVAL_CSV),
        sweep_csv=path_or_default(args.sweep_csv, DEFAULT_SWEEP_CSV),
        rag_json=path_or_default(args.rag_json, DEFAULT_RAG_JSON),
        report_md=path_or_default(args.out, DEFAULT_REPORT_MD),
        summary_csv=path_or_default(args.summary_csv, DEFAULT_SUMMARY_CSV),
        retrieval_config=path_or_default(args.retrieval_config, DEFAULT_RETRIEVAL_CONFIG),
        rag_config=path_or_default(args.rag_config, DEFAULT_RAG_CONFIG),
        datasets_config=path_or_default(args.datasets_config, DEFAULT_DATASETS_CONFIG),
        auto_research_config=path_or_default(args.auto_research_config, DEFAULT_AUTO_RESEARCH_CONFIG))
    generate_report(paths)


if __name__ == "__main__":
    main()
