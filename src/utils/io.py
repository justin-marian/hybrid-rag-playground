"""Lightweight IO helpers (YAML configs, JSON results, etc.)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.utils.logging import get_logger
from src.utils.paths import CONFIGS_DIR, resolve

logger = get_logger(__name__)


def read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file as a dictionary."""
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file. Accepts an absolute path, a project-relative path,
    or a bare filename to be looked up under ``configs/``."""
    p = Path(path)
    if not p.exists():
        # Try resolving relative to project root.
        candidate = resolve(path)
        if candidate.exists():
            p = candidate
        else:
            # Try as a name inside configs/.
            candidate = CONFIGS_DIR / p.name
            if candidate.exists():
                p = candidate
            else:
                raise FileNotFoundError(f"Could not locate YAML file: {path}")
    with p.open("r", encoding=" utf-8") as fh:
        return yaml.safe_load(fh) or {}


def save_json(obj: Any, path: str | Path, indent: int = 2) -> Path:
    """Write JSON to ``path`` (creating parent dirs)."""
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding=" utf-8") as fh:
        json.dump(obj, fh, indent=indent, ensure_ascii=False)
    return p


def load_json(path: str | Path) -> Any:
    """Read a JSON file."""
    p = resolve(path)
    with p.open("r", encoding=" utf-8") as fh:
        return json.load(fh)


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file using an explicit context manager."""
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line := line.strip():
                rows.append(json.loads(line))
    return rows


def hash_text(text: str) -> str:
    """Return a deterministic SHA1 hash for one text."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def safe_model_name(model_name: str) -> str:
    """Return a filesystem-safe model name."""
    return model_name.replace("/", "_")


def json_dumps(data: dict[str, Any]) -> str:
    """Serialize metadata deterministically."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def path_or_default(value: str | None, default: Path) -> Path:
    """Resolve a user-provided path or return the default path."""
    return resolve(value) if value else default


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    """Read a CSV file if it exists, otherwise return an empty DataFrame."""
    if not path.exists() or not path.is_file():
        logger.warning("Missing CSV artifact: %s", path)
        return pd.DataFrame()
    return pd.read_csv(path)


def read_json_if_exists(path: Path) -> Any:
    """Read a JSON file if it exists, otherwise return an empty list."""
    if not path.exists() or not path.is_file():
        logger.warning("Missing JSON artifact: %s", path)
        return []
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
