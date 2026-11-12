"""Record where data came from, and check licenses before writing shareable tables."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import __version__
from .paths import catalog_path, derived_dir

# Values of the catalog's `redistribution` column that allow a derived table
# to be written to data/derived/ (and so committed to this public repo).
SHAREABLE = {"yes", "conditional"}


class LicenseError(RuntimeError):
    """Raised when a source's terms don't allow sharing derived data."""


def catalog_entry(source_id: str) -> dict[str, str]:
    with open(catalog_path(), newline="") as f:
        for row in csv.DictReader(f):
            if row["id"] == source_id:
                return row
    raise KeyError(f"{source_id!r} is not in catalog/sources.csv")


def check_shareable(source_id: str) -> dict[str, str]:
    """Return the catalog entry, or raise if the source may not be shared."""
    entry = catalog_entry(source_id)
    if entry["access"] == "controlled":
        raise LicenseError(f"{source_id} is access-controlled; its data never goes in this repo")
    if entry["redistribution"] not in SHAREABLE:
        raise LicenseError(
            f"{source_id} has redistribution={entry['redistribution']!r}; "
            "derived tables can't be written to data/derived/"
        )
    return entry


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_manifest(path: Path, **fields: Any) -> Path:
    """Write <path>.manifest.json describing how a file was made."""
    manifest = {"file": path.name, "created": now_utc(), "msr_version": __version__, **fields}
    target = path.with_name(path.name + ".manifest.json")
    target.write_text(json.dumps(manifest, indent=2) + "\n")
    return target


def write_derived_csv(
    name: str,
    rows: Iterable[dict[str, Any]],
    columns: list[str],
    *,
    source_id: str,
    query: dict[str, Any],
    notes: str = "",
) -> Path:
    """Write a shareable table to data/derived/ with its manifest.

    Refuses to write if the catalog says the source can't be shared.
    """
    entry = check_shareable(source_id)
    path = derived_dir() / name
    rows = list(rows)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    write_manifest(
        path,
        source=entry["name"],
        source_id=source_id,
        source_url=entry["url"],
        license=entry["license"],
        terms_url=entry["terms_url"],
        query=query,
        rows=len(rows),
        notes=notes,
    )
    return path
