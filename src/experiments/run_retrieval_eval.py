"""Retrieval evaluation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import click

from src.data.beir_loader import load_beir
from src.data.dataset_registry import load_registry
from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.evaluation.evaluator import EvalResult, evaluate_retriever
from src.evaluation.tables import results_to_wide_df, save_results
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.utils.io import load_yaml
from src.utils.logging import get_logger
from src.utils.paths import DATA_DIR, DOCS_DIR, RESULTS_DIR, ensure_dirs
from src.weaviate_io.client import weaviate_client
from src.weaviate_io.schema import collection_name

logger = get_logger(__name__)


@dataclass(frozen=True)
class EvalArgs:
    """Parsed CLI arguments for retrieval evaluation."""

    datasets: tuple[str, ...]
    config: str
    datasets_config: str
    top_k: int | None
    alpha: float | None


@dataclass(frozen=True)
class RetrievalSettings:
    """Resolved retrieval settings used by all datasets."""

    top_k: int
    alpha: float
    prefix: str


@dataclass(frozen=True)
class WeaviateSettings:
    """Weaviate connection settings."""

    host: str
    http_port: int
    grpc_port: int


def parse_args(
        datasets: tuple[str, ...], config: str, datasets_config: str,
        top_k: int | None, alpha: float | None) -> EvalArgs:
    """Validate and package Click arguments."""
    if top_k is not None and top_k < 1:
        raise click.ClickException("--top-k must be at least 1.")
    if alpha is not None and not 0.0 <= alpha <= 1.0:
        raise click.ClickException("--alpha must be in [0, 1].")

    return EvalArgs(datasets=datasets, config=config, datasets_config=datasets_config, top_k=top_k, alpha=alpha)


def read_retrieval_settings(cfg: dict[str, Any], args: EvalArgs) -> RetrievalSettings:
    """Resolve retrieval settings from config and CLI overrides."""
    values = cfg["retrieval"]
    return RetrievalSettings(
        top_k=int(args.top_k or values["top_k"]),
        alpha=float(args.alpha if args.alpha is not None else values["hybrid_alpha"]),
        prefix=str(cfg["weaviate"]["collection_prefix"]))


def read_weaviate_settings(cfg: dict[str, Any]) -> WeaviateSettings:
    """Read Weaviate connection settings from config."""
    values = cfg["weaviate"]
    return WeaviateSettings(host=str(values["host"]), http_port=int(values["http_port"]), grpc_port=int(values["grpc_port"]))


def build_embedder(cfg: dict[str, Any]) -> MiniLMEmbedder:
    """Create the MiniLM embedder from retrieval config."""
    values = cfg["embedding"]
    return MiniLMEmbedder(
        model_name=values["model_name"], batch_size=int(values["batch_size"]),
        normalize=bool(values["normalize"]), cache_dir=values["cache_dir"])


def selected_dataset_keys(registry: dict[str, Any], requested: tuple[str, ...]) -> list[str]:
    """Return selected dataset keys with validation."""
    keys = list(requested) if requested else list(registry.keys())
    if missing := [key for key in keys if key not in registry]:
        available = ", ".join(sorted(registry.keys()))
        raise click.ClickException(f"Unknown dataset(s): {missing}. Available: {available}")
    return keys


def build_retrievers(client: Any, collection: str, embedder: MiniLMEmbedder, alpha: float) -> list[Any]:
    """Create BM25, dense, and hybrid retrievers for one collection."""
    return [
        BM25Retriever(client, collection),
        DenseRetriever(client, collection, embedder),
        HybridRetriever(client, collection, embedder, alpha=alpha)]


def evaluate_dataset(
        client: Any, key: str, spec: Any, settings: RetrievalSettings,
        embedder: MiniLMEmbedder) -> list[EvalResult]:
    """Evaluate all retrievers for one BEIR dataset."""
    collection = collection_name(settings.prefix, spec.key)
    logger.info("=== Evaluating dataset=%s collection=%s ===", spec.name, collection)
    beir = load_beir(spec)

    results: list[EvalResult] = []
    for retriever in build_retrievers(client, collection, embedder, settings.alpha):
        result = evaluate_retriever(
            retriever=retriever, queries=beir.queries,
            qrels=beir.qrels, dataset_name=spec.name,
            top_k=settings.top_k)
        results.append(result)

    return results


def save_eval_outputs(results: list[EvalResult]):
    """Save long and wide retrieval evaluation tables."""
    save_results(results, csv_path=RESULTS_DIR / "retrieval_metrics.csv", md_path=DOCS_DIR / "RETRIEVAL_COMPARE_TABLE.md")

    wide = results_to_wide_df(results)
    wide_csv = DATA_DIR / "retrieval_comparison_table.csv"
    wide.to_csv(wide_csv)
    logger.info("Wrote wide-format comparative CSV: %s", wide_csv)

    print("\n=== Retrieval comparison (rows = retrievers, cols = (dataset, metric)) ===\n")
    print(wide.to_string(float_format=lambda value: f"{value:.4f}"))


def run_from_args(args: EvalArgs):
    """Run BM25, dense, and hybrid retrieval evaluation from parsed arguments."""
    cfg = load_yaml(args.config)
    registry = load_registry(args.datasets_config)
    keys = selected_dataset_keys(registry, args.datasets)
    settings = read_retrieval_settings(cfg, args)
    weaviate = read_weaviate_settings(cfg)
    embedder = build_embedder(cfg)

    ensure_dirs(RESULTS_DIR, DOCS_DIR)
    all_results: list[EvalResult] = []

    with weaviate_client(host=weaviate.host, http_port=weaviate.http_port, grpc_port=weaviate.grpc_port) as client:
        for key in keys:
            all_results.extend(evaluate_dataset(client, key, registry[key], settings, embedder))

    save_eval_outputs(all_results)


@click.command()
@click.option("--dataset", "datasets", multiple=True, default=None, help="Restrict to specific datasets.")
@click.option("--config", default="retrieval.yaml")
@click.option("--datasets-config", default="datasets.yaml")
@click.option("--top-k", type=int, default=None, help="Override top-k from config.")
@click.option("--alpha", type=float, default=None, help="Override hybrid alpha.")
def main(datasets: tuple[str, ...], config: str, datasets_config: str, top_k: int | None, alpha: float | None):
    """Run BM25, dense, and hybrid retrieval evaluation."""
    args = parse_args(datasets, config, datasets_config, top_k, alpha)
    run_from_args(args)


if __name__ == "__main__":
    main()  # type: ignore[call-arg]
