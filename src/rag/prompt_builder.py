"""Build the RAG prompt sent to the local LLM."""

from __future__ import annotations

from pathlib import Path

from src.retrieval.base import RetrievedHit
from src.utils.paths import resolve


def truncate_text(text: str, max_chars: int) -> str:
    """Return text truncated to the character budget."""
    text = text.strip()
    return text if len(text) <= max_chars else f"{text[:max_chars].rstrip()}…"


def load_prompt_template(path: str | Path) -> str:
    """Load a prompt template from disk."""
    prompt_path = resolve(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8-sig")


def format_context_block(hits: list[RetrievedHit], dataset_name: str, max_chunk_chars: int = 1200) -> str:
    """Render retrieved hits as a citation-friendly context block."""
    blocks: list[str] = []
    for hit in hits:
        text = truncate_text(hit.text, max_chunk_chars)
        header = f"[chunk_id={hit.chunk_id} | doc_id={hit.doc_id} | dataset={dataset_name}]"
        blocks.append(f"{header}\n{text}")
    return "\n\n".join(blocks)


def build_prompt(template: str, query: str, hits: list[RetrievedHit], dataset_name: str, max_chunk_chars: int = 1200) -> str:
    """Format a prompt template with the query and retrieved context."""
    context_block = format_context_block(hits, dataset_name, max_chunk_chars=max_chunk_chars)
    return template.format(query=query.strip(), context_block=context_block)


def build_prompt_from_file(query: str, hits: list[RetrievedHit], dataset_name: str, template_path: str | Path, max_chunk_chars: int = 1200) -> str:
    """Load a prompt template from disk and format it."""
    template = load_prompt_template(template_path)
    return build_prompt(template, query, hits, dataset_name, max_chunk_chars=max_chunk_chars)
