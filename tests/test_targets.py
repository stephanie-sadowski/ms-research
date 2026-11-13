import io
import json
import zipfile

import pytest

from msr.analysis import targets as t
from msr.fetch import hpa, opentargets, pubtator
from msr.provenance import LicenseError, write_derived_csv


def cand(symbol, papers=0, background=0, opc=0.0, oligo=0.0, spec=1.0, drug=0):
    return t.Candidate(symbol=symbol, ensembl=f"ENSG_{symbol}", papers=papers, background=background,
                       opc_ncpm=opc, oligo_ncpm=oligo, specificity=spec, druggability=drug)


def test_percentiles():
    assert t.percentiles([1, 2, 3, 4]) == [0.25, 0.5, 0.75, 1.0]
    assert t.percentiles([5, 5]) == [1.0, 1.0]
    assert t.percentiles([]) == []


def test_enrichment_penalises_popular_genes():
    niche = cand("NICHE", papers=20, background=200)
    popular = cand("POPULAR", papers=20, background=50000)
    assert niche.enrichment > popular.enrichment


def test_scoring_orders_strong_evidence_first():
    strong = cand("STRONG", papers=50, background=500, opc=200, spec=10, drug=3)
    weak = cand("WEAK", papers=1, background=50000, opc=1, spec=0.5, drug=0)
    middle = cand("MID", papers=10, background=5000, opc=50, spec=2, drug=1)
    cands = [weak, middle, strong]
    t.score(cands)
    assert [c.symbol for c in t.rank(cands)] == ["STRONG", "MID", "WEAK"]
    assert set(strong.scores) == {"literature", "expression", "druggability", "overall"}
    assert strong.scores["overall"] == pytest.approx(1.0)


def test_known_answer_report_counts_pairs():
    ranked = [cand(s) for s in ["CHRM1", "LINGO1", "RXRG", "HRH3", "RGMA"]]
    report = "\n".join(t.known_answer_report(ranked))
    # CHRM1(1) beats LINGO1(2) and RGMA(5); RXRG(3), HRH3(4) beat RGMA only -> 4 of 6.
    assert "in 4 of 6 pairs" in report
    assert "CHRM1   positive rank     1 of 5" in report


def test_trial_evidence_is_not_in_the_score():
    a = cand("CHRM1", papers=5, background=1000, opc=10, spec=1, drug=3)
    b = cand("OTHER1", papers=5, background=1000, opc=10, spec=1, drug=3)
    t.score([a, b])
    assert a.scores == b.scores


def test_druggability_levels():
    assert opentargets.TargetInfo("e", "s").druggability == 0
    assert opentargets.TargetInfo("e", "s", small_molecule_tractable=True).druggability == 1
    assert opentargets.TargetInfo("e", "s", clinical_drugs=["X"]).druggability == 2
    assert opentargets.TargetInfo("e", "s", approved_drugs=["X"], clinical_drugs=["X"]).druggability == 3


def _zip(path, name, text):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(name, text)


def test_hpa_load(tmp_repo, monkeypatch):
    folder = tmp_repo / "data" / "raw" / "hpa"
    folder.mkdir(parents=True)
    _zip(folder / "proteinatlas.tsv.zip", "proteinatlas.tsv",
         "Gene\tEnsembl\tUniprot\tProtein class\nOLIG2\tENSG1\tQ1\tTranscription factors\n")
    _zip(folder / "rna_single_nuclei_cluster_type.tsv.zip", "x.tsv",
         "Gene\tGene name\tCluster type\tnCPM\n"
         "ENSG1\tOLIG2\toligodendrocyte progenitor cells\t280\n"
         "ENSG1\tOLIG2\toligodendrocytes\t40\n"
         "ENSG1\tOLIG2\tastrocytes\t9\n")
    monkeypatch.setattr(hpa, "download", lambda url, dest, refresh=False: dest)
    genes = hpa.load()
    g = genes["ENSG1"]
    assert (g.symbol, g.uniprot, g.opc_ncpm, g.oligo_ncpm, g.max_other_type) == ("OLIG2", "Q1", 280, 40, "astrocytes")
    assert g.lineage_specificity == pytest.approx(281 / 10)


def test_pubtator_gene_mentions(monkeypatch):
    doc = {"PubTator3": [{"id": 1, "passages": [{"annotations": [
        {"infons": {"type": "Gene", "identifier": "1128"}},
        {"infons": {"type": "Gene", "identifier": "12669;1128"}},
        {"infons": {"type": "Chemical", "identifier": "MESH:D1"}},
        {"infons": {"type": "Gene", "identifier": None}},
    ]}]}]}
    monkeypatch.setattr(pubtator, "get_json", lambda url, params, use_cache=True: doc)
    assert pubtator.gene_mentions(["1"]) == {"1": {"1128", "12669"}}


def test_multi_source_tables_check_every_source(tmp_repo):
    path = write_derived_csv("ok.csv", [{"a": 1}], ["a"], source_id=["open-targets", "chembl"], query={})
    manifest = json.loads(path.with_name("ok.csv.manifest.json").read_text())
    assert [s["id"] for s in manifest["sources"]] == ["open-targets", "chembl"]
    with pytest.raises(LicenseError):
        write_derived_csv("bad.csv", [], ["a"], source_id=["open-targets", "gbd-results"], query={})
