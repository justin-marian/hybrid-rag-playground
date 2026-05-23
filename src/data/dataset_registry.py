"""Typed access to the dataset registry defined in ``configs/datasets.yaml``."""

from __future__ import annotations

from dataclasses import dataclass

from src.utils.io import load_yaml
from src.utils.paths import resolve


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    name: str
    split: str
    description: str
    expected_size: int
    url: str
    download_root: str

    @property
    def collection_safe_name(self) -> str:
        """Return a string safe to use as a Weaviate collection name."""
        return self.name.replace("-", "_").lower()


def load_datasets(config_path: str = "datasets.yaml") -> dict[str, DatasetSpec]:
    """Parse ``configs/datasets.yaml`` and return a dict of dataset key -> spec."""
    raw = load_yaml(config_path)
    url_template = raw["url_template"]
    download_root = raw["download_root"]

    out: dict[str, DatasetSpec] = {}
    for key, entry in raw["datasets"].items():
        name = entry["name"]
        out[key] = DatasetSpec(
            key=key, name=name,
            split=entry.get("split", "test"),
            description=entry.get("description", ""),
            expected_size=int(entry.get("expected_size", 0)),
            url=url_template.format(name=name),
            download_root=str(resolve(download_root)))
    return out


def get_spec(key: str, config_path: str = "datasets.yaml") -> DatasetSpec:
    """Convenience accessor for a single dataset."""
    reg = load_datasets(config_path)
    if key not in reg:
        raise KeyError(f"Unknown dataset key: {key!r}. Known: {list(reg)}")
    return reg[key]
