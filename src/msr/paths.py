"""Standard locations inside the repo."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """Return the repo root (the folder holding pyproject.toml).

    Set MSR_ROOT to override, for example in tests.
    """
    override = os.environ.get("MSR_ROOT")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def raw_dir(source: str) -> Path:
    """Folder for raw downloads from one source. Gitignored; never committed."""
    path = repo_root() / "data" / "raw" / source
    path.mkdir(parents=True, exist_ok=True)
    return path


def derived_dir() -> Path:
    """Folder for small derived tables that may be committed."""
    path = repo_root() / "data" / "derived"
    path.mkdir(parents=True, exist_ok=True)
    return path


def catalog_path() -> Path:
    return repo_root() / "catalog" / "sources.csv"
