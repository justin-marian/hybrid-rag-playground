"""End-to-end RAG pipeline: retrieval, prompting, and local generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.rag.ollama_client import OllamaClient
from src.rag.prompt_builder import build_prompt
from src.retrieval.base import RetrievedHit, Retriever


@dataclass
class RagAnswer:
    """Serializable RAG output for manual evaluation and JSON export."""

    query_id: str
    query: str
    dataset: str
    retriever: str
    top_k: int
    hits: list[dict[str, Any]]
    prompt: str
    answer: str

    def to_dict(self) -> dict[str, Any]:
        """Return the answer as a plain dictionary."""
        return asdict(self)


class RagPipeline:
    """Compose a retriever and an Ollama client into one answer call."""

    def __init__(
        self, retriever: Retriever, llm: OllamaClient, prompt_template: str,
        dataset_name: str, top_k: int = 10, max_chunk_chars: int = 1200) -> None:
        self.retriever = retriever
        self.llm = llm
        self.prompt_template = prompt_template
        self.dataset_name = dataset_name
        self.top_k = top_k
        self.max_chunk_chars = max_chunk_chars

    @staticmethod
    def serialize_hit(hit: RetrievedHit) -> dict[str, Any]:
        """Serialize one retrieved hit for reports and JSON dumps."""
        return {
            "chunk_id": hit.chunk_id, "doc_id": hit.doc_id,
            "title": hit.title, "text": hit.text, 
            "rank": hit.rank, "score": hit.score}

    def serialize_hits(self, hits: list[RetrievedHit]) -> list[dict[str, Any]]:
        """Serialize retrieved hits without changing their order."""
        return [self.serialize_hit(hit) for hit in hits]

    def build_prompt(self, query: str, hits: list[RetrievedHit]) -> str:
        """Build the LLM prompt from the configured template."""
        return build_prompt(
            self.prompt_template, query, hits, self.dataset_name,
            max_chunk_chars=self.max_chunk_chars)

    def answer(self, query: str, query_id: str = "") -> RagAnswer:
        """Run retrieval and generation for one query."""
        hits = self.retriever.search(query, top_k=self.top_k)
        prompt = self.build_prompt(query, hits)
        answer_text = self.llm.generate(prompt)
        return RagAnswer(
            query_id=query_id, query=query, 
            dataset=self.dataset_name,
            retriever=self.retriever.name, top_k=self.top_k,
            hits=self.serialize_hits(hits), prompt=prompt, answer=answer_text)
