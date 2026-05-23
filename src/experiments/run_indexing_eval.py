"""Indexing evaluation pipeline."""

from __future__ import annotations

from typing import Any

import click

from src.chunking.adaptive_chunker import AdaptiveDocChunker
from src.data.beir_loader import load_beir
from src.data.dataset_registry import load_datasets
from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.utils.io import load_yaml
from src.utils.logging import get_logger
from src.weaviate_io.client import weaviate_client
from src.weaviate_io.indexer import collection_size, index_chunks
from src.weaviate_io.schema import collection_name, ensure_collection

logger = get_logger(__name__)


def read_defaults(
    config: str, datasets_config: str,
    datasets: tuple[str, ...], chunk_size: int | None, overlap_ratio: float | None
) -> tuple[dict[str, Any], dict[str, Any], list[str], int, float]:
    """Read config files and resolve CLI overrides."""
    cfg = load_yaml(config)
    registry = load_datasets(datasets_config)

    selected_keys = list(datasets) if datasets else list(registry.keys())
    chunk_size_tokens = chunk_size or cfg["chunking"]["chunk_size_tokens"]
    overlap = overlap_ratio if overlap_ratio is not None else cfg["chunking"]["overlap_ratio"]

    return cfg, registry, selected_keys, chunk_size_tokens, overlap


def build_chunker(cfg: dict[str, Any], chunk_size_tokens: int, overlap_ratio: float) -> AdaptiveDocChunker:
    """Build the adaptive chunker."""
    chk_cfg = cfg["chunking"]

    return AdaptiveDocChunker(
        chunk_size_tokens=chunk_size_tokens, min_chunk_tokens=chk_cfg["min_chunk_tokens"],
        full_doc_thr_tokens=chk_cfg["full_doc_thr_tokens"], overlap_ratio=overlap_ratio,
        preserve_title=chk_cfg["preserve_title"], tokenizer_name=chk_cfg["tokenizer"])


def build_embedder(cfg: dict[str, Any]) -> MiniLMEmbedder:
    """Build the sentence embedder."""
    emb_cfg = cfg["embedding"]

    return MiniLMEmbedder(
        model_name=emb_cfg["model_name"], batch_size=emb_cfg["batch_size"],
        max_seq_length=emb_cfg["max_seq_length"], normalize=emb_cfg["normalize"], cache_dir=emb_cfg["cache_dir"])


def index_dataset(client: Any, spec: Any, cfg: dict[str, Any], chunker: AdaptiveDocChunker, embedder: MiniLMEmbedder, recreate: bool):
    """Index one BEIR dataset into Weaviate."""
    weaviate_cfg = cfg["weaviate"]
    vector_name = weaviate_cfg["vector_name"]
    coll_name = collection_name(weaviate_cfg["collection_prefix"], spec.key)

    logger.info(
        "Indexing dataset=%s collection=%s chunk_size=%d overlap=%.2f",
        spec.name, coll_name, chunker.chunk_size_tokens, chunker.overlap_ratio)

    ensure_collection(
        client, coll_name, vector_name=vector_name,
        recreate=recreate, distance=weaviate_cfg["distance"])

    beir = load_beir(spec)
    chunks = list(chunker.chunk_corpus(beir.corpus, dataset=spec.name))
    logger.info("Built %d chunks from %d docs.", len(chunks), beir.num_docs)

    inserted = index_chunks(
        client=client, collection_name=coll_name, chunks=chunks,
        embedder=embedder, vector_name=vector_name, batch_size=weaviate_cfg["batch_size"])

    final_size = collection_size(client, coll_name)
    logger.info("Indexed %d chunks into %s; collection now holds %d objects.", inserted, coll_name, final_size)


@click.command()
@click.option("--dataset", "datasets", multiple=True, default=None, help="Dataset key(s) to index. If omitted, all datasets from configs/datasets.yaml are indexed.")
@click.option("--config", default="retrieval.yaml", help="Retrieval config YAML.")
@click.option("--datasets-config", default="datasets.yaml", help="Datasets config YAML.")
@click.option("--recreate/--no-recreate", default=False, help="Drop and recreate collections.")
@click.option("--chunk-size", type=int, default=None, help="Override chunk size in tokens.")
@click.option("--overlap-ratio", type=float, default=None, help="Override chunk overlap ratio.")
def main(datasets: tuple[str, ...], config: str, datasets_config: str, recreate: bool, chunk_size: int | None, overlap_ratio: float | None):
    """Index BEIR datasets into Weaviate using external vectors."""
    retrieval_cfg, datasets_cfg, selected_keys, chunk_size_tokens, overlap = read_defaults(config, datasets_config, datasets, chunk_size, overlap_ratio)
    chunker = build_chunker(retrieval_cfg, chunk_size_tokens, overlap)
    embedder = build_embedder(retrieval_cfg)

    with weaviate_client(host=retrieval_cfg["weaviate"]["host"],  http_port=retrieval_cfg["weaviate"]["http_port"], grpc_port=retrieval_cfg["weaviate"]["grpc_port"]) as client:
        for key in selected_keys:
            index_dataset(client, datasets_cfg[key], retrieval_cfg, chunker, embedder, recreate)


if __name__ == "__main__":
    main()  # type: ignore[call-arg]
