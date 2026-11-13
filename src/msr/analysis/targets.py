"""Track C (first version): rank genes as possible myelin-repair targets.

    python -m msr.analysis.targets

Each gene gets three evidence scores, each a percentile from 0 to 1 within the
candidate genes:

- literature: how often the gene appears in papers on remyelination and OPC
  maturation (PubTator gene tags), and how specific that is compared with
  how often the gene appears in PubMed overall.
- expression: how strongly the gene is expressed in OPCs or oligodendrocytes in
  the human brain (Human Protein Atlas), and how specific it is to that lineage.
- druggability: whether drugs exist for it (Open Targets), from "approved drug"
  down to "tractable".

The overall score is a weighted mean. Human trial results from Track A are NOT
used in the score; they are kept separate so they can check the ranking.

Outputs (data/derived/):
- targets_repair.csv: every candidate gene with its evidence and scores
- targets_repair_drugs.csv: for the top genes, known drugs and how they act (ChEMBL)
"""

from __future__ import annotations

import argparse
import csv
import math
from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Any

from ..fetch import chembl, hpa, opentargets, pubmed, pubtator
from ..paths import derived_dir
from ..provenance import write_derived_csv

REPAIR_CORPUS = (
    'remyelination[tiab] OR "oligodendrocyte differentiation"[tiab] OR "oligodendrocyte precursor"[tiab] '
    'OR "oligodendrocyte progenitor"[tiab] OR "myelin repair"[tiab]'
)
WEIGHTS = {"literature": 0.4, "expression": 0.3, "druggability": 0.3}

# Which genes enter the ranking.
MIN_PAPERS = 3            # mentioned in at least this many repair papers, or
MIN_LINEAGE_NCPM = 20.0   # clearly expressed in OPCs/oligodendrocytes and
MIN_SPECIFICITY = 2.0     # at least 2x higher there than in any other brain cell type

# Known answers from human trials (Track A), used only to check the ranking.
# "positive" = met or partly met a repair endpoint in people;
# "negative" = worked in animals but missed in human trials.
KNOWN = {
    "CHRM1": "positive",  # clemastine (ReBUILD), PIPE-307
    "RXRG": "positive",   # bexarotene (CCMR-One, partial)
    "HRH3": "positive",   # GSK239512 (partial)
    "LINGO1": "negative", # opicinumab
    "RGMA": "negative",   # elezanumab
}

TOP_FOR_DRUGS = 50


@dataclass
class Candidate:
    symbol: str
    ensembl: str
    uniprot: str = ""
    protein_class: str = ""
    papers: int = 0
    background: int = 0
    opc_ncpm: float = 0.0
    oligo_ncpm: float = 0.0
    specificity: float = 0.0
    top_other_cell_type: str = ""
    druggability: int = 0
    approved_drugs: list[str] = field(default_factory=list)
    clinical_drugs: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def enrichment(self) -> float:
        """Repair papers per 1,000 papers about the gene, with smoothing for rare genes."""
        return 1000 * (self.papers + 1) / (self.background + 100)


def percentiles(values: list[float]) -> list[float]:
    """Percentile rank of each value (0 = lowest, 1 = highest; ties share the higher rank)."""
    ordered = sorted(values)
    n = len(values)
    return [bisect_right(ordered, v) / n if n else 0.0 for v in values]


def score(cands: list[Candidate]) -> None:
    """Fill in each candidate's component and overall scores."""
    lit_volume = percentiles([math.log1p(c.papers) for c in cands])
    lit_specific = percentiles([c.enrichment for c in cands])
    expr_level = percentiles([math.log1p(max(c.opc_ncpm, c.oligo_ncpm)) for c in cands])
    expr_specific = percentiles([c.specificity for c in cands])
    drug = [c.druggability / 3 for c in cands]
    for i, c in enumerate(cands):
        c.scores = {
            "literature": (lit_volume[i] + lit_specific[i]) / 2,
            "expression": (expr_level[i] + expr_specific[i]) / 2,
            "druggability": drug[i],
        }
        c.scores["overall"] = sum(WEIGHTS[k] * c.scores[k] for k in WEIGHTS)


def rank(cands: list[Candidate]) -> list[Candidate]:
    return sorted(cands, key=lambda c: (-c.scores["overall"], c.symbol))


def known_answer_report(ranked: list[Candidate]) -> list[str]:
    """How the trial-backed genes rank. A useful ranking puts positives above negatives."""
    position = {c.symbol: i + 1 for i, c in enumerate(ranked)}
    total = len(ranked)
    lines = []
    for symbol, label in KNOWN.items():
        if symbol in position:
            p = position[symbol]
            lines.append(f"  {symbol:7s} {label:8s} rank {p:5d} of {total} (top {100 * p / total:.0f}%)")
        else:
            lines.append(f"  {symbol:7s} {label:8s} not in the candidate list")
    pos = [position[s] for s, l in KNOWN.items() if l == "positive" and s in position]
    neg = [position[s] for s, l in KNOWN.items() if l == "negative" and s in position]
    if pos and neg:
        pairs = [(p, n) for p in pos for n in neg]
        won = sum(p < n for p, n in pairs)
        lines.append(f"  Positives ranked above negatives in {won} of {len(pairs)} pairs")
    return lines


def build(use_cache: bool = True) -> list[Candidate]:
    expression = hpa.load()
    by_symbol = {e.symbol.upper(): e for e in expression.values()}

    pmids = sorted(set(pubmed.search_all_ids(REPAIR_CORPUS, use_cache=use_cache)))
    papers = pubtator.papers_per_human_symbol(pmids, use_cache=use_cache)

    chosen: dict[str, hpa.GeneExpression] = {}
    for symbol, e in by_symbol.items():
        enough_papers = len(papers.get(symbol, ())) >= MIN_PAPERS
        lineage = e.lineage_ncpm >= MIN_LINEAGE_NCPM and e.lineage_specificity >= MIN_SPECIFICITY
        if enough_papers or lineage or symbol in KNOWN:
            chosen[symbol] = e

    targets = opentargets.fetch_targets([e.ensembl for e in chosen.values()], use_cache=use_cache)
    cands = []
    for symbol, e in chosen.items():
        t = targets.get(e.ensembl)
        cands.append(
            Candidate(
                symbol=e.symbol,
                ensembl=e.ensembl,
                uniprot=e.uniprot,
                protein_class=e.protein_class,
                papers=len(papers.get(symbol, ())),
                background=pubtator.background_count(e.symbol, use_cache=use_cache),
                opc_ncpm=e.opc_ncpm,
                oligo_ncpm=e.oligo_ncpm,
                specificity=round(e.lineage_specificity, 2),
                top_other_cell_type=e.max_other_type,
                druggability=t.druggability if t else 0,
                approved_drugs=t.approved_drugs if t else [],
                clinical_drugs=t.clinical_drugs if t else [],
            )
        )
    score(cands)
    return rank(cands)


def drug_rows(ranked: list[Candidate], top: int, use_cache: bool = True) -> list[dict[str, Any]]:
    rows = []
    for i, c in enumerate(ranked[:top], start=1):
        if not c.uniprot or c.druggability < 2:
            continue
        accession = c.uniprot.split(",")[0].strip()
        seen = set()
        for m in chembl.mechanisms_for_uniprot(accession, use_cache=use_cache):
            key = (m.molecule_chembl_id, m.action_type)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "rank": i,
                    "gene": c.symbol,
                    "drug": m.drug_name,
                    "chembl_id": m.molecule_chembl_id,
                    "action_type": m.action_type,
                    "mechanism": m.mechanism,
                    "max_phase": m.max_phase,
                }
            )
    return rows


COLUMNS = [
    "rank", "gene", "ensembl", "overall", "literature", "expression", "druggability",
    "repair_papers", "all_papers", "repair_per_1000", "opc_ncpm", "oligo_ncpm",
    "lineage_specificity", "top_other_cell_type", "druggability_level",
    "approved_drugs", "clinical_drugs", "human_trial_evidence", "protein_class",
]


def to_rows(ranked: list[Candidate]) -> list[dict[str, Any]]:
    levels = {0: "none known", 1: "tractable", 2: "clinical-stage drugs", 3: "approved drugs"}
    return [
        {
            "rank": i,
            "gene": c.symbol,
            "ensembl": c.ensembl,
            "overall": round(c.scores["overall"], 3),
            "literature": round(c.scores["literature"], 3),
            "expression": round(c.scores["expression"], 3),
            "druggability": round(c.scores["druggability"], 3),
            "repair_papers": c.papers,
            "all_papers": c.background,
            "repair_per_1000": round(c.enrichment, 1),
            "opc_ncpm": c.opc_ncpm,
            "oligo_ncpm": c.oligo_ncpm,
            "lineage_specificity": c.specificity,
            "top_other_cell_type": c.top_other_cell_type,
            "druggability_level": levels[c.druggability],
            "approved_drugs": "; ".join(c.approved_drugs[:15]),
            "clinical_drugs": len(c.clinical_drugs),
            "human_trial_evidence": KNOWN.get(c.symbol, ""),
            "protein_class": c.protein_class,
        }
        for i, c in enumerate(ranked, start=1)
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true", help="ignore the cache and re-download")
    args = parser.parse_args(argv)
    use_cache = not args.refresh

    ranked = build(use_cache=use_cache)
    query = {
        "repair_corpus": REPAIR_CORPUS,
        "weights": WEIGHTS,
        "candidate_rules": {"min_papers": MIN_PAPERS, "min_lineage_ncpm": MIN_LINEAGE_NCPM,
                            "min_specificity": MIN_SPECIFICITY},
        "hpa_files": [hpa.GENES_URL, hpa.CELL_TYPES_URL],
    }
    out = write_derived_csv(
        "targets_repair.csv",
        to_rows(ranked),
        COLUMNS,
        source_id=["human-protein-atlas", "open-targets", "pubtator", "chembl"],
        query=query,
        notes=(
            "First-pass ranking of possible myelin-repair targets. Scores are percentiles within the "
            "candidate genes. Human trial evidence is shown for checking only and is not part of the score. "
            "Drug lists come from Open Targets, which takes them from ChEMBL (CC BY-SA 3.0), so this table "
            "is shared under CC BY-SA 3.0. Expression data: Human Protein Atlas v26.0 (proteinatlas.org), CC BY 4.0."
        ),
    )
    drugs = write_derived_csv(
        "targets_repair_drugs.csv",
        drug_rows(ranked, TOP_FOR_DRUGS, use_cache=use_cache),
        ["rank", "gene", "drug", "chembl_id", "action_type", "mechanism", "max_phase"],
        source_id="chembl",
        query={"top_genes": TOP_FOR_DRUGS, "api": chembl.API},
        notes="Drugs acting on the top-ranked genes, with direction (action_type). CC BY-SA 3.0, from ChEMBL.",
    )

    print(f"{len(ranked)} candidate genes")
    print("\nTop 30:")
    for i, c in enumerate(ranked[:30], start=1):
        s = c.scores
        print(f"  {i:3d} {c.symbol:9s} overall {s['overall']:.2f}  lit {s['literature']:.2f}  "
              f"expr {s['expression']:.2f}  drug {s['druggability']:.2f}  papers {c.papers}")
    print("\nKnown-answer check:")
    print("\n".join(known_answer_report(ranked)))
    print(f"\n-> {out}\n-> {drugs}")


if __name__ == "__main__":
    main()
