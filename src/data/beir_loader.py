"""BEIR dataset loading.

Wraps the official ``beir`` package so the rest of the project deals with simple,
typed structures rather than raw dicts.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from beir import util as beir_util

from src.data.dataset_registry import DatasetSpec
from src.utils.io import load_jsonl
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
    download_root = Path(spec.download_root)
    ensure_dirs(download_root)

    target = download_root / spec.name
    if target.exists() and any(target.iterdir()):
        logger.info("BEIR dataset already on disk: %s", target)
        return target

    logger.info("Downloading BEIR dataset %s from %s", spec.name, spec.url)
    data_path = beir_util.download_and_unzip(spec.url, str(download_root))
    return Path(data_path)


def load_corpus(path: Path) -> dict[str, dict[str, str]]:
    """Load BEIR corpus.jsonl into a doc_id keyed dictionary."""
    corpus: dict[str, dict[str, str]] = {}
    for row in load_jsonl(path):
        doc_id = str(row.get("_id", ""))
        corpus[doc_id] = {
            "title": str(row.get("title", "")),
            "text": str(row.get("text", ""))}
    return corpus


def load_queries(path: Path) -> dict[str, str]:
    """Load BEIR queries.jsonl into a query_id keyed dictionary."""
    queries: dict[str, str] = {}
    for row in load_jsonl(path):
        query_id = str(row.get("_id", ""))
        queries[query_id] = str(row.get("text", ""))
    return queries


def load_qrels(path: Path) -> dict[str, dict[str, int]]:
    """Load BEIR qrels TSV into a query_id -> doc_id relevance dictionary."""
    qrels: dict[str, dict[str, int]] = {}
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file, delimiter="\t")

        for row in reader:
            if len(row) < 3 or row[0].lower() == "query-id":
                continue

            query_id, doc_id, score = row[0], row[1], row[2]
            qrels.setdefault(str(query_id), {})[str(doc_id)] = int(float(score))

    return qrels


def load_beir(spec: DatasetSpec) -> BeirDataset:
    """Download (if needed) and load a BEIR dataset."""
    data_path = download_dataset(spec)
    logger.info("Loading BEIR dataset %s (split=%s) from %s", spec.name, spec.split, data_path)

    corpus = load_corpus(data_path / "corpus.jsonl")
    queries = load_queries(data_path / "queries.jsonl")
    qrels = load_qrels(data_path / "qrels" / f"{spec.split}.tsv")

    logger.info("Loaded %s: %d docs, %d queries, %d qrels", spec.name, len(corpus), len(queries), len(qrels))
    return BeirDataset(spec=spec, corpus=corpus, queries=queries, qrels=qrels)
