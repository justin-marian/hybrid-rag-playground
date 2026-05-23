"""Batch-index chunks with BYO vectors into Weaviate."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Any

from tqdm import tqdm
from weaviate import WeaviateClient

from src.chunking.adaptive_chunker import Chunk
from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.utils.logging import get_logger

logger = get_logger(__name__)


def to_uuid(chunk_id: str) -> str:
    """Return a deterministic UUID-5 string for an idempotent Weaviate object ID."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def chunk_index(chunk: Chunk) -> int:
    """Return the chunk index while tolerating older chunk field names."""
    return int(chunk.chk_idx)


def chunk_properties(chunk: Chunk) -> dict[str, Any]:
    """Build the Weaviate property payload for one chunk."""
    properties = {
        "chunk_id": chunk.chunk_id, "doc_id": chunk.doc_id,
        "dataset": chunk.dataset, "title": chunk.title,
        "chk_idx": chunk_index(chunk), "text": chunk.text}

    if hasattr(chunk, "strategy"):
        properties["strategy"] = chunk.strategy
    if hasattr(chunk, "is_full_doc"):
        properties["is_full_doc"] = bool(chunk.is_full_doc)

    return properties


def log_failed_objects(failed: Iterable[object], limit: int = 3) -> int:
    """Log failed Weaviate batch objects and return their count."""
    failed_list = list(failed)
    if not failed_list:
        return 0

    logger.error("Indexing failed for %d objects (first %d shown):", len(failed_list), min(limit, len(failed_list)))
    for failed_obj in failed_list[:limit]:
        logger.error("  - %s", failed_obj)
    return len(failed_list)


def index_chunks(client: WeaviateClient, collection_name: str, chunks: list[Chunk], embedder: MiniLMEmbedder, batch_size: int, vector_name: str = "default") -> int:
    """Embed chunks and insert them into a Weaviate collection."""
    if not chunks:
        logger.warning("No chunks to index into %s", collection_name)
        return 0

    logger.info("Embedding %d chunks for collection %s with %s", len(chunks), collection_name, embedder.model_name)
    vectors = embedder.encode([chunk.text for chunk in chunks], show_progress=True)
    embedder.save_cache()

    collection = client.collections.get(collection_name)
    logger.info("Inserting %d objects into %s (batch=%d)", len(chunks), collection_name, batch_size)

    inserted = 0
    with collection.batch.fixed_size(batch_size=batch_size) as batch:
        iterator = zip(chunks, vectors, strict=True)
        for chunk, vector in tqdm(iterator, total=len(chunks), desc=f"Indexing {collection_name}"):
            batch.add_object(properties=chunk_properties(chunk), uuid=to_uuid(chunk.chunk_id), vector={vector_name: vector.tolist()})
            inserted += 1

    failed_count = log_failed_objects(collection.batch.failed_objects)
    logger.info("Indexing complete for %s: attempted=%d, failed=%d", collection_name, inserted, failed_count)
    return inserted - failed_count


def collection_size(client: WeaviateClient, collection_name: str) -> int:
    """Return the number of objects currently stored in a collection."""
    collection = client.collections.get(collection_name)
    return collection.aggregate.over_all(total_count=True).total_count
