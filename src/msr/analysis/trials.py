"""Track A: combine fetched trial records with the hand review.

    python -m msr.analysis.trials

Inputs:
- data/derived/trials_remyelination.csv   (from msr.fetch.clinicaltrials)
- data/curation/extra_trials.csv          (repair trials not on ClinicalTrials.gov)
- data/curation/trial_review.csv          (hand review: relevance, mechanism, result)

Output:
- data/derived/trials_repair_curated.csv  (every trial with its review)
- a summary printed to the terminal
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..paths import derived_dir, repo_root
from ..provenance import write_derived_csv

RELEVANCE = {
    "repair_efficacy": "Tests whether a therapy repairs myelin or restores function",
    "repair_safety": "Safety or dosing study of a therapy meant to repair myelin",
    "repair_secondary": "Another therapy (usually immune) with myelin repair as a secondary measure",
    "imaging_method": "Develops or tests a way to measure myelin",
    "other": "Not about myelin repair (found by a loose search)",
}
PRIMARY_MET = {"yes", "partial", "no", "harm", "pending", "unknown", ""}
REPAIR = {"repair_efficacy", "repair_safety", "repair_secondary"}

REVIEW_COLUMNS = [
    "relevance",
    "therapy",
    "mechanism",
    "targets",
    "population",
    "repair_outcome",
    "primary_met",
    "result_summary",
    "result_pmid",
    "notes",
]
TRIAL_COLUMNS = [
    "registry",
    "title",
    "status",
    "phases",
    "study_type",
    "start_date",
    "completion_date",
    "enrollment",
    "interventions",
    "lead_sponsor",
    "primary_outcomes",
    "has_results",
    "matched_by",
]
COLUMNS = ["trial_id"] + REVIEW_COLUMNS + TRIAL_COLUMNS


class ReviewError(ValueError):
    """The hand review doesn't line up with the fetched trials."""


def curation_dir() -> Path:
    return repo_root() / "data" / "curation"


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load_trials() -> dict[str, dict[str, Any]]:
    """Fetched ClinicalTrials.gov rows plus the hand-entered extra trials, by trial ID."""
    trials: dict[str, dict[str, Any]] = {}
    for row in read_csv(derived_dir() / "trials_remyelination.csv"):
        trials[row["nct_id"]] = {**row, "trial_id": row["nct_id"], "registry": "ClinicalTrials.gov"}
    for row in read_csv(curation_dir() / "extra_trials.csv"):
        if row["trial_id"] in trials:
            raise ReviewError(f"{row['trial_id']} is in both the fetched and the extra trials")
        trials[row["trial_id"]] = {**row, "matched_by": "manual", "has_results": ""}
    return trials


def validate(trials: dict[str, dict], review: list[dict[str, str]]) -> None:
    """Every trial needs exactly one valid review row, and every review row a trial."""
    problems = []
    seen = Counter(r["trial_id"] for r in review)
    problems += [f"{t} is reviewed {n} times" for t, n in seen.items() if n > 1]
    problems += [f"{t} has no review row" for t in sorted(set(trials) - set(seen))]
    problems += [f"{t} is reviewed but wasn't fetched" for t in sorted(set(seen) - set(trials))]
    for r in review:
        if r["relevance"] not in RELEVANCE:
            problems.append(f"{r['trial_id']}: unknown relevance {r['relevance']!r}")
        if r["primary_met"] not in PRIMARY_MET:
            problems.append(f"{r['trial_id']}: unknown primary_met {r['primary_met']!r}")
        if r["primary_met"] and r["relevance"] != "repair_efficacy":
            problems.append(f"{r['trial_id']}: primary_met is only for repair_efficacy trials")
    if problems:
        raise ReviewError("Trial review problems:\n  " + "\n  ".join(problems))


def combine(trials: dict[str, dict], review: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = [{**trials[r["trial_id"]], **r} for r in review]
    order = list(RELEVANCE)
    rows.sort(key=lambda r: (order.index(r["relevance"]), r["therapy"].lower(), r.get("start_date") or ""))
    return rows


def summarise(rows: list[dict[str, Any]]) -> str:
    lines = [f"{len(rows)} trials reviewed"]
    for key, label in RELEVANCE.items():
        lines.append(f"  {sum(r['relevance'] == key for r in rows):3d}  {key}: {label}")

    efficacy = [r for r in rows if r["relevance"] == "repair_efficacy"]
    lines.append("\nRepair efficacy trials by result:")
    for result, n in Counter(r["primary_met"] or "unknown" for r in efficacy).most_common():
        lines.append(f"  {n:3d}  {result}")

    by_therapy: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        if r["relevance"] in REPAIR - {"repair_secondary"}:
            by_therapy[r["therapy"]].append(r["primary_met"] or "-")
    lines.append("\nRepair therapies (trials; efficacy results):")
    for therapy, results in sorted(by_therapy.items(), key=lambda kv: -len(kv[1])):
        shown = ", ".join(x for x in results if x != "-") or "safety/dosing only"
        lines.append(f"  {therapy}: {len(results)} ({shown})")
    return "\n".join(lines)


def main() -> None:
    trials = load_trials()
    review = read_csv(curation_dir() / "trial_review.csv")
    validate(trials, review)
    rows = combine(trials, review)
    out = write_derived_csv(
        "trials_repair_curated.csv",
        rows,
        COLUMNS,
        source_id="clinicaltrials-gov",
        query={"inputs": ["data/derived/trials_remyelination.csv", "data/curation/extra_trials.csv",
                          "data/curation/trial_review.csv"]},
        notes=(
            "Trial records from ClinicalTrials.gov (see trials_remyelination.csv.manifest.json for the "
            "processing date), plus hand-entered trials from other registries. Review columns "
            "(relevance to myelin repair, mechanism, targets, result) were added by hand from the cited papers."
        ),
    )
    print(summarise(rows))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
