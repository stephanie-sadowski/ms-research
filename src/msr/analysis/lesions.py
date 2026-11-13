"""Track B: how OPCs differ in MS lesions compared with control white matter.

    python -m msr.analysis.lesions

Data (downloaded to data/raw/, never committed):
- Main: Lerma-Martin et al. 2024 (GEO GSE279180, PMID 39501036): about 3,900 OPC
  nuclei from 6 people with progressive MS and 6 controls, labelled by lesion
  type (chronic active, chronic inactive) and OPC state.
- Replication: Jäkel et al. 2019 (CELLxGENE "Oligodendrocytes in MS",
  PMID 30747918): 352 OPCs from 5 people with MS and 4 controls.

Method:
- Cells from the same person are not independent, so counts are summed per
  person (a "pseudobulk") before comparing groups. Groups are then compared
  person by person (Welch t-test on log2 counts per million), with
  Benjamini-Hochberg false discovery rates.
- With 6 vs 6 people, power is low. Effect sizes (log2 fold change) matter more
  than p-values, and agreement between the two studies matters most.

Outputs (data/derived/), gene- and group-level summaries only:
- lesion_opc_genes.csv: per gene, MS vs control in OPCs in both studies
- lesion_opc_states.csv: share of OPCs in each state, by lesion type
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse, stats

from ..http import download
from ..paths import raw_dir
from ..provenance import write_derived_csv

LERMA_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE279nnn/GSE279180/suppl/GSE279180_ctype_OPC.h5ad"
JAKEL_URL = "https://datasets.cellxgene.cziscience.com/8bbea7c5-c742-4c27-a597-0f1e1383bb48.h5ad"

MIN_CELLS = 30          # minimum OPCs for a person (or person + lesion type) to count
MIN_CELLS_JAKEL = 10    # Jäkel has few OPCs per person, so OPCs and COPs are pooled
JAKEL_CELL_TYPES = {"OPCs", "COPs"}
MIN_CELLS_PAIRED = 20   # per state, per person, for the within-person comparison

# Lerma-Martin OPC states: disease-associated vs resting (homeostatic).
DISEASE_STATES = {"OPC_Dis1", "OPC_Dis2"}
RESTING_STATES = {"OPC_Homeo"}
MIN_CPM = 10.0          # gene must reach this mean CPM in one group to be tested

# OPC states in Lerma-Martin that are on the way to becoming oligodendrocytes.
MATURING_STATES = {"OPC_COP", "OPC_PreOL", "OPC_Mature"}

# Genes to report explicitly as checks.
CHECK_GENES = {
    "interferon / antigen presentation (expected up in MS OPCs)": [
        "B2M", "HLA-A", "HLA-B", "HLA-C", "STAT1", "IFITM3", "SERPINA3", "CD74"],
    "OPC identity (expected stable)": ["PDGFRA", "OLIG2", "SOX10", "CSPG4"],
    "known repair targets": ["CHRM1", "RXRG", "HRH3", "LINGO1", "RGMA", "GPR17", "S1PR5", "LPAR1"],
}


# ---------- generic helpers (tested in tests/test_lesions.py) ----------

def pseudobulk(counts, groups: pd.Series, genes: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Sum cell counts per group. Returns (genes x groups counts, cells per group)."""
    codes, labels = pd.factorize(groups, sort=True)
    indicator = sparse.csr_matrix((np.ones(len(codes)), (codes, np.arange(len(codes)))), shape=(len(labels), len(codes)))
    summed = indicator @ (counts if sparse.issparse(counts) else sparse.csr_matrix(counts))
    summed = np.asarray(summed.todense()) if sparse.issparse(summed) else np.asarray(summed)
    table = pd.DataFrame(summed.T, index=genes, columns=list(labels))
    sizes = pd.Series(np.bincount(codes, minlength=len(labels)), index=list(labels))
    return table, sizes


def cpm(table: pd.DataFrame) -> pd.DataFrame:
    return table / table.sum(axis=0) * 1e6


def bh_fdr(pvalues: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (NaNs are kept as NaN)."""
    p = np.asarray(pvalues, dtype=float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    n = len(pv)
    if n == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order] * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1]
    result = np.empty(n)
    result[order] = np.minimum(adjusted, 1.0)
    out[ok] = result
    return out


def compare(cpm_table: pd.DataFrame, case: list[str], control: list[str], min_cpm: float = MIN_CPM) -> pd.DataFrame:
    """Per-gene comparison of two groups of pseudobulk samples."""
    a = cpm_table[case]
    b = cpm_table[control]
    keep = (a.mean(axis=1) >= min_cpm) | (b.mean(axis=1) >= min_cpm)
    la = np.log2(a[keep] + 1)
    lb = np.log2(b[keep] + 1)
    t, p = stats.ttest_ind(la, lb, axis=1, equal_var=False)
    return pd.DataFrame(
        {
            "mean_cpm_case": a[keep].mean(axis=1),
            "mean_cpm_control": b[keep].mean(axis=1),
            "log2fc": la.mean(axis=1) - lb.mean(axis=1),
            "t": t,
            "p": p,
            "fdr": bh_fdr(p),
            "n_case": len(case),
            "n_control": len(control),
        }
    )


# ---------- dataset-specific loading ----------

@dataclass
class Dataset:
    name: str
    counts: object
    genes: list[str]
    obs: pd.DataFrame


def load_lerma() -> Dataset:
    import anndata as ad

    path = download(LERMA_URL, raw_dir("geo") / "GSE279180_ctype_OPC.h5ad")
    a = ad.read_h5ad(path)
    obs = a.obs.copy()
    obs["person"] = obs["patient_id"].astype(str).str.split().str[0]
    obs["lesion"] = obs["lesion_type"].astype(str)
    obs["is_ms"] = obs["condition"].astype(str) == "MS"
    return Dataset("Lerma-Martin 2024", a.X, list(a.var_names), obs)


def load_jakel() -> Dataset:
    import anndata as ad

    path = download(JAKEL_URL, raw_dir("cellxgene") / "jakel2019_oligodendrocytes_in_ms.h5ad")
    a = ad.read_h5ad(path)
    opc = a.obs["author_cell_types"].astype(str).isin(JAKEL_CELL_TYPES).to_numpy()
    obs = a.obs.loc[opc].copy()
    obs["person"] = obs["donor_id"].astype(str)
    obs["lesion"] = obs["Lesion"].astype(str)
    obs["is_ms"] = obs["disease"].astype(str) == "multiple sclerosis"
    genes = list(a.var["feature_name"].astype(str))
    return Dataset("Jäkel 2019", a.X[opc], genes, obs)


def person_level(ds: Dataset, min_cells: int) -> tuple[pd.DataFrame, list[str], list[str]]:
    """CPM per person, and the MS and control people with enough OPCs."""
    table, sizes = pseudobulk(ds.counts, ds.obs["person"], ds.genes)
    table = table.T.groupby(level=0).sum().T  # merge duplicate gene symbols
    keep = sizes[sizes >= min_cells].index
    is_ms = ds.obs.groupby("person")["is_ms"].first()
    case = [p for p in keep if is_ms[p]]
    control = [p for p in keep if not is_ms[p]]
    return cpm(table[list(keep)]), case, control


def lesion_level(ds: Dataset, lesion: str, min_cells: int) -> tuple[pd.DataFrame, list[str], list[str]]:
    """CPM for one lesion type (one pseudobulk per person) against controls."""
    key = ds.obs["person"] + "|" + ds.obs["lesion"]
    table, sizes = pseudobulk(ds.counts, key, ds.genes)
    table = table.T.groupby(level=0).sum().T
    keep = [k for k in sizes.index if sizes[k] >= min_cells]
    case = [k for k in keep if k.endswith(f"|{lesion}")]
    control = [k for k in keep if k.endswith("|Ctrl")]
    return cpm(table[keep]), case, control


def paired_compare(cpm_a: pd.DataFrame, cpm_b: pd.DataFrame, min_cpm: float = MIN_CPM) -> pd.DataFrame:
    """Per-gene paired comparison: the same people (columns) in two conditions."""
    people = [c for c in cpm_a.columns if c in cpm_b.columns]
    a, b = cpm_a[people], cpm_b[people]
    keep = (a.mean(axis=1) >= min_cpm) | (b.mean(axis=1) >= min_cpm)
    diff = np.log2(a[keep] + 1) - np.log2(b[keep] + 1)
    t, p = stats.ttest_1samp(diff, 0.0, axis=1)
    return pd.DataFrame({
        "log2fc": diff.mean(axis=1),
        "people_up": (diff > 0).sum(axis=1),
        "t": t,
        "p": p,
        "fdr": bh_fdr(p),
        "mean_cpm_disease": a[keep].mean(axis=1),
        "mean_cpm_resting": b[keep].mean(axis=1),
        "n_people": len(people),
    })


def disease_program(ds: Dataset) -> pd.DataFrame:
    """Within MS people: disease-associated OPC states vs resting OPCs (paired by person)."""
    obs = ds.obs
    state = obs["subtype"].astype(str)
    group = np.where(state.isin(DISEASE_STATES), "disease", np.where(state.isin(RESTING_STATES), "resting", "other"))
    key = pd.Series(obs["person"].to_numpy() + "|" + group, index=obs.index)
    table, sizes = pseudobulk(ds.counts, key, ds.genes)
    table = table.T.groupby(level=0).sum().T
    ms_people = sorted(set(obs.loc[obs["is_ms"], "person"]))
    people = [p for p in ms_people
              if sizes.get(f"{p}|disease", 0) >= MIN_CELLS_PAIRED and sizes.get(f"{p}|resting", 0) >= MIN_CELLS_PAIRED]
    norm = cpm(table)
    dis = norm[[f"{p}|disease" for p in people]].set_axis(people, axis=1)
    rest = norm[[f"{p}|resting" for p in people]].set_axis(people, axis=1)
    return paired_compare(dis, rest)


def contamination_flags(genes: list[str], max_share: float = 0.1) -> pd.Series:
    """Flag genes that probably come from other cells' RNA rather than from OPCs.

    In damaged tissue, free-floating RNA from other cells (for example GFAP from
    scarring astrocytes) sticks to nuclei. A gene is flagged if it is mitochondrial,
    or if in healthy brain (Human Protein Atlas) its OPC/oligodendrocyte-lineage
    expression is under `max_share` of its level in the top other cell type.
    """
    from ..fetch import hpa

    expr = {e.symbol: e for e in hpa.load().values()}
    flags = {}
    for g in genes:
        if g.startswith("MT-"):
            flags[g] = "mitochondrial"
            continue
        e = expr.get(g)
        if e and e.max_other_ncpm >= 20 and e.opc_ncpm < max_share * e.max_other_ncpm:
            flags[g] = f"mainly {e.max_other_type}"
        else:
            flags[g] = ""
    return pd.Series(flags)


def state_summary(obs: pd.DataFrame, min_cells: int = MIN_CELLS) -> pd.DataFrame:
    """Share of maturing OPCs per person and lesion type, summarised by lesion type."""
    obs = obs.assign(maturing=obs["subtype"].astype(str).isin(MATURING_STATES))
    per = obs.groupby(["lesion", "person"]).agg(cells=("maturing", "size"), maturing=("maturing", "mean"))
    per = per[per["cells"] >= min_cells].reset_index()
    rows = []
    control = per.loc[per["lesion"] == "Ctrl", "maturing"]
    for lesion, grp in per.groupby("lesion"):
        p = np.nan
        if lesion != "Ctrl" and len(grp) >= 2 and len(control) >= 2:
            p = stats.mannwhitneyu(grp["maturing"], control, alternative="two-sided").pvalue
        rows.append({
            "lesion_type": lesion,
            "people": len(grp),
            "opcs": int(grp["cells"].sum()),
            # Group mean only: with as few as 2 people, min/max would reveal individuals.
            "mean_share_maturing": round(grp["maturing"].mean(), 3),
            "p_vs_control": round(p, 4) if pd.notna(p) else p,
        })
    # Overall states too, pooled per lesion type (counts of cells, not people).
    shares = obs.groupby("lesion")["subtype"].value_counts(normalize=True).unstack(fill_value=0).round(3)
    return pd.DataFrame(rows).merge(shares, left_on="lesion_type", right_index=True, how="left")


def main() -> None:
    lerma = load_lerma()
    jakel = load_jakel()

    cpm_l, ms_l, ctrl_l = person_level(lerma, MIN_CELLS)
    main_cmp = compare(cpm_l, ms_l, ctrl_l)
    ca = compare(*lesion_level(lerma, "CA", MIN_CELLS))
    ci = compare(*lesion_level(lerma, "CI", MIN_CELLS))
    cpm_j, ms_j, ctrl_j = person_level(jakel, MIN_CELLS_JAKEL)
    rep = compare(cpm_j, ms_j, ctrl_j)

    genes = main_cmp.join(ca[["log2fc", "fdr"]].add_prefix("chronic_active_"), how="left")
    genes = genes.join(ci[["log2fc", "fdr"]].add_prefix("chronic_inactive_"), how="left")
    genes = genes.join(rep[["log2fc", "p"]].add_prefix("jakel_"), how="left")
    genes["replicated"] = (
        (genes["fdr"] < 0.1)
        & (genes["jakel_p"] < 0.05)
        & (np.sign(genes["log2fc"]) == np.sign(genes["jakel_log2fc"]))
    )
    genes["possible_contamination"] = contamination_flags(list(genes.index)).reindex(genes.index).fillna("")
    genes = genes.sort_values("p")
    genes.index.name = "gene"
    out = genes.reset_index().round(
        {"mean_cpm_case": 1, "mean_cpm_control": 1, "log2fc": 3, "t": 3, "chronic_active_log2fc": 3,
         "chronic_inactive_log2fc": 3, "jakel_log2fc": 3})
    for col in ["p", "fdr", "chronic_active_fdr", "chronic_inactive_fdr", "jakel_p"]:
        out[col] = out[col].map(lambda v: float(f"{v:.3g}") if pd.notna(v) else v)

    columns = ["gene", "log2fc", "p", "fdr", "mean_cpm_case", "mean_cpm_control", "n_case", "n_control",
               "chronic_active_log2fc", "chronic_active_fdr", "chronic_inactive_log2fc", "chronic_inactive_fdr",
               "jakel_log2fc", "jakel_p", "replicated", "possible_contamination"]
    sources = ["geo-gse279180", "cellxgene"]
    gene_path = write_derived_csv(
        "lesion_opc_genes.csv", out.to_dict("records"), columns, source_id=sources,
        query={"lerma": LERMA_URL, "jakel": JAKEL_URL, "min_cells": MIN_CELLS,
               "min_cells_jakel": MIN_CELLS_JAKEL, "min_cpm": MIN_CPM},
        notes=("OPC gene expression, MS vs control white matter. Person-level pseudobulk, Welch t-test on "
               "log2(CPM+1), Benjamini-Hochberg FDR. log2fc > 0 means higher in MS. Main study: Lerma-Martin et al. "
               "2024 (PMID 39501036, GEO GSE279180). Replication: Jäkel et al. 2019 (PMID 30747918, CELLxGENE, "
               "CC BY 4.0). Summary statistics only; no cell- or person-level data."),
    )
    program = disease_program(lerma).sort_values("p")
    program["possible_contamination"] = contamination_flags(list(program.index)).reindex(program.index).fillna("")
    program.index.name = "gene"
    prog_out = program.reset_index()
    for col in ["log2fc", "t", "mean_cpm_disease", "mean_cpm_resting"]:
        prog_out[col] = prog_out[col].round(3)
    for col in ["p", "fdr"]:
        prog_out[col] = prog_out[col].map(lambda v: float(f"{v:.3g}") if pd.notna(v) else v)
    prog_path = write_derived_csv(
        "lesion_opc_disease_program.csv", prog_out.to_dict("records"),
        ["gene", "log2fc", "people_up", "n_people", "p", "fdr", "mean_cpm_disease", "mean_cpm_resting", "t",
         "possible_contamination"],
        source_id="geo-gse279180",
        query={"lerma": LERMA_URL, "disease_states": sorted(DISEASE_STATES), "resting_states": sorted(RESTING_STATES),
               "min_cells_per_state": MIN_CELLS_PAIRED, "min_cpm": MIN_CPM},
        notes=("Within people with MS: disease-associated OPC states (Dis1, Dis2, as labelled by the authors) vs "
               "resting OPCs, pseudobulk per person and state, paired t-test on log2(CPM+1), BH FDR. "
               "Lerma-Martin et al. 2024 (PMID 39501036). Summary statistics only."),
    )

    states = state_summary(lerma.obs)
    state_path = write_derived_csv(
        "lesion_opc_states.csv", states.to_dict("records"), list(states.columns), source_id="geo-gse279180",
        query={"lerma": LERMA_URL, "maturing_states": sorted(MATURING_STATES), "min_cells": MIN_CELLS},
        notes=("Share of OPCs in maturing states (COP, PreOL, Mature) by lesion type, Lerma-Martin et al. 2024. "
               "mean/min/max are across people; state columns are pooled cell shares. Group summaries only."),
    )

    print(f"Lerma-Martin: {len(ms_l)} MS vs {len(ctrl_l)} control people; Jäkel: {len(ms_j)} MS vs {len(ctrl_j)} control")
    sig = genes[genes["fdr"] < 0.1]
    print(f"FDR < 0.1 genes flagged as possible contamination: {(sig['possible_contamination'] != '').sum()} of {len(sig)}; "
          f"up: {((sig['possible_contamination'] != '') & (sig['log2fc'] > 0)).sum()} of {(sig['log2fc'] > 0).sum()}")
    print(f"Genes tested: {len(main_cmp)}; FDR < 0.1: {(main_cmp['fdr'] < 0.1).sum()} "
          f"(up {((main_cmp['fdr'] < 0.1) & (main_cmp['log2fc'] > 0)).sum()}, "
          f"down {((main_cmp['fdr'] < 0.1) & (main_cmp['log2fc'] < 0)).sum()}); replicated in Jäkel: {int(genes['replicated'].sum())}")
    print("\nTop replicated genes:")
    print(genes[genes["replicated"]].head(25)[["log2fc", "fdr", "jakel_log2fc", "jakel_p"]].round(3).to_string())
    for label, glist in CHECK_GENES.items():
        print(f"\n{label}:")
        print(genes.reindex([g for g in glist])[["log2fc", "fdr", "mean_cpm_control", "jakel_log2fc", "jakel_p"]].round(3).to_string())
    print("\nOPC states by lesion type:")
    print(states.to_string(index=False))
    sig = program[program["fdr"] < 0.05]
    print(f"\nDisease-associated vs resting OPCs, within {int(program['n_people'].iloc[0])} MS people: "
          f"{len(sig)} genes at FDR < 0.05 (up {(sig['log2fc'] > 0).sum()}, down {(sig['log2fc'] < 0).sum()})")
    print("Top up:", ", ".join(sig[sig["log2fc"] > 0].sort_values("log2fc", ascending=False).head(30).index))
    print("Top down:", ", ".join(sig[sig["log2fc"] < 0].sort_values("log2fc").head(30).index))
    print("\nKnown genes in the disease program:")
    allg = [g for gl in CHECK_GENES.values() for g in gl]
    print(program.reindex(allg)[["log2fc", "people_up", "fdr", "mean_cpm_resting"]].round(3).to_string())
    print(f"\n-> {gene_path}\n-> {prog_path}\n-> {state_path}")


if __name__ == "__main__":
    main()
