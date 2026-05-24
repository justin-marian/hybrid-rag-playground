"""Document-aware adaptive chunking for BEIR RAG experiments."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from transformers import AutoTokenizer

from src.utils.logging import get_logger

load_dotenv()

logger = get_logger(__name__)


@dataclass
class Chunk:
    """A single retrieval unit with document-level provenance."""

    chunk_id: str
    doc_id: str
    dataset: str
    title: str
    text: str
    chk_idx: int
    strategy: str = "document_aware"
    is_full_doc: bool = False


def normalize_text(text: str) -> str:
    """Normalize line endings and repeated whitespace."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_sentences(text: str) -> list[str]:
    """Split text into lightweight sentence units."""
    text = text.strip()
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9ȘȚĂÂÎ])", text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

def flush_current(chunks: list[str], curr_sentences: list[str]):
    """Append the current sentence buffer if it contains text."""
    if curr_sentences and (chunk := " ".join(curr_sentences).strip()):
        chunks.append(chunk)


@dataclass
class AdaptiveDocChunker:
    """Chunk BEIR documents adaptively while preserving document-level relevance alignment."""

    tokenizer_name: str | None = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer: Any | None = field(default=None, init=False, repr=False)

    chunk_size_tokens: int = 512
    min_chunk_tokens: int = 80
    full_doc_thr_tokens: int = 384

    overlap_ratio: float = 0.10
    preserve_title: bool = True

    def __post_init__(self):
        if not 0.0 <= self.overlap_ratio < 1.0:
            raise ValueError("overlap_ratio must be in [0, 1).")
        if self.chunk_size_tokens < 64:
            raise ValueError("chunk_size_tokens must be at least 64.")
        if self.full_doc_thr_tokens < 64:
            raise ValueError("full_doc_thr_tokens must be at least 64.")
        if self.full_doc_thr_tokens > self.chunk_size_tokens:
            raise ValueError("full_doc_thr_tokens cannot exceed chunk_size_tokens.")
        if self.min_chunk_tokens < 1:
            raise ValueError("min_chunk_tokens must be positive.")

    @property
    def overlap_tokens(self) -> int:
        """Return the overlap budget in tokens."""
        return max(1, int(self.chunk_size_tokens * self.overlap_ratio))

    @property
    def stride(self) -> int:
        """Return the token-window stride used by fallback splitting."""
        return max(1, self.chunk_size_tokens - self.overlap_tokens)

    def load_tokenizer(self) -> Any | None:
        """Load the HuggingFace tokenizer lazily, falling back to word counts on failure."""
        if self.tokenizer is not None or self.tokenizer_name is None:
            return self.tokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        if hasattr(self.tokenizer, "model_max_length"):
            self.tokenizer.model_max_length = int(1e9)
        logger.debug("Loaded tokenizer: %s", self.tokenizer_name)
        return self.tokenizer

    def token_count(self, text: str) -> int:
        """Count tokens using the configured tokenizer or whitespace fallback."""
        text = text.strip()
        if not text:
            return 0

        tokenizer = self.load_tokenizer()
        if tokenizer is None:
            return len(text.split())
        return len(tokenizer.encode(text, add_special_tokens=False))

    def token_window_split(self, text: str) -> list[str]:
        """Split text with overlapping token windows as the final fallback."""
        text = text.strip()
        if not text:
            return []

        tokenizer = self.load_tokenizer()
        if tokenizer is None:
            return self.word_window_split(text)

        token_ids = tokenizer.encode(text, add_special_tokens=False)
        chunks: list[str] = []
        for start in range(0, len(token_ids), self.stride):
            window = token_ids[start:start + self.chunk_size_tokens]
            if not window:
                break

            if chunk := tokenizer.decode(window, skip_special_tokens=True).strip():
                chunks.append(chunk)
            if start + self.chunk_size_tokens >= len(token_ids):
                break

        return chunks

    def word_window_split(self, text: str) -> list[str]:
        """Split text with overlapping word windows when no tokenizer is available."""
        words = text.split()
        chunks: list[str] = []
        for start in range(0, len(words), self.stride):
            window = words[start:start + self.chunk_size_tokens]
            if not window:
                break

            chunks.append(" ".join(window))
            if start + self.chunk_size_tokens >= len(words):
                break

        return chunks

    def make_sentence_windows(self, text: str) -> list[str]:
        """Create sentence windows only when the full document is too large."""
        sentences = split_sentences(text)
        if len(sentences) <= 1:
            return self.token_window_split(text)

        chunks: list[str] = []
        curr_sentences: list[str] = []
        curr_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.token_count(sentence)
            if sentence_tokens > self.chunk_size_tokens:
                flush_current(chunks, curr_sentences)
                curr_sentences, curr_tokens = [], 0
                chunks.extend(self.token_window_split(sentence))
                continue

            if curr_sentences and curr_tokens + sentence_tokens > self.chunk_size_tokens:
                chunks.append(" ".join(curr_sentences).strip())
                curr_sentences = self.select_sentence_overlap(curr_sentences)
                curr_tokens = sum(self.token_count(sentence) for sentence in curr_sentences)

            curr_sentences.append(sentence)
            curr_tokens += sentence_tokens

        flush_current(chunks, curr_sentences)
        return self.merge_small_chunks(chunks)

    def select_sentence_overlap(self, sentences: list[str]) -> list[str]:
        """Select trailing complete sentences within the overlap budget."""
        selected: list[str] = []
        total_tokens = 0

        for sentence in reversed(sentences):
            sentence_tokens = self.token_count(sentence)
            if selected and total_tokens + sentence_tokens > self.overlap_tokens:
                break

            selected.append(sentence)
            total_tokens += sentence_tokens
            if total_tokens >= self.overlap_tokens:
                break

        return list(reversed(selected))

    def merge_small_chunks(self, chunks: list[str]) -> list[str]:
        """Merge tiny chunks into the previous chunk when the token budget allows it."""
        merged: list[str] = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            chunk_tokens = self.token_count(chunk)
            if (merged and chunk_tokens < self.min_chunk_tokens and self.token_count(merged[-1]) + chunk_tokens <= self.chunk_size_tokens):
                merged[-1] = f"{merged[-1]} {chunk}".strip()
            else:
                merged.append(chunk)

        return merged

    def chunk_text(self, text: str) -> list[str]:
        """Return document-aware chunks for one text."""
        if text := normalize_text(text):
            return [text] if self.token_count(text) <= self.full_doc_thr_tokens else self.make_sentence_windows(text)
        else:
            return []

    def chunk_document(self, doc_id: str, title: str, text: str, dataset: str) -> list[Chunk]:
        """Chunk one BEIR document while preserving source-document provenance."""
        title, text = title or "", text or ""
        body = f"{title.strip()}. {text.strip()}".strip() if self.preserve_title and title else text.strip()
        pieces = self.chunk_text(body)
        is_full_doc = len(pieces) == 1

        return [Chunk(
            chunk_id=f"{doc_id}::doc" if is_full_doc else f"{doc_id}::part_{index:03d}",
            doc_id=doc_id, dataset=dataset, title=title, text=piece,
            chk_idx=index, strategy="document_aware", 
            is_full_doc=is_full_doc
        ) for index, piece in enumerate(pieces)]

    def chunk_corpus(self, corpus: dict[str, dict[str, str]], dataset: str) -> Iterable[Chunk]:
        """Yield chunks for every document in a BEIR corpus."""
        for doc_id, doc in corpus.items():
            yield from self.chunk_document(doc_id=doc_id, title=doc.get("title", ""), text=doc.get("text", ""), dataset=dataset)
