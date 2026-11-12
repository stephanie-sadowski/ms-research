"""Fetch MS trial records from ClinicalTrials.gov (API v2).

Run the myelin-repair preset:

    python -m msr.fetch.clinicaltrials

This saves the full study records to data/raw/clinicaltrials/ and writes
data/derived/trials_remyelination.csv (one row per trial).

Terms: https://clinicaltrials.gov/about-site/terms-conditions
When sharing, credit ClinicalTrials.gov, show the processing date and describe
changes. The manifest written next to the CSV records all three.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Iterator

from ..http import get_json
from ..paths import raw_dir
from ..provenance import now_utc, write_derived_csv, write_manifest

API = "https://clinicaltrials.gov/api/v2/studies"
SOURCE_ID = "clinicaltrials-gov"

# Conditions for the myelin-repair preset. Optic neuritis is included because
# several repair drugs were first tested there (for example opicinumab, clemastine).
CONDITIONS = "multiple sclerosis OR optic neuritis"

# Free-text terms that mark a trial as being about myelin repair.
REPAIR_TERMS = 'remyelination OR remyelinating OR "myelin repair"'

# Drugs tested as myelin-repair treatments. Searched as interventions so trials
# that don't use the word "remyelination" are still found. Some (for example
# metformin) also bring in trials with other aims, so every row is labelled
# with what matched it and needs review.
REPAIR_DRUGS = [
    "clemastine",
    "opicinumab",
    "elezanumab",
    "bexarotene",
    "PIPE-307",
    "temelimab",
    "CNM-Au8",
    "GSK239512",
    "liothyronine",
    "metformin",
    "bazedoxifene",
    "ifenprodil",
    "BIIB061",
    "PRO-1562",
    "rHIgM22",
]

# Trials that matter for myelin repair but that the searches above can't find,
# with the reason each one is included.
EXTRA_TRIALS = {
    "NCT03109288": (
        "TRAP-MS platform trial. Its clemastine arm was stopped for faster disability "
        "progression (PMID 40371642), but the registry no longer lists clemastine."
    ),
}

COLUMNS = [
    "nct_id",
    "title",
    "matched_by",
    "status",
    "why_stopped",
    "phases",
    "study_type",
    "start_date",
    "completion_date",
    "enrollment",
    "conditions",
    "interventions",
    "intervention_types",
    "lead_sponsor",
    "primary_outcomes",
    "has_results",
    "reference_pmids",
    "last_updated",
]


def search_studies(
    *,
    cond: str | None = None,
    term: str | None = None,
    intr: str | None = None,
    page_size: int = 100,
    use_cache: bool = True,
) -> Iterator[dict[str, Any]]:
    """Yield full study records matching the query, following every page."""
    params: dict[str, Any] = {"pageSize": page_size, "format": "json"}
    if cond:
        params["query.cond"] = cond
    if term:
        params["query.term"] = term
    if intr:
        params["query.intr"] = intr

    while True:
        data = get_json(API, params, use_cache=use_cache)
        yield from data.get("studies", [])
        token = data.get("nextPageToken")
        if not token:
            break
        params = {**params, "pageToken": token}


def get_study(nct_id: str, use_cache: bool = True) -> dict[str, Any]:
    """Fetch one full study record by NCT ID."""
    return get_json(f"{API}/{nct_id}", {"format": "json"}, use_cache=use_cache)


def _join(values: list[Any]) -> str:
    return "; ".join(str(v) for v in values if v not in (None, ""))


def flatten(study: dict[str, Any]) -> dict[str, Any]:
    """Turn one API study record into a flat row."""
    p = study.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    arms = p.get("armsInterventionsModule", {})
    sponsor = p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})
    outcomes = p.get("outcomesModule", {})
    refs = p.get("referencesModule", {}).get("references", [])
    interventions = arms.get("interventions", [])

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "status": status.get("overallStatus"),
        "why_stopped": status.get("whyStopped", ""),
        "phases": _join(design.get("phases", [])),
        "study_type": design.get("studyType"),
        "start_date": status.get("startDateStruct", {}).get("date"),
        "completion_date": status.get("completionDateStruct", {}).get("date"),
        "enrollment": design.get("enrollmentInfo", {}).get("count"),
        "conditions": _join(p.get("conditionsModule", {}).get("conditions", [])),
        "interventions": _join([i.get("name") for i in interventions]),
        "intervention_types": _join(sorted({i.get("type") for i in interventions if i.get("type")})),
        "lead_sponsor": sponsor.get("name"),
        "primary_outcomes": _join([o.get("measure") for o in outcomes.get("primaryOutcomes", [])]),
        "has_results": bool(study.get("hasResults")),
        "reference_pmids": _join([r.get("pmid") for r in refs]),
        "last_updated": status.get("lastUpdatePostDateStruct", {}).get("date"),
    }


def fetch_repair_trials(use_cache: bool = True) -> tuple[list[dict[str, Any]], dict[str, dict]]:
    """Run the keyword search and every drug search; merge by NCT ID.

    Returns (rows, raw_studies_by_nct_id).
    """
    queries: list[tuple[str, dict[str, str]]] = [
        ("keyword", {"cond": CONDITIONS, "term": REPAIR_TERMS}),
    ] + [(f"drug:{d}", {"cond": CONDITIONS, "intr": d}) for d in REPAIR_DRUGS]

    raw: dict[str, dict] = {}
    matched: dict[str, list[str]] = {}
    for label, query in queries:
        for study in search_studies(**query, use_cache=use_cache):
            nct = study["protocolSection"]["identificationModule"]["nctId"]
            raw[nct] = study
            matched.setdefault(nct, []).append(label)

    for nct in EXTRA_TRIALS:
        raw[nct] = get_study(nct, use_cache=use_cache)
        matched.setdefault(nct, []).append("manual")

    rows = []
    for nct, study in raw.items():
        row = flatten(study)
        row["matched_by"] = _join(matched[nct])
        rows.append(row)
    rows.sort(key=lambda r: (r["start_date"] or "", r["nct_id"]))
    return rows, raw


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true", help="ignore the cache and re-download")
    args = parser.parse_args(argv)

    processed = now_utc()
    rows, raw = fetch_repair_trials(use_cache=not args.refresh)

    raw_path = raw_dir("clinicaltrials") / "remyelination_studies.json"
    raw_path.write_text(json.dumps(raw, indent=1))
    write_manifest(raw_path, source="ClinicalTrials.gov", api=API, processed=processed, studies=len(raw))

    query = {
        "api": API,
        "conditions": CONDITIONS,
        "terms": REPAIR_TERMS,
        "drugs": REPAIR_DRUGS,
        "extra_trials": EXTRA_TRIALS,
    }
    out = write_derived_csv(
        "trials_remyelination.csv",
        rows,
        COLUMNS,
        source_id=SOURCE_ID,
        query=query,
        notes=(
            f"Data from ClinicalTrials.gov, processed {processed}. "
            "Modified: selected fields flattened to one row per study; lists joined with '; '; "
            "matched_by added to show which search found each study. "
            "Rows found only by a drug search may not be about myelin repair and need review."
        ),
    )
    print(f"{len(rows)} trials -> {out}")


if __name__ == "__main__":
    main()
