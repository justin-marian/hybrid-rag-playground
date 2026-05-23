"""Schema management for per-dataset Weaviate collections."""

from __future__ import annotations

import weaviate.classes.config as wvcc
from weaviate import WeaviateClient

from src.utils.logging import get_logger

logger = get_logger(__name__)


DISTANCE_METRICS: dict[str, wvcc.VectorDistances] = {
    "cosine": wvcc.VectorDistances.COSINE,
    "l2-squared": wvcc.VectorDistances.L2_SQUARED,
    "dot": wvcc.VectorDistances.DOT}

CHUNK_PROPERTIES = [
    wvcc.Property(name="chunk_id", data_type=wvcc.DataType.TEXT),
    wvcc.Property(name="doc_id", data_type=wvcc.DataType.TEXT),
    wvcc.Property(name="dataset", data_type=wvcc.DataType.TEXT),
    wvcc.Property(name="title", data_type=wvcc.DataType.TEXT),
    wvcc.Property(name="chk_idx", data_type=wvcc.DataType.INT),
    wvcc.Property(name="text", data_type=wvcc.DataType.TEXT),
    wvcc.Property(name="strategy", data_type=wvcc.DataType.TEXT),
    wvcc.Property(name="is_full_doc", data_type=wvcc.DataType.BOOL)]


def collection_name(prefix: str, dataset_key: str) -> str:
    """Build a Weaviate-safe collection name using a PascalCase dataset suffix."""
    safe = dataset_key.replace("-", "_").replace(" ", "_")
    suffix = "".join(part.capitalize() for part in safe.split("_") if part)
    return f"{prefix}_{suffix}"


def distance_metric(distance: str) -> wvcc.VectorDistances:
    """Return the Weaviate vector distance enum for a user-facing distance name."""
    key = distance.lower().strip()
    if key not in DISTANCE_METRICS:
        valid = ", ".join(sorted(DISTANCE_METRICS))
        raise ValueError(f"Unsupported distance '{distance}'. Expected one of: {valid}.")
    return DISTANCE_METRICS[key]


def ensure_collection(client: WeaviateClient, name: str, distance: str, recreate: bool, vector_name: str = "default") -> None:
    """Create a Weaviate collection unless it already exists."""
    if recreate and client.collections.exists(name):
        logger.warning("Dropping existing collection %s", name)
        client.collections.delete(name)

    if client.collections.exists(name):
        logger.info("Collection %s already exists; reusing.", name)
        return

    metric = distance_metric(distance)
    logger.info("Creating Weaviate collection %s (distance=%s, vector=%s)", name, distance, vector_name)
    client.collections.create(
        name=name,
        vector_config=wvcc.Configure.Vectors.self_provided(
            name=vector_name,
            vector_index_config=wvcc.Configure.VectorIndex.hnsw(distance_metric=metric)),
        inverted_index_config=wvcc.Configure.inverted_index(),
        properties=CHUNK_PROPERTIES)


def drop_collection(client: WeaviateClient, name: str) -> None:
    """Drop a Weaviate collection if it exists."""
    if not client.collections.exists(name):
        logger.info("Collection %s does not exist; nothing to drop.", name)
        return
    client.collections.delete(name)
    logger.info("Dropped collection %s", name)
