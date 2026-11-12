import json

from msr.fetch import clinicaltrials, pubmed


def test_flatten_trial(fixture_text):
    row = clinicaltrials.flatten(json.loads(fixture_text("ctgov_study.json")))
    assert row["nct_id"] == "NCT00000001"
    assert row["status"] == "TERMINATED"
    assert row["why_stopped"] == "Safety stopping criteria met"
    assert row["phases"] == "PHASE1; PHASE2"
    assert row["enrollment"] == 50
    assert row["interventions"] == "Clemastine; Placebo; MRI"
    assert row["intervention_types"] == "DIAGNOSTIC_TEST; DRUG"
    assert row["primary_outcomes"] == "VEP P100 latency"
    assert row["reference_pmids"] == "29029896"
    assert row["has_results"] is True


def test_flatten_handles_missing_sections():
    row = clinicaltrials.flatten({"protocolSection": {"identificationModule": {"nctId": "NCT1"}}})
    assert row["nct_id"] == "NCT1"
    assert row["interventions"] == ""
    assert row["has_results"] is False


def test_search_follows_pages(monkeypatch):
    pages = [
        {"studies": [{"id": 1}], "nextPageToken": "abc"},
        {"studies": [{"id": 2}]},
    ]
    seen_params = []

    def fake_get_json(url, params, use_cache=True):
        seen_params.append(dict(params))
        return pages[len(seen_params) - 1]

    monkeypatch.setattr(clinicaltrials, "get_json", fake_get_json)
    studies = list(clinicaltrials.search_studies(cond="multiple sclerosis"))
    assert studies == [{"id": 1}, {"id": 2}]
    assert "pageToken" not in seen_params[0]
    assert seen_params[1]["pageToken"] == "abc"


def test_parse_pubmed_without_abstracts(fixture_text):
    rows = pubmed.parse_articles(fixture_text("pubmed.xml"))
    assert [r["pmid"] for r in rows] == ["11111111", "22222222"]
    first, second = rows
    assert first["title"] == "A trial of remyelination in MS."
    assert first["journal"] == "Ex J"
    assert first["year"] == "2017"
    assert first["doi"] == "10.1000/example.1"
    assert first["publication_types"] == "Journal Article; Randomized Controlled Trial"
    assert first["mesh_terms"] == "Multiple Sclerosis; Remyelination"
    assert "abstract" not in first
    # Falls back to MedlineDate and the full journal title.
    assert second["year"] == "2019"
    assert second["journal"] == "Another Journal"
    assert second["doi"] == ""
