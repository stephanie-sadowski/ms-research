"""Count genes mentioned in a set of papers, using NCBI PubTator3 annotations.

PubTator tags genes with standard NCBI Gene IDs, so ambiguous symbols (for
example "AR" or "ID2") are resolved. Mouse and rat gene IDs are mapped to human
by symbol (upper-cased), which works for most genes but not all.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Iterable

from ..http import get_json
from ..paths import raw_dir

API = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson"
GENE_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
BATCH = 100


def gene_mentions(pmids: list[str], use_cache: bool = True) -> dict[str, set[str]]:
    """Return {pmid: set of NCBI Gene IDs mentioned in its title or abstract}."""
    out: dict[str, set[str]] = {}
    for start in range(0, len(pmids), BATCH):
        batch = pmids[start : start + BATCH]
        data = get_json(API, {"pmids": ",".join(batch)}, use_cache=use_cache)
        for doc in data.get("PubTator3", []):
            genes = out.setdefault(str(doc["id"]), set())
            for passage in doc.get("passages", []):
                for ann in passage.get("annotations", []):
                    info = ann.get("infons", {})
                    if info.get("type") != "Gene":
                        continue
                    # Some annotations list several IDs separated by ";".
                    for gene_id in str(info.get("identifier") or "").split(";"):
                        if gene_id.strip().isdigit():
                            genes.add(gene_id.strip())
    return out


def gene_symbols(gene_ids: Iterable[str], use_cache: bool = True) -> dict[str, tuple[str, str]]:
    """Return {NCBI Gene ID: (symbol, organism)}."""
    ids = sorted(set(gene_ids), key=int)
    out: dict[str, tuple[str, str]] = {}
    for start in range(0, len(ids), 200):
        batch = ids[start : start + 200]
        data = get_json(GENE_SUMMARY, {"db": "gene", "id": ",".join(batch), "retmode": "json"}, use_cache=use_cache)
        result = data.get("result", {})
        for gid in result.get("uids", []):
            rec = result[gid]
            out[gid] = (rec.get("name", ""), rec.get("organism", {}).get("scientificname", ""))
    return out


SEARCH = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/search/"


def background_count(symbol: str, use_cache: bool = True) -> int:
    """Number of PubMed papers PubTator tags with this gene symbol (any species), as a popularity baseline."""
    data = get_json(SEARCH, {"text": f"@GENE_{symbol}", "page": 1}, use_cache=use_cache)
    return int(data.get("count") or 0)


def papers_per_human_symbol(pmids: list[str], use_cache: bool = True) -> dict[str, set[str]]:
    """Return {upper-case gene symbol: set of PMIDs mentioning it} for human, mouse and rat genes."""
    mentions = gene_mentions(pmids, use_cache=use_cache)
    symbols = gene_symbols({g for genes in mentions.values() for g in genes}, use_cache=use_cache)
    keep = {"Homo sapiens", "Mus musculus", "Rattus norvegicus"}
    papers: dict[str, set[str]] = defaultdict(set)
    for pmid, genes in mentions.items():
        for gid in genes:
            symbol, organism = symbols.get(gid, ("", ""))
            if symbol and organism in keep:
                papers[symbol.upper()].add(pmid)

    raw = raw_dir("pubtator") / "gene_mentions.json"
    raw.write_text(json.dumps({p: sorted(g) for p, g in mentions.items()}))
    return dict(papers)
