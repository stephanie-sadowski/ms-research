"""Fetch paper citations from PubMed (NCBI E-utilities).

Run the myelin-repair preset:

    python -m msr.fetch.pubmed

This saves the full PubMed XML to data/raw/pubmed/ and writes
data/derived/pubmed_ms_remyelination.csv with citation details only
(PMID, title, journal, year, DOI, publication types, MeSH terms).

Abstracts stay in data/raw/ because publishers hold their copyright.

Set NCBI_API_KEY in your environment to allow 10 requests/second instead of 3.
"""

from __future__ import annotations

import argparse
import os
import xml.etree.ElementTree as ET
from typing import Any, Iterator

from ..http import MIN_INTERVAL, get_json, get_text
from ..paths import raw_dir
from ..provenance import write_derived_csv, write_manifest

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SOURCE_ID = "pubmed"

REPAIR_QUERY = '"multiple sclerosis"[MeSH] AND (remyelination[MeSH] OR remyelination[tiab])'

# esearch returns at most 9,999 IDs per query.
MAX_IDS = 9999
BATCH = 200

COLUMNS = ["pmid", "title", "journal", "year", "doi", "publication_types", "mesh_terms"]


def _key_params() -> dict[str, str]:
    key = os.environ.get("NCBI_API_KEY")
    if key:
        MIN_INTERVAL["eutils.ncbi.nlm.nih.gov"] = 0.11
        return {"api_key": key}
    return {}


def search_ids(term: str, use_cache: bool = True) -> tuple[list[str], int]:
    """Return (PMIDs, total count) for a PubMed query, newest first."""
    data = get_json(
        f"{EUTILS}/esearch.fcgi",
        {"db": "pubmed", "term": term, "retmax": MAX_IDS, "retmode": "json", "sort": "pub_date", **_key_params()},
        use_cache=use_cache,
    )
    result = data["esearchresult"]
    return result["idlist"], int(result["count"])


def fetch_xml(pmids: list[str], use_cache: bool = True) -> Iterator[str]:
    """Yield PubMed XML for the given PMIDs, BATCH at a time."""
    for start in range(0, len(pmids), BATCH):
        batch = pmids[start : start + BATCH]
        yield get_text(
            f"{EUTILS}/efetch.fcgi",
            {"db": "pubmed", "id": ",".join(batch), "retmode": "xml", **_key_params()},
            use_cache=use_cache,
        )


def _text(node: ET.Element | None) -> str:
    return "".join(node.itertext()).strip() if node is not None else ""


def _year(article: ET.Element) -> str:
    pub_date = article.find(".//Journal/JournalIssue/PubDate")
    if pub_date is None:
        return ""
    year = pub_date.findtext("Year")
    if year:
        return year
    # Some records only have a free-text date such as "2019 Nov-Dec".
    medline = pub_date.findtext("MedlineDate") or ""
    return medline[:4] if medline[:4].isdigit() else ""


def parse_articles(xml: str) -> list[dict[str, Any]]:
    """Parse efetch XML into citation rows (no abstracts)."""
    rows = []
    for art in ET.fromstring(xml).iter("PubmedArticle"):
        doi = next(
            (_text(i) for i in art.iterfind(".//PubmedData/ArticleIdList/ArticleId") if i.get("IdType") == "doi"),
            "",
        )
        rows.append(
            {
                "pmid": art.findtext(".//MedlineCitation/PMID"),
                "title": _text(art.find(".//Article/ArticleTitle")),
                "journal": art.findtext(".//Journal/ISOAbbreviation") or art.findtext(".//Journal/Title") or "",
                "year": _year(art),
                "doi": doi,
                "publication_types": "; ".join(_text(t) for t in art.iterfind(".//PublicationTypeList/PublicationType")),
                "mesh_terms": "; ".join(_text(m) for m in art.iterfind(".//MeshHeadingList/MeshHeading/DescriptorName")),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--query", default=REPAIR_QUERY, help="PubMed query (default: MS + remyelination)")
    parser.add_argument("--name", default="pubmed_ms_remyelination", help="output file name, without extension")
    parser.add_argument("--refresh", action="store_true", help="ignore the cache and re-download")
    args = parser.parse_args(argv)
    use_cache = not args.refresh

    pmids, total = search_ids(args.query, use_cache=use_cache)
    if total > len(pmids):
        print(f"Warning: {total} matches; only the newest {len(pmids)} are fetched. Narrow the query.")

    raw_path = raw_dir("pubmed") / f"{args.name}.xml"
    rows: list[dict[str, Any]] = []
    with open(raw_path, "w") as raw:
        for xml in fetch_xml(pmids, use_cache=use_cache):
            raw.write(xml)
            raw.write("\n")
            rows.extend(parse_articles(xml))
    write_manifest(raw_path, source="PubMed", query=args.query, total_matches=total, fetched=len(pmids))

    out = write_derived_csv(
        f"{args.name}.csv",
        rows,
        COLUMNS,
        source_id=SOURCE_ID,
        query={"api": f"{EUTILS}/esearch.fcgi", "term": args.query, "total_matches": total},
        notes="Citation details only; abstracts are left out because publishers hold their copyright.",
    )
    print(f"{len(rows)} papers (of {total} matches) -> {out}")


if __name__ == "__main__":
    main()
