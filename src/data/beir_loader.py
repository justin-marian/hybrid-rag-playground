"""BEIR dataset loading.

Wraps the official ``beir`` package so the rest of the project deals with simple,
typed structures rather than raw dicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.dataset_registry import DatasetSpec
from src.utils.logging import get_logger
from src.utils.paths import ensure_dirs

logger = get_logger(__name__)


@dataclass
class BeirDataset:
    """Container for a loaded BEIR dataset."""

    spec: DatasetSpec
    corpus: dict[str, dict[str, str]]   # doc_id -> {"title": ..., "text": ...}
    queries: dict[str, str]             # query_id -> text
    qrels: dict[str, dict[str, int]]    # query_id -> {doc_id: relevance}

    @property
    def num_docs(self) -> int:
        return len(self.corpus)

    @property
    def num_queries(self) -> int:
        return len(self.queries)


def download_dataset(spec: DatasetSpec) -> Path:
    """Download (if needed) the BEIR archive and return the extracted folder path."""
    from beir import util as beir_util  # imported lazily to keep import cost low

    download_root = Path(spec.download_root)
    ensure_dirs(download_root)

    target = download_root / spec.name
    if target.exists() and any(target.iterdir()):
        logger.info("BEIR dataset already on disk: %s", target)
        return target

    logger.info("Downloading BEIR dataset %s from %s", spec.name, spec.url)
    data_path = beir_util.download_and_unzip(spec.url, str(download_root))
    return Path(data_path)


def load_beir(spec: DatasetSpec) -> BeirDataset:
    """Download (if needed) and load a BEIR dataset."""
    from beir.datasets.data_loader import GenericDataLoader

    data_path = download_dataset(spec)
    logger.info("Loading BEIR dataset %s (split=%s) from %s", spec.name, spec.split, data_path)
    corpus, queries, qrels = GenericDataLoader(data_folder=str(data_path)).load(split=spec.split)
    logger.info(
        "Loaded %s: %d docs, %d queries, %d qrels",
        spec.name,
        len(corpus),
        len(queries),
        len(qrels),
    )
    return BeirDataset(spec=spec, corpus=corpus, queries=queries, qrels=qrels)
