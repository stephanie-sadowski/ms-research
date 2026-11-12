import csv
import json

import pytest

from msr.http import cache_key
from msr.provenance import LicenseError, check_shareable, write_derived_csv


def test_controlled_sources_are_blocked(tmp_repo):
    for source in ["msbase", "narcoms", "uk-ms-register", "uk-biobank"]:
        with pytest.raises(LicenseError):
            check_shareable(source)


def test_non_shareable_open_sources_are_blocked(tmp_repo):
    # Global Burden of Disease forbids redistribution; GEO is per-dataset.
    for source in ["gbd-results", "geo"]:
        with pytest.raises(LicenseError):
            check_shareable(source)


def test_unknown_source_raises(tmp_repo):
    with pytest.raises(KeyError):
        check_shareable("not-a-source")


def test_write_derived_csv_with_manifest(tmp_repo):
    path = write_derived_csv(
        "example.csv",
        [{"a": 1, "b": "x", "extra": "ignored"}],
        ["a", "b"],
        source_id="clinicaltrials-gov",
        query={"cond": "multiple sclerosis"},
    )
    assert path == tmp_repo / "data" / "derived" / "example.csv"
    with open(path) as f:
        assert list(csv.DictReader(f)) == [{"a": "1", "b": "x"}]
    manifest = json.loads(path.with_name("example.csv.manifest.json").read_text())
    assert manifest["source_id"] == "clinicaltrials-gov"
    assert manifest["rows"] == 1
    assert manifest["terms_url"].startswith("https://clinicaltrials.gov/")


def test_write_derived_csv_refuses_blocked_source(tmp_repo):
    with pytest.raises(LicenseError):
        write_derived_csv("x.csv", [], ["a"], source_id="uk-biobank", query={})
    assert not (tmp_repo / "data" / "derived" / "x.csv").exists()


def test_cache_key_ignores_param_order():
    assert cache_key("https://x", {"a": 1, "b": 2}) == cache_key("https://x", {"b": 2, "a": 1})
    assert cache_key("https://x", {"a": 1}) != cache_key("https://x", {"a": 2})
