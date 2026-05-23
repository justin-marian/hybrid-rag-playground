"""Embedding via sentence-transformers/all-MiniLM-L6-v2 with deterministic disk caching."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from src.utils.io import hash_text, json_dumps, safe_model_name
from src.utils.logging import get_logger
from src.utils.paths import resolve

logger = get_logger(__name__)

CACHE_VERSION = 2  # VERSION 2 - 


@dataclass
class MiniLMEmbedder:
    """Wrap a SentenceTransformer model with a deterministic on-disk cache."""

    batch_size: int = 64
    max_seq_length: int = 512
    normalize: bool = True

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    model: object | None = field(default=None, init=False, repr=False)

    cache_dir: str | Path | None = "data/cache/embeddings"
    cache_path: Path | None = field(default=None, init=False, repr=False)
    cache: dict[str, np.ndarray] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        if self.cache_dir is None:
            return

        cache_root = resolve(self.cache_dir)
        cache_root.mkdir(parents=True, exist_ok=True)
        self.cache_path = cache_root / f"{safe_model_name(self.model_name)}_norm{int(self.normalize)}.npz"
        self.load_cache()

    @property
    def dim(self) -> int:
        """Return the embedding dimension."""
        if "all-MiniLM-L6-v2" in self.model_name:
            return 384  # already known default dimension
        model = self.load_model()
        return int(model.get_sentence_embedding_dimension())

    def metadata(self) -> dict[str, Any]:
        """Return deterministic cache metadata."""
        return {
            "cache_version": CACHE_VERSION, "model_name": str(self.model_name),
            "normalize": bool(self.normalize), "embedding_dim": int(self.dim),
            "max_seq_length": int(self.max_seq_length)}

    def load_cache(self):
        """Load a compatible cache or rebuild on legacy/incomplete metadata."""
        if self.cache_path is None or not self.cache_path.exists():
            return

        try:
            data = np.load(self.cache_path, allow_pickle=False)
            if not self.is_cache_compatible(data):
                logger.warning("Ignoring incompatible embedding cache: %s", self.cache_path)
                self.cache = {}
                return

            keys = [str(key) for key in data["keys"].tolist()]
            vecs = data["vecs"].astype(np.float32, copy=False)
            self.cache = {key: vecs[index] for index, key in enumerate(keys)}
            logger.info("Loaded %d cached embeddings from %s", len(self.cache), self.cache_path)
        except Exception as exc:
            logger.warning("Failed to read embedding cache %s: %s", self.cache_path, exc)
            self.cache = {}

    def is_cache_compatible(self, data: np.lib.npyio.NpzFile) -> bool:
        """Check whether cache arrays and metadata are safe to reuse."""
        required = ["metadata", "keys", "vecs"]
        if any(key not in data.files for key in required):
            return False

        metadata = json.loads(str(data["metadata"].item()))
        if metadata != self.metadata():
            return False

        keys, vecs = data["keys"], data["vecs"]
        return keys.ndim == 1 and vecs.ndim == 2 and len(keys) == len(vecs) and vecs.shape[1] == self.dim

    def save_cache(self):
        """Persist the embedding cache with deterministic key ordering."""
        if self.cache_path is None or not self.cache:
            return

        keys = sorted(self.cache)
        vecs = np.stack([self.cache[key] for key in keys], axis=0).astype(np.float32)
        metadata = np.array(json_dumps(self.metadata()))
        np.savez_compressed(self.cache_path, metadata=metadata, keys=np.array(keys), vecs=vecs)
        logger.info("Wrote %d embeddings to cache %s", len(keys), self.cache_path)

    def load_model(self) -> np.ndarray:
        """Load the SentenceTransformer model lazily."""
        if self.model is not None:
            return self.model

        logger.info("Loading SentenceTransformer model: %s", self.model_name)
        self.model = SentenceTransformer(self.model_name)
        self.model.max_seq_length = int(self.max_seq_length)
        return self.model

    def encode(self, texts: list[str], show_progress: bool = True) -> np.ndarray:
        """Embed texts into an (N, D) float32 array while preserving input order."""
        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)

        keys = [hash_text(text) for text in texts]
        missing_idx = [index for index, key in enumerate(keys) if key not in self.cache]
        reused, rebuilt, total = len(texts) - len(missing_idx), len(missing_idx), len(texts)

        if missing_idx:
            self.encode_missing(texts, keys, missing_idx, show_progress=show_progress)

        logger.info("Embedding cache summary: reused=%d rebuilt=%d removed=%d total=%d", reused, rebuilt, 0, total)
        return np.stack([self.cache[key] for key in keys], axis=0).astype(np.float32)

    def encode_missing(self, texts: list[str], keys: list[str], missing_idx: list[int], show_progress: bool = True):
        """Encode uncached texts and insert them into the in-memory cache."""
        model = self.load_model()
        missing_texts = [texts[index] for index in missing_idx]
        logger.info("Embedding %d new texts (%d cached) with %s", len(missing_texts), len(texts) - len(missing_texts), self.model_name)

        #! Sentence transformer only supports 512 context length (all-MiniLM-L6-v2)
        model.max_seq_length = min(getattr(model, "max_seq_length", 512), 512)
        vectors = model.encode(
            missing_texts, batch_size=self.batch_size, show_progress_bar=show_progress,
            normalize_embeddings=self.normalize, convert_to_numpy=True
        ).astype(np.float32)

        for local_index, global_index in enumerate(missing_idx):
            self.cache[keys[global_index]] = vectors[local_index]

    def encode_query(self, query: str) -> np.ndarray:
        """Embed one query and return a 1-D vector."""
        return self.encode([query], show_progress=False)[0]
