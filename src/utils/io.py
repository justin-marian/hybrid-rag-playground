"""Lightweight IO helpers (YAML configs, JSON results, etc.)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.utils.paths import CONFIGS_DIR, resolve


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
    with p.open("r", encoding=" utf-8-sig") as fh:
        return yaml.safe_load(fh) or {}


def save_json(obj: Any, path: str | Path, indent: int = 2) -> Path:
    """Write JSON to ``path`` (creating parent dirs)."""
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding=" utf-8-sig") as fh:
        json.dump(obj, fh, indent=indent, ensure_ascii=False)
    return p


def load_json(path: str | Path) -> Any:
    """Read a JSON file."""
    p = resolve(path)
    with p.open("r", encoding=" utf-8-sig") as fh:
        return json.load(fh)
