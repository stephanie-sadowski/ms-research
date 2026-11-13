"""Human Protein Atlas: gene expression in brain cell types (single-nucleus RNA).

Downloads two files into data/raw/hpa/:
- proteinatlas.tsv.zip: one row per gene (Ensembl ID, symbol, UniProt, classes)
- rna_single_nuclei_cluster_type.tsv.zip: expression (nCPM) of every gene in
  every brain cell type, including oligodendrocyte progenitor cells (OPCs) and
  oligodendrocytes

License: CC BY 4.0. Cite a primary HPA publication, proteinatlas.org and the
version (see https://www.proteinatlas.org/about/licence).
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ..http import download
from ..paths import raw_dir

BASE = "https://www.proteinatlas.org/download"
GENES_URL = f"{BASE}/proteinatlas.tsv.zip"
CELL_TYPES_URL = f"{BASE}/tsv/rna_single_nuclei_cluster_type.tsv.zip"

OPC = "oligodendrocyte progenitor cells"
OLIGO = "oligodendrocytes"


@dataclass
class GeneExpression:
    ensembl: str
    symbol: str
    uniprot: str
    protein_class: str
    opc_ncpm: float
    oligo_ncpm: float
    max_other_ncpm: float
    max_other_type: str

    @property
    def lineage_ncpm(self) -> float:
        """Highest expression in the oligodendrocyte lineage (OPC or mature)."""
        return max(self.opc_ncpm, self.oligo_ncpm)

    @property
    def lineage_specificity(self) -> float:
        """Lineage expression relative to the highest other brain cell type (>1 = lineage-enriched)."""
        return (self.lineage_ncpm + 1) / (self.max_other_ncpm + 1)


def fetch(refresh: bool = False) -> tuple[Path, Path]:
    folder = raw_dir("hpa")
    genes = download(GENES_URL, folder / "proteinatlas.tsv.zip", refresh=refresh)
    cells = download(CELL_TYPES_URL, folder / "rna_single_nuclei_cluster_type.tsv.zip", refresh=refresh)
    return genes, cells


def _read_zipped_tsv(path: Path):
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")


def load(refresh: bool = False) -> dict[str, GeneExpression]:
    """Return expression per gene, keyed by Ensembl ID."""
    genes_path, cells_path = fetch(refresh)
    info = {
        row["Ensembl"]: (row["Gene"], row["Uniprot"], row["Protein class"])
        for row in _read_zipped_tsv(genes_path)
    }
    per_gene: dict[str, dict[str, float]] = {}
    symbols: dict[str, str] = {}
    for row in _read_zipped_tsv(cells_path):
        per_gene.setdefault(row["Gene"], {})[row["Cluster type"]] = float(row["nCPM"] or 0)
        symbols[row["Gene"]] = row["Gene name"]

    out = {}
    for ensembl, types in per_gene.items():
        others = {k: v for k, v in types.items() if k not in (OPC, OLIGO)}
        other_type, other_max = max(others.items(), key=lambda kv: kv[1]) if others else ("", 0.0)
        symbol, uniprot, protein_class = info.get(ensembl, (symbols[ensembl], "", ""))
        out[ensembl] = GeneExpression(
            ensembl=ensembl,
            symbol=symbol,
            uniprot=uniprot,
            protein_class=protein_class,
            opc_ncpm=types.get(OPC, 0.0),
            oligo_ncpm=types.get(OLIGO, 0.0),
            max_other_ncpm=other_max,
            max_other_type=other_type,
        )
    return out
