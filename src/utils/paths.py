"""Project path resolution helpers.

All paths are computed relative to the repository root so the code runs
identically on any machine, in Docker, or in CI.
"""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Return the repository root (directory that contains pyproject.toml).

    Walks up from this file until ``pyproject.toml`` is found. Falls back to
    three parents up if not found (defensive).
    """
    here = Path(__file__).resolve()
    return next((parent for parent in [here.parent, *here.parents] if (parent / "pyproject.toml").exists()), here.parents[2])


ROOT = project_root()

CONFIGS_DIR = ROOT / "configs"
DATA_DIR = ROOT / "data"
BEIR_DIR = DATA_DIR / "beir"
RESULTS_DIR = DATA_DIR / "results"
CACHE_DIR = DATA_DIR / "cache"
IMAGES_DIR = ROOT / "images"
DOCS_DIR = ROOT / "docs"


def ensure_dirs(*paths: Path):
    """Create directories if they don't already exist."""
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def resolve(rel_path: str | Path) -> Path:
    """Resolve a string/Path against the project root if not absolute."""
    p = Path(rel_path)
    return p if p.is_absolute() else ROOT / p
