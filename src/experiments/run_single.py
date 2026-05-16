"""Single-query end-to-end demo for the 2 minute screen recording."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.data.beir_loader import load_beir
from src.data.dataset_registry import get_spec
from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.rag.ollama_client import OllamaClient
from src.rag.rag_pipeline import RagPipeline
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.utils.io import load_yaml
from src.utils.logging import get_logger
from src.weaviate_io.client import weaviate_client
from src.weaviate_io.schema import collection_name

logger = get_logger(__name__)
console = Console()


@dataclass(frozen=True)
class DemoArgs:
    """Parsed CLI arguments for one RAG demo run."""

    retrieval_config: str
    rag_config: str
    datasets_config: str
    dataset: str | None
    query_text: str | None
    top_k: int
    alpha: float | None
    model: str | None


def parse_args(
        retrieval_config: str, rag_config: str, datasets_config: str,
        dataset: str | None, query_text: str | None, top_k: int,
        alpha: float | None, model: str | None) -> DemoArgs:
    """Validate and package Click arguments."""
    if top_k < 1:
        raise click.ClickException("--top-k must be at least 1.")
    if alpha is not None and not 0.0 <= alpha <= 1.0:
        raise click.ClickException("--alpha must be in [0, 1].")
    return DemoArgs(
        retrieval_config=retrieval_config, rag_config=rag_config,
        datasets_config=datasets_config, dataset=dataset,
        query_text=query_text, top_k=top_k, alpha=alpha, model=model)


def truncate(text: str, max_chars: int) -> str:
    """Return a single-line text snippet."""
    snippet = text.replace("\n", " ").strip()
    return snippet[:max_chars] + ("…" if len(snippet) > max_chars else "")


def print_hits(title: str, hits: Any, max_chars: int = 180) -> None:
    """Pretty-print retrieval hits as a Rich table."""
    table = Table(title=title, show_lines=False)
    table.add_column("Rank", justify="right", style="cyan", width=4)
    table.add_column("Score", justify="right", style="magenta", width=8)
    table.add_column("chunk_id", style="green", overflow="fold")
    table.add_column("doc_id", style="yellow", overflow="fold")
    table.add_column("Text snippet", overflow="fold")

    for hit in hits:
        table.add_row(str(hit.rank), f"{hit.score:.3f}", hit.chunk_id, hit.doc_id, truncate(hit.text, max_chars))
    console.print(table)


def build_embedder(cfg: dict[str, Any]) -> MiniLMEmbedder:
    """Create the MiniLM embedder from retrieval config."""
    emb = cfg["embedding"]
    return MiniLMEmbedder(
        model_name=emb["model_name"], batch_size=int(emb["batch_size"]),
        normalize=bool(emb["normalize"]), cache_dir=emb["cache_dir"])


def resolve_query(query_text: str | None, spec: Any) -> str:
    """Return an explicit query or the first qrels-backed BEIR test query."""
    if query_text:
        return query_text

    beir = load_beir(spec)
    for qid, query in beir.queries.items():
        if any(rel > 0 for rel in beir.qrels.get(qid, {}).values()):
            console.print(f"[dim]Using test query[/dim] [bold]{qid}[/bold]: {query}")
            return query
    raise click.ClickException("Could not resolve a query. Pass --query 'your text'.")


def build_llm(cfg: dict[str, Any], model_name: str) -> OllamaClient:
    """Create and validate the local Ollama client."""
    llm_cfg = cfg["llm"]
    llm = OllamaClient(model=model_name, host=llm_cfg["host"], options=llm_cfg.get("options", {}))
    llm.ensure_model()
    return llm


def run_demo(
        client: Any, collection: str, query_text: str, dataset_name: str,
        retrieval_cfg: dict[str, Any], rag_cfg: dict[str, Any],
        top_k: int, alpha: float, model_name: str) -> str:
    """Run BM25, dense, hybrid, and final RAG for one query."""
    embedder = build_embedder(retrieval_cfg)
    bm25 = BM25Retriever(client, collection)
    dense = DenseRetriever(client, collection, embedder)
    hybrid = HybridRetriever(client, collection, embedder, alpha=alpha)
    hybrid_hits = hybrid.search(query_text, top_k=top_k)

    print_hits("1) BM25", bm25.search(query_text, top_k=top_k))
    print_hits("2) Dense", dense.search(query_text, top_k=top_k))
    print_hits(f"3) Hybrid (alpha={alpha:.2f})", hybrid_hits)

    pipeline = RagPipeline(
        retriever=hybrid, llm=build_llm(rag_cfg, model_name),
        prompt_template=rag_cfg["prompt_template"], dataset_name=dataset_name,
        top_k=top_k, max_chunk_chars=rag_cfg["rag"]["max_chunk_chars"])
    return pipeline.answer(query_text).answer


def run_from_args(args: DemoArgs) -> None:
    """Run one query through BM25, dense, hybrid, and RAG from parsed arguments."""
    retrieval_cfg = load_yaml(args.retrieval_config)
    rag_cfg = load_yaml(args.rag_config)

    dataset_key = args.dataset or rag_cfg["rag"]["dataset"]
    spec = get_spec(dataset_key, args.datasets_config)
    collection = collection_name(retrieval_cfg["weaviate"]["collection_prefix"], spec.key)
    alpha_value = args.alpha if args.alpha is not None else retrieval_cfg["retrieval"]["hybrid_alpha"]
    model_name = args.model or rag_cfg["llm"]["model"]
    query_text = resolve_query(args.query_text, spec)

    console.print(Panel.fit(query_text, title="Query", border_style="bold cyan"))
    with weaviate_client(
        host=retrieval_cfg["weaviate"]["host"],
        http_port=retrieval_cfg["weaviate"]["http_port"],
        grpc_port=retrieval_cfg["weaviate"]["grpc_port"]) as client:
        answer = run_demo(client, collection, query_text, spec.name, retrieval_cfg, rag_cfg, args.top_k, alpha_value, model_name)
    console.print(Panel(answer.strip(), title="4) Final RAG answer", border_style="bold green"))


@click.command()
@click.option("--retrieval-config", default="retrieval.yaml")
@click.option("--rag-config", default="rag.yaml")
@click.option("--datasets-config", default="datasets.yaml")
@click.option("--dataset", default=None)
@click.option("--query", "query_text", default=None, help="Query, if omitted, picked from test set.")
@click.option("--top-k", type=int, default=5)
@click.option("--alpha", type=float, default=None)
@click.option("--model", default=None)
def main(
        retrieval_config: str, rag_config: str, datasets_config: str,
        dataset: str | None, query_text: str | None, top_k: int,
        alpha: float | None, model: str | None) -> None:
    """Run one query through BM25, dense, hybrid, and RAG."""
    args = parse_args(retrieval_config, rag_config, datasets_config, dataset, query_text, top_k, alpha, model)
    run_from_args(args)


if __name__ == "__main__":
    main()  # type: ignore[call-arg]
