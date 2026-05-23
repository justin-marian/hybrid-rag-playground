"""Hyperparameter testing XAI for RAG calibration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, cast

import click
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes

from src.chunking.adaptive_chunker import AdaptiveDocChunker
from src.data.beir_loader import load_beir
from src.data.dataset_registry import get_spec
from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.evaluation.evaluator import evaluate_retriever
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.utils.io import load_yaml
from src.utils.logging import get_logger
from src.utils.paths import IMAGES_DIR, RESULTS_DIR, ensure_dirs, resolve
from src.weaviate_io.client import weaviate_client
from src.weaviate_io.indexer import index_chunks
from src.weaviate_io.schema import collection_name, ensure_collection

logger = get_logger(__name__)

TestingAxis = Literal["alpha", "top_k", "chunk_size"]
SWEEP_AXES: tuple[TestingAxis, ...] = ("alpha", "top_k", "chunk_size")


@dataclass(frozen=True)
class TestingConfig:
    """Default configuration shared by axis-aligned test_calibration runs."""

    chunk_size: int
    top_k: int
    alpha: float


@dataclass(frozen=True)
class WeaviateSettings:
    """Weaviate connection and indexing settings."""

    host: str
    http_port: int
    grpc_port: int
    prefix: str
    distance: str
    batch_size: int


@dataclass(frozen=True)
class ChunkingSettings:
    """Chunking settings used during re-indexing."""

    overlap_ratio: float
    tokenizer_name: str | None


@dataclass
class TestingRow:
    """One test calibration evaluation result."""

    axis: str
    value: float
    chunk_size: int
    top_k: int
    alpha: float
    retriever: str
    dataset: str
    recall_at_10: float
    mrr: float
    ndcg_at_10: float

    def as_dict(self) -> dict[str, str | float | int]:
        """Return a serializable row dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class TestingArgs:
    """Parsed CLI arguments for one test calibration run."""

    retrieval_config: str
    test_calibration_config: str
    datasets_config: str
    dataset: str | None
    skip_alpha: bool
    skip_top_k: bool
    skip_chunk: bool


def read_defaults(cfg: dict[str, Any]) -> TestingConfig:
    """Read test_calibration defaults from config."""
    values = cfg["defaults"]
    return TestingConfig(chunk_size=int(values["chunk_size"]), top_k=int(values["top_k"]), alpha=float(values["hybrid_alpha"]))


def read_weaviate_settings(cfg: dict[str, Any]) -> WeaviateSettings:
    """Read Weaviate settings from retrieval config."""
    values = cfg["weaviate"]
    return WeaviateSettings(
        host=values["host"], http_port=int(values["http_port"]),
        grpc_port=int(values["grpc_port"]), prefix=values["collection_prefix"],
        distance=values["distance"], batch_size=int(values["batch_size"]))


def read_chunking_settings(cfg: dict[str, Any]) -> ChunkingSettings:
    """Read chunking settings from retrieval config."""
    values = cfg["chunking"]
    return ChunkingSettings(overlap_ratio=float(values["overlap_ratio"]), tokenizer_name=values.get("tokenizer"))


def build_embedder(cfg: dict[str, Any]) -> MiniLMEmbedder:
    """Create the MiniLM embedder from retrieval config."""
    values = cfg["embedding"]
    return MiniLMEmbedder(model_name=values["model_name"], batch_size=int(values["batch_size"]), normalize=bool(values["normalize"]), cache_dir=values["cache_dir"])


def build_retriever(
        name: str, client: Any, coll: str, embedder: MiniLMEmbedder,
        alpha: float):
    """Create one retriever instance by name."""
    if name == "bm25":
        return BM25Retriever(client, coll)
    if name == "dense":
        return DenseRetriever(client, coll, embedder)
    if name == "hybrid":
        return HybridRetriever(client, coll, embedder, alpha=alpha)
    raise ValueError(f"Unknown retriever: {name}")


def eval_one(
        client: Any, coll: str, beir: Any, embedder: MiniLMEmbedder,
        top_k: int, alpha: float, retriever_name: str) -> tuple[float, float, float]:
    """Evaluate one retriever configuration and return aggregate metrics."""
    retriever = build_retriever(retriever_name, client, coll, embedder, alpha)
    result = evaluate_retriever(retriever=retriever, queries=beir.queries, qrels=beir.qrels, dataset_name=beir.spec.name, top_k=top_k)
    return result.recall_at_10, result.mrr, result.ndcg_at_10


def reindex_collection(
        client: Any, coll: str, beir: Any, 
        chunk_size: int, chunking: ChunkingSettings,
        embedder: MiniLMEmbedder, settings: WeaviateSettings):
    """Drop and rebuild the collection with the requested chunk size."""
    chunker = AdaptiveDocChunker(chunk_size_tokens=chunk_size, overlap_ratio=chunking.overlap_ratio, tokenizer_name=chunking.tokenizer_name)
    ensure_collection(client, coll, distance=settings.distance, recreate=True)
    chunks = list(chunker.chunk_corpus(beir.corpus, dataset=beir.spec.name))
    logger.info("Re-indexed with chunk_size=%d -> %d chunks.", chunk_size, len(chunks))
    index_chunks(client, coll, chunks, embedder=embedder, batch_size=settings.batch_size)


def append_eval_row(
        rows: list[TestingRow], axis: str, value: float, 
        chunk_size: int, top_k: int, alpha: float, 
        dataset: str, metrics: tuple[float, float, float]):
    """Append one hybrid test calibration result row."""
    recall, mrr, ndcg = metrics
    rows.append(TestingRow(
        axis=axis, value=value, 
        chunk_size=chunk_size, top_k=top_k, alpha=alpha, 
        retriever="hybrid", dataset=dataset,
        recall_at_10=recall, mrr=mrr, ndcg_at_10=ndcg))


def test_calibration_alpha(
        client: Any, coll: str, beir: Any, embedder: MiniLMEmbedder,
        defaults: TestingConfig, values: list[float]) -> list[TestingRow]:
    """Run alpha test calibration with fixed chunk size and top-k."""
    logger.info("=== Testing axis: alpha (chunk_size=%d, top_k=%d) ===", defaults.chunk_size, defaults.top_k)
    rows: list[TestingRow] = []
    for alpha in values:
        metrics = eval_one(client, coll, beir, embedder, defaults.top_k, float(alpha), "hybrid")
        append_eval_row(rows, "alpha", float(alpha), defaults.chunk_size, defaults.top_k, float(alpha), beir.spec.name, metrics)
    return rows


def test_calibration_top_k(
        client: Any, coll: str, beir: Any, embedder: MiniLMEmbedder,
        defaults: TestingConfig, values: list[int]) -> list[TestingRow]:
    """Run top-k test calibration with fixed chunk size and alpha."""
    logger.info("=== Testing axis: top_k (chunk_size=%d, alpha=%.2f) ===", defaults.chunk_size, defaults.alpha)
    rows: list[TestingRow] = []
    for top_k in values:
        metrics = eval_one(client, coll, beir, embedder, int(top_k), defaults.alpha, "hybrid")
        append_eval_row(rows, "top_k", float(top_k), defaults.chunk_size, int(top_k), defaults.alpha, beir.spec.name, metrics)
    return rows


def test_calibration_chunk_size(
        client: Any, coll: str, beir: Any, embedder: MiniLMEmbedder,
        defaults: TestingConfig, values: list[int], chunking: ChunkingSettings,
        settings: WeaviateSettings) -> list[TestingRow]:
    """Run chunk-size test calibration, re-indexing once per chunk size."""
    logger.info("=== Testing axis: chunk_size (alpha=%.2f, top_k=%d) - RE-INDEXING ===", defaults.alpha, defaults.top_k)
    rows: list[TestingRow] = []
    for chunk_size in values:
        reindex_collection(client, coll, beir, int(chunk_size), chunking, embedder, settings)
        metrics = eval_one(client, coll, beir, embedder, defaults.top_k, defaults.alpha, "hybrid")
        append_eval_row(rows, "chunk_size", float(chunk_size), int(chunk_size), defaults.top_k, defaults.alpha, beir.spec.name, metrics)
    return rows


def plot_axis(ax: Axes, df: pd.DataFrame, axis_name: TestingAxis):
    """Plot one nDCG@10 test calibration axis with seaborn."""
    required_cols = {"axis", "value", "ndcg_at_10"}
    if missing_cols := required_cols.difference(df.columns):
        raise ValueError(f"Missing required columns: {sorted(missing_cols)}")

    sub = df.loc[df["axis"].eq(axis_name)].copy()
    if sub.empty:
        raise ValueError(f"No rows found for axis={axis_name!r}")

    order = sub["value"].astype(float).to_numpy().argsort()
    sub = sub.iloc[order]

    sns.lineplot(data=sub, x="value", y="ndcg_at_10", marker="o", ax=ax)
    ax.set_xlabel(axis_name)
    ax.set_ylabel("nDCG@10")
    ax.set_title(f"nDCG@10 vs {axis_name}")

    for _, row in sub.iterrows():
        ax.annotate(
            f"{float(cast(Any, row['ndcg_at_10'])):.3f}",
            (float(cast(Any, row["value"])), float(cast(Any, row["ndcg_at_10"]))),
            textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)


def plot_test_calibration(df: pd.DataFrame, out_path: str | Path):
    """Save the nDCG@10 calibration plot."""
    if df.empty:
        return

    present_axes = set(df["axis"].dropna().astype(str))
    axes_present: list[TestingAxis] = [axis for axis in SWEEP_AXES if axis in present_axes]
    if not axes_present:
        raise ValueError("No valid test calibration axes found in results.")

    sns.set_theme(context="notebook", style="whitegrid")
    fig, axs = plt.subplots(1, len(axes_present), figsize=(5 * len(axes_present), 4))
    axs_list = [axs] if len(axes_present) == 1 else list(axs)

    for ax, axis_name in zip(axs_list, axes_present, strict=True):
        plot_axis(ax, df, axis_name)

    dataset_name = str(df["dataset"].iloc[0])
    fig.suptitle(f"Testing - dataset={dataset_name}, retriever=hybrid")
    fig.tight_layout()
    fig.savefig(str(out_path))
    plt.close(fig)
    logger.info("Saved test calibration plot: %s", out_path)


def save_results(rows: list[TestingRow], csv_path: str | Path, plot_path: str | Path) -> pd.DataFrame:
    """Save test calibration rows to CSV and plot non-empty results."""
    df = pd.DataFrame([row.as_dict() for row in rows])
    out_csv, out_plot = resolve(csv_path), resolve(plot_path)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    logger.info("Wrote test calibration CSV: %s", out_csv)
    if not df.empty:
        plot_test_calibration(df, out_plot)
    return df


def print_recommendation(df: pd.DataFrame):
    """Print the best observed configuration by nDCG@10."""
    if df.empty:
        return

    order = df["ndcg_at_10"].astype(float).to_numpy().argsort()[::-1]
    best = df.iloc[order[0]]

    print("\n=== Recommended configuration (max nDCG@10) ===")
    print(f"  axis varied:  {cast(Any, best['axis'])!s}")
    print(f"  chunk_size:   {int(cast(Any, best['chunk_size']))}")
    print(f"  top_k:        {int(cast(Any, best['top_k']))}")
    print(f"  hybrid alpha: {float(cast(Any, best['alpha'])):.2f}")
    print(f"  recall@10:    {float(cast(Any, best['recall_at_10'])):.4f}")
    print(f"  mrr:          {float(cast(Any, best['mrr'])):.4f}")
    print(f"  ndcg@10:      {float(cast(Any, best['ndcg_at_10'])):.4f}")


def run_test_calibration(args: TestingArgs):
    """Run calibration test calibration from parsed arguments."""
    retrieval_cfg, test_calibration_cfg = load_yaml(args.retrieval_config), load_yaml(args.test_calibration_config)

    defaults = read_defaults(test_calibration_cfg)
    settings = read_weaviate_settings(retrieval_cfg)
    chunking = read_chunking_settings(retrieval_cfg)

    spec = get_spec(args.dataset or test_calibration_cfg["dataset"], args.datasets_config)
    embedder = build_embedder(retrieval_cfg)
    coll = collection_name(settings.prefix, spec.key)

    rows: list[TestingRow] = []
    ensure_dirs(RESULTS_DIR, IMAGES_DIR)

    with weaviate_client(host=settings.host, http_port=settings.http_port, grpc_port=settings.grpc_port) as client:
        beir = load_beir(spec)
        if not client.collections.exists(coll):
            logger.info("Collection %s missing; building with default chunk size %d.", coll, defaults.chunk_size)
            reindex_collection(client, coll, beir, defaults.chunk_size, chunking, embedder, settings)

        if not args.skip_alpha:
            rows.extend(test_calibration_alpha(
                client, coll, beir, embedder, defaults,
                [float(value) for value in test_calibration_cfg["hybrid_alphas"]]))
        if not args.skip_top_k:
            rows.extend(test_calibration_top_k(
                client, coll, beir, embedder, defaults,
                [int(value) for value in test_calibration_cfg["top_k_values"]]))
        if not args.skip_chunk:
            rows.extend(test_calibration_chunk_size(
                client, coll, beir, embedder, defaults,
                [int(value) for value in test_calibration_cfg["chunk_sizes"]],
                chunking, settings))

    df = save_results(rows, test_calibration_cfg["output"]["csv_path"], test_calibration_cfg["output"]["plot_path"])
    print_recommendation(df)


def parse_args(
        retrieval_config: str, test_calibration_config: str,
        datasets_config: str, dataset: str | None,
        skip_alpha: bool, skip_top_k: bool, skip_chunk: bool) -> TestingArgs:
    """Validate and package Click arguments."""
    if skip_alpha and skip_top_k and skip_chunk:
        raise click.ClickException("At least one test calibration axis must be enabled.")

    return TestingArgs(
        retrieval_config=retrieval_config, test_calibration_config=test_calibration_config, datasets_config=datasets_config, 
        dataset=dataset, skip_alpha=skip_alpha, skip_top_k=skip_top_k, skip_chunk=skip_chunk)


@click.command()
@click.option("--retrieval-config", default="retrieval.yaml")
@click.option("--test-calibration-config", default="system_arch.yaml")
@click.option("--datasets-config", default="datasets.yaml")
@click.option("--dataset", default=None, help="Override the test calibration dataset.")
@click.option("--skip-alpha", is_flag=True, help="Skip the alpha test calibration.")
@click.option("--skip-top-k", is_flag=True, help="Skip the top-k test calibration.")
@click.option("--skip-chunk", is_flag=True, help="Skip the chunk-size test calibration; it re-indexes.")
def main(
        retrieval_config: str, test_calibration_config: str, datasets_config: str, 
        dataset: str | None, skip_alpha: bool, skip_top_k: bool, skip_chunk: bool):
    """Run calibration test calibration and produce the nDCG@10 plot."""
    args = parse_args(
        retrieval_config, test_calibration_config, datasets_config, 
        dataset, skip_alpha, skip_top_k, skip_chunk)
    run_test_calibration(args)


if __name__ == "__main__":
    main()  # type: ignore[call-arg]
