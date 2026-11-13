import numpy as np
import pandas as pd
import pytest
from scipy import sparse

pytest.importorskip("scipy")
from msr.analysis import lesions as L  # noqa: E402


def test_pseudobulk_sums_cells_per_group():
    counts = sparse.csr_matrix(np.array([[1, 0], [2, 3], [0, 5]]))
    table, sizes = L.pseudobulk(counts, pd.Series(["b", "a", "b"]), ["G1", "G2"])
    assert table.loc["G1", "a"] == 2 and table.loc["G2", "a"] == 3
    assert table.loc["G1", "b"] == 1 and table.loc["G2", "b"] == 5
    assert sizes.to_dict() == {"a": 1, "b": 2}


def test_cpm_columns_sum_to_a_million():
    table = pd.DataFrame({"x": [1, 3], "y": [10, 10]}, index=["G1", "G2"])
    assert L.cpm(table).sum().round().tolist() == [1e6, 1e6]


def test_bh_fdr_matches_hand_calculation():
    p = np.array([0.01, 0.04, 0.03, np.nan])
    # sorted 0.01, 0.03, 0.04 -> 0.03, 0.045, 0.04 -> monotone: 0.03, 0.04, 0.04
    assert L.bh_fdr(p)[:3] == pytest.approx([0.03, 0.04, 0.04])
    assert np.isnan(L.bh_fdr(p)[3])


def _people_table(effect: float, n: int = 5, seed: int = 0) -> tuple[pd.DataFrame, list[str], list[str]]:
    rng = np.random.default_rng(seed)
    case = [f"ms{i}" for i in range(n)]
    control = [f"co{i}" for i in range(n)]
    data = {}
    for p in case + control:
        base = rng.normal(100, 5, size=3)
        if p in case:
            base[0] *= 2 ** effect  # gene UP changes, others don't
        data[p] = base
    return pd.DataFrame(data, index=["UP", "SAME", "SAME2"]), case, control


def test_compare_finds_the_changed_gene():
    table, case, control = _people_table(effect=2.0)
    res = L.compare(table, case, control, min_cpm=1)
    assert res.loc["UP", "log2fc"] == pytest.approx(2.0, abs=0.2)
    assert res.loc["UP", "p"] < 0.001
    assert abs(res.loc["SAME", "log2fc"]) < 0.3


def test_compare_drops_low_expression_genes():
    table = pd.DataFrame({"a": [1.0, 100.0], "b": [1.0, 100.0], "c": [1.0, 100.0], "d": [1.0, 100.0]},
                         index=["LOW", "HIGH"])
    res = L.compare(table, ["a", "b"], ["c", "d"], min_cpm=10)
    assert list(res.index) == ["HIGH"]


def test_paired_compare_uses_matching_people():
    a = pd.DataFrame({"p1": [200.0, 50], "p2": [400.0, 52], "p3": [80.0, 49]}, index=["UP", "SAME"])
    b = pd.DataFrame({"p3": [40.0, 50], "p1": [100.0, 51], "p2": [200.0, 50]}, index=["UP", "SAME"])
    res = L.paired_compare(a, b, min_cpm=1)
    assert res.loc["UP", "log2fc"] == pytest.approx(1.0, abs=0.02)
    assert res.loc["UP", "people_up"] == 3
    assert res.loc["UP", "n_people"] == 3


def test_state_summary_counts_maturing_share():
    obs = pd.DataFrame({
        "person": ["a"] * 40 + ["b"] * 40,
        "lesion": ["Ctrl"] * 40 + ["CA"] * 40,
        "subtype": ["OPC_Homeo"] * 39 + ["OPC_COP"] + ["OPC_Homeo"] * 30 + ["OPC_PreOL"] * 10,
    })
    s = L.state_summary(obs, min_cells=30).set_index("lesion_type")
    assert s.loc["Ctrl", "mean_share_maturing"] == pytest.approx(1 / 40, abs=1e-3)
    assert s.loc["CA", "mean_share_maturing"] == pytest.approx(0.25)
    assert s.loc["CA", "people"] == 1
