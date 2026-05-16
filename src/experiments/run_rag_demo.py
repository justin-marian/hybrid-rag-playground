"""End-to-end RAG demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from src.data.beir_loader import load_beir
from src.data.dataset_registry import get_spec
from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.rag.ollama_client import OllamaClient
from src.rag.rag_pipeline import RagPipeline
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.utils.io import load_yaml, save_json
from src.utils.logging import get_logger
from src.utils.paths import IMAGES_DIR, RESULTS_DIR, ensure_dirs, resolve
from src.weaviate_io.client import weaviate_client
from src.weaviate_io.schema import collection_name

logger = get_logger(__name__)
Retriever = BM25Retriever | DenseRetriever | HybridRetriever


def pick_queries(beir: Any, n_queries: int) -> list[tuple[str, str]]:
    """Pick the first query IDs that have at least one relevant document."""
    picked: list[tuple[str, str]] = []

    for qid, query_text in beir.queries.items():
        qrels = beir.qrels.get(qid, {})
        if any(score > 0 for score in qrels.values()):
            picked.append((qid, query_text))
        if len(picked) >= n_queries:
            return picked

    return picked


def build_retriever(
        name: str, client: Any, collection: str,
        embedder: MiniLMEmbedder, alpha: float) -> Retriever:
    """Build the selected retriever for the Weaviate collection."""
    retriever_name = name.lower()

    if retriever_name == "bm25":
        return BM25Retriever(client, collection)
    if retriever_name == "dense":
        return DenseRetriever(client, collection, embedder)
    if retriever_name == "hybrid":
        return HybridRetriever(client, collection, embedder, alpha=alpha)

    raise ValueError(f"Unknown retriever: {name!r}")


def truncate_cell(value: str, max_chars: int) -> str:
    """Normalize and truncate Markdown table cell text."""
    text = value.replace("\n", " ").replace("|", "\\|").strip()
    return text[:max_chars] + ("…" if len(text) > max_chars else "")


def render_markdown_summary(answers: list[dict[str, Any]], md_path: Path) -> None:
    """Write a Markdown summary for manual report evaluation."""
    if not answers:
        logger.warning("Skipping RAG demo Markdown summary because no answers were produced.")
        return

    first = answers[0]
    lines: list[str] = [
        "# RAG Manual Evaluation\n",
        f"**Dataset:** {first['dataset']}  ",
        f"**Retriever:** {first['retriever']}  ",
        f"**Top-k:** {first['top_k']}  ",
        f"**Queries:** {len(answers)}\n",
        "_Use this table during manual evaluation. Mark each row as_ "
        "`correct`, `partial`, or `hallucination` _and note the cited chunks._\n",
        "| # | Query | Top chunks (chunk_id) | LLM answer (truncated) | Notes |",
        "|---|---|---|---|---|"]

    for index, answer in enumerate(answers, start=1):
        hits = answer.get("hits", [])
        chunk_ids = ", ".join(str(hit["chunk_id"]) for hit in hits[:3] if "chunk_id" in hit)
        query = truncate_cell(str(answer.get("query", "")), 100)
        llm_answer = truncate_cell(str(answer.get("answer") or ""), 280)
        lines.append(f"| {index} | {query} | {chunk_ids} | {llm_answer} |   |")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    logger.info("Wrote RAG demo Markdown summary: %s", md_path)


def read_demo_settings(
        retrieval_config: str, rag_config: str,
        dataset: str | None, retriever: str | None,
        top_k: int | None, alpha: float | None,
        model: str | None, num_queries: int | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Read configs and resolve CLI overrides into deterministic demo settings."""
    retrieval_cfg = load_yaml(retrieval_config)
    rag_cfg = load_yaml(rag_config)
    settings = {
        "dataset_key": dataset or rag_cfg["rag"]["dataset"],
        "retriever_name": retriever or rag_cfg["rag"]["retriever"],
        "top_k": top_k or rag_cfg["rag"]["top_k"],
        "alpha": alpha if alpha is not None else retrieval_cfg["retrieval"]["hybrid_alpha"],
        "model_name": model or rag_cfg["llm"]["model"],
        "num_queries": num_queries or rag_cfg["demo"]["num_queries"]}
    return retrieval_cfg, rag_cfg, settings


def build_embedder(retrieval_cfg: dict[str, Any]) -> MiniLMEmbedder:
    """Build the configured MiniLM embedder."""
    embedding_cfg = retrieval_cfg["embedding"]
    return MiniLMEmbedder(
        model_name=embedding_cfg["model_name"], batch_size=embedding_cfg["batch_size"],
        normalize=embedding_cfg["normalize"], cache_dir=embedding_cfg["cache_dir"])


def build_llm(rag_cfg: dict[str, Any], model_name: str) -> OllamaClient:
    """Build and validate the configured Ollama client."""
    llm_cfg = rag_cfg["llm"]
    llm = OllamaClient(model=model_name, host=llm_cfg["host"], options=llm_cfg.get("options", {}))
    llm.ensure_model()
    return llm


def print_answer(query_id: str, query_text: str, answer: str) -> None:
    """Print one demo answer in the expected console format."""
    print("\n" + "=" * 72)
    print(f"Q[{query_id}]: {query_text}")
    print("-" * 72)
    print(answer.strip())
    print("=" * 72)


def save_results(answers: list[dict[str, Any]], results_dir: Path) -> tuple[Path, Path]:
    """Save JSON results and the Markdown report summary."""
    json_path = results_dir / "rag_demo.json"
    save_json(answers, json_path)
    logger.info("Wrote RAG demo JSON: %s", json_path)

    md_path = IMAGES_DIR / "rag_demo.md"
    render_markdown_summary(answers, md_path)
    return json_path, md_path


@click.command()
@click.option("--retrieval-config", default="retrieval.yaml")
@click.option("--rag-config", default="rag.yaml")
@click.option("--datasets-config", default="datasets.yaml")
@click.option("--dataset", default=None, help="Override the dataset key.")
@click.option("--retriever", default=None, help="bm25 | dense | hybrid (overrides rag.yaml).")
@click.option("--top-k", type=int, default=None)
@click.option("--alpha", type=float, default=None, help="Hybrid alpha override.")
@click.option("--model", default=None, help="Ollama model override (e.g. llama3.2:3b).")
@click.option("--num-queries", type=int, default=None)
def main(
        retrieval_config: str, rag_config: str, datasets_config: str,
        dataset: str | None, retriever: str | None, top_k: int | None,
        alpha: float | None, model: str | None, num_queries: int | None) -> None:
    """Run the end-to-end RAG demo on a fixed batch of queries."""
    retrieval_cfg, rag_cfg, settings = read_demo_settings(
        retrieval_config, rag_config,
        dataset, retriever, top_k, alpha, model, num_queries)

    spec = get_spec(settings["dataset_key"], datasets_config)
    collection = collection_name(retrieval_cfg["weaviate"]["collection_prefix"], spec.key)
    embedder = build_embedder(retrieval_cfg)
    llm = build_llm(rag_cfg, settings["model_name"])

    results_dir = resolve(rag_cfg["demo"]["results_dir"])
    ensure_dirs(results_dir, RESULTS_DIR, IMAGES_DIR)

    beir = load_beir(spec)
    queries = pick_queries(beir, settings["num_queries"])
    logger.info(
        "Running RAG demo: dataset=%s retriever=%s top_k=%d model=%s queries=%d",
        spec.name, settings["retriever_name"], settings["top_k"],
        settings["model_name"], len(queries))

    answers: list[dict[str, Any]] = []
    weaviate_cfg = retrieval_cfg["weaviate"]
    with weaviate_client(
            host=weaviate_cfg["host"], http_port=weaviate_cfg["http_port"],
            grpc_port=weaviate_cfg["grpc_port"]) as client:
        retriever_obj = build_retriever(
            settings["retriever_name"], client, collection,
            embedder, settings["alpha"])
        pipeline = RagPipeline(
            retriever=retriever_obj, llm=llm, prompt_template=rag_cfg["prompt_template"],
            dataset_name=spec.name, top_k=settings["top_k"],
            max_chunk_chars=rag_cfg["rag"]["max_chunk_chars"])

        for query_id, query_text in queries:
            logger.info("Q[%s]: %s", query_id, query_text[:120])
            output = pipeline.answer(query_text, query_id=query_id)
            answers.append(output.to_dict())
            print_answer(query_id, query_text, output.answer)

    json_path, md_path = save_results(answers, results_dir)
    print("\nWrote:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")
    print("\nReminder (Cerința 3): manually mark at least one row in {md_path} as `hallucination` and discuss the cause in the report.")


if __name__ == "__main__":
    main()  # type: ignore[call-arg]
