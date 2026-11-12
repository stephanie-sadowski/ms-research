import csv

import pytest

from msr.analysis import trials as t

REVIEW_HEADER = ["trial_id"] + t.REVIEW_COLUMNS


def write(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in header})


@pytest.fixture
def repo(tmp_repo):
    write(
        tmp_repo / "data" / "derived" / "trials_remyelination.csv",
        ["nct_id", "title", "status", "matched_by", "start_date"],
        [
            {"nct_id": "NCT1", "title": "Repair drug trial", "status": "COMPLETED", "matched_by": "keyword"},
            {"nct_id": "NCT2", "title": "Unrelated", "status": "COMPLETED", "matched_by": "drug:x"},
        ],
    )
    write(
        tmp_repo / "data" / "curation" / "extra_trials.csv",
        ["trial_id", "registry", "title", "status"],
        [{"trial_id": "ISRCTN1", "registry": "ISRCTN", "title": "UK trial", "status": "COMPLETED"}],
    )
    return tmp_repo


def review_rows(**overrides):
    rows = {
        "NCT1": {"trial_id": "NCT1", "relevance": "repair_efficacy", "therapy": "Drug A", "primary_met": "no"},
        "NCT2": {"trial_id": "NCT2", "relevance": "other", "therapy": "Thing"},
        "ISRCTN1": {"trial_id": "ISRCTN1", "relevance": "repair_efficacy", "therapy": "Drug B", "primary_met": "yes"},
    }
    for trial_id, change in overrides.items():
        if change is None:
            rows.pop(trial_id)
        else:
            rows[trial_id] = {**rows.get(trial_id, {"trial_id": trial_id}), **change}
    return [{k: r.get(k, "") for k in REVIEW_HEADER} for r in rows.values()]


def test_load_trials_includes_extra_registries(repo):
    trials = t.load_trials()
    assert set(trials) == {"NCT1", "NCT2", "ISRCTN1"}
    assert trials["NCT1"]["registry"] == "ClinicalTrials.gov"
    assert trials["ISRCTN1"]["matched_by"] == "manual"


def test_valid_review_combines(repo):
    trials = t.load_trials()
    review = review_rows()
    t.validate(trials, review)
    rows = t.combine(trials, review)
    assert [r["trial_id"] for r in rows] == ["NCT1", "ISRCTN1", "NCT2"]
    assert rows[0]["title"] == "Repair drug trial"
    assert rows[0]["primary_met"] == "no"


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"NCT2": None}, "NCT2 has no review row"),
        ({"NCT9": {"relevance": "other"}}, "NCT9 is reviewed but wasn't fetched"),
        ({"NCT1": {"relevance": "maybe"}}, "unknown relevance"),
        ({"NCT1": {"primary_met": "sort of"}}, "unknown primary_met"),
        ({"NCT2": {"primary_met": "no"}}, "only for repair_efficacy"),
    ],
)
def test_validation_catches_problems(repo, overrides, message):
    with pytest.raises(t.ReviewError, match=message):
        t.validate(t.load_trials(), review_rows(**overrides))


def test_duplicate_review_rows_are_caught(repo):
    review = review_rows()
    review.append(dict(review[0]))
    with pytest.raises(t.ReviewError, match="reviewed 2 times"):
        t.validate(t.load_trials(), review)


def test_real_review_is_valid():
    """The committed hand review matches the committed trial table."""
    trials = t.load_trials()
    t.validate(trials, t.read_csv(t.curation_dir() / "trial_review.csv"))
