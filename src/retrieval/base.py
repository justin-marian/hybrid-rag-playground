"""Common retriever result types and base conversion helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievedHit:
    """One ranked retrieval result."""

    chunk_id: str
    doc_id: str
    text: str
    title: str
    score: float
    rank: int


class Retriever(ABC):
    """Abstract retriever over one Weaviate collection."""

    name: str = "base"

    def __init__(self, client: Any, collection_name: str) -> None:
        self.client = client
        self.collection_name = collection_name
        self.collection = client.collections.get(collection_name)

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> list[RetrievedHit]:
        """Return up to ``top_k`` hits sorted by descending score."""
        raise NotImplementedError

    @staticmethod
    def metadata_score(metadata: Any | None) -> float:
        """Extract a comparable score from Weaviate metadata."""
        if metadata is None:
            return 0.0

        score = getattr(metadata, "score", None)
        if score is not None:
            return float(score)

        distance = getattr(metadata, "distance", None)
        return float(1.0 - distance) if distance is not None else 0.0

    @classmethod
    def object_to_hit(cls, obj: Any, rank: int) -> RetrievedHit:
        """Convert one Weaviate object into a ranked hit."""
        props = obj.properties or {}
        return RetrievedHit(
            chunk_id=str(props.get("chunk_id", "")),  doc_id=str(props.get("doc_id", "")),
            title=str(props.get("title", "")), text=str(props.get("text", "")), 
            score=cls.metadata_score(getattr(obj, "metadata", None)), rank=rank)

    @classmethod
    def objects_to_hits(cls, objects: Any) -> list[RetrievedHit]:
        """Convert Weaviate query objects into ``RetrievedHit`` rows."""
        return [cls.object_to_hit(obj, rank) for rank, obj in enumerate(objects, start=1)]
