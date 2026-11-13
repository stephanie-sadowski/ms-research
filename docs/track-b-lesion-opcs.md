# Track B: OPCs in MS lesions

*Run 2026-11-12. This is part of the [myelin repair plan](myelin-repair-plan.md).*

**Question:** what's different about oligodendrocyte precursor cells (OPCs), the cells that should rebuild myelin, inside MS lesions?

**Short answer from this first pass:** the clearest signal is a **change in which states the OPCs are in**, not in individual genes.
- In chronic lesions, about half the OPCs are in "disease-associated" states, against about 12% in control white matter.
- Lesions also hold *more* OPCs on the way to maturing than control white matter does (about 11% against 1.5%).
- Gene-by-gene differences are weak with the number of people available, and they didn't replicate in a second study.

## Data

| Study | What | People | OPCs |
|---|---|---|---|
| **Lerma-Martin et al. 2024**, Nat Neurosci ([PMID 39501036](https://pubmed.ncbi.nlm.nih.gov/39501036/), GEO [GSE279180](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE279180)) | Single-nucleus RNA from subcortical white matter: chronic active (CA) and chronic inactive (CI) lesions, plus controls. The authors labelled each OPC's state. | 6 MS (all secondary progressive), 6 controls | 3,945 |
| **Jäkel et al. 2019**, Nature ([PMID 30747918](https://pubmed.ncbi.nlm.nih.gov/30747918/), CELLxGENE) | Single-nucleus RNA from MS and control white matter | 5 MS, 4 controls (3 and 5 with enough cells) | 352 OPCs + 242 COPs |

Both files hold raw counts. They stay in `data/raw/` (gitignored); only gene-level and group-level summaries are committed.

## Method

`python -m msr.analysis.lesions`:

- **Person-level pseudobulk.** Cells from the same person aren't independent, so counts are summed per person before comparing groups. Comparing thousands of cells as if they were separate samples would give falsely small p-values.
- **Three comparisons:**
  1. MS vs control OPCs: Lerma-Martin as the main study, Jäkel as replication (OPCs and COPs pooled, because Jäkel has too few OPCs per person).
  2. Within people with MS: OPCs in disease-associated states (the authors' Dis1 and Dis2) against resting OPCs (Homeo), **paired by person**.
  3. The share of OPCs in each state, by lesion type.
- **Statistics:** Welch or paired t-test on log2(CPM+1), with Benjamini–Hochberg false discovery rate (FDR).
- **Contamination flags.** Damaged tissue releases RNA that sticks to other cells' nuclei. A gene is flagged if it is mitochondrial, or if healthy-brain data shows it mainly in another cell type (from the Human Protein Atlas).

## Results

### 1. OPC states shift strongly in lesions (most robust finding)

Shares of OPCs in each state, from [`lesion_opc_states.csv`](../data/derived/lesion_opc_states.csv):

| | Control (6 people) | Chronic active (4) | Chronic inactive (2) |
|---|---|---|---|
| Resting (Homeo) | **85%** | 28% | 37% |
| Disease-associated (Dis1 + Dis2) | 12% | **48%** | **44%** |
| Maturing (COP + PreOL + Mature) | 1.5% (per-person mean) | **10.5%** | **11.8%** |
| Maturing, person-level test against control | | p = 0.04 (4 vs 6) | p = 0.13 (2 vs 6) |

- Most OPCs in lesions leave the resting state.
- Lesions contain **more** maturing OPCs than healthy white matter, where turnover is very low.

This doesn't contradict the "stuck OPC" idea. Kuhlmann et al. 2008 found maturing OPCs to be rare in chronic lesions **compared with early lesions** ([PMID 18515322](https://pubmed.ncbi.nlm.nih.gov/18515322/)), and this dataset has no early lesions. What these data add is that in chronic lesions **some maturation is still being attempted**. That suggests the block may sit partly at a **later step**, from pre-myelinating to myelinating cells, rather than only at the start.

**Caveats:**
- Only 4 and 2 people have lesions of each type.
- The states are the authors' labels.
- Control white matter came from different people than the lesions.

### 2. Gene-by-gene MS vs control: weak and not replicated

From [`lesion_opc_genes.csv`](../data/derived/lesion_opc_genes.csv):
- 9,689 genes tested; 88 at FDR < 0.1 (39 up, 49 down).
- **Half the "up" genes are probably contamination:** 20 of 39 are flagged, including mitochondrial genes and **GFAP** (from scarring astrocytes).
- Several unflagged "up" genes are mature-oligodendrocyte genes (TUBA1A, APLP1, ANLN, TMCC2). They probably reflect the larger share of maturing cells in lesion OPCs, not a change inside each OPC.
- **Replication failed.** Only 47 of the 88 genes moved the same way in Jäkel, which is chance level, and only 1 gene (ADAM23) replicated formally. Jäkel has only 3 usable MS donors, so this is a weak test, not proof the signals are false.
- The most interesting unflagged "down" genes are VEGFA (−2.6 log2), PROM1, SULF2 and XYLT1. They're tentative.

### 3. Disease-associated vs resting OPCs within the same people: small, consistent shifts

From [`lesion_opc_disease_program.csv`](../data/derived/lesion_opc_disease_program.csv), for 6 people with MS:
- No gene reaches FDR < 0.05; the differences are small (typically 1.2–1.4×).
- **542 genes change in the same direction in all 6 people.** That's a reasonable basis for a "disease-associated OPC" signature for drug repurposing (Track D).
- **GPR17**, a known brake on OPC maturation, is higher in disease-associated OPCs in **all 6 people** (log2 +1.26). That fits its role as a repair target noted in Track C.
- **Interferon and antigen-presentation genes** (B2M, HLA-A/B/C, STAT1) lean upward (4–5 of 6 people) but aren't significant. Earlier studies reported immune-like OPCs in MS; this data gives only weak support.

### Known repair targets

| Gene | In OPCs here? | Notes |
|---|---|---|
| CHRM1, RXRG, HRH3 | Too low to test | As in healthy-brain data: single-nucleus RNA may miss low-abundance receptors |
| GPR17 | Yes | Up in disease-associated OPCs in 6 of 6 people |
| LINGO1, RGMA | Yes | No consistent change |

## What this means

1. **For Track C (target ranking):** expression in lesion OPCs can't confirm the best-supported targets, because CHRM1, RXRG and HRH3 are below detection. Absence in this data isn't evidence against a target. GPR17 gains support.
2. **For Track D (drug repurposing):** the 542 consistent genes from the paired comparison, after removing contamination-flagged genes, are the best "disease-associated OPC" signature available so far. Use it with caution, given the small effects.
3. **On the biology:** the strongest result is about **cell states, not single genes**. Lesions push OPCs out of rest; some start to mature, but most end up in disease-associated states. Repair strategies could aim either at moving OPCs out of those states, or at helping the ones that start maturing finish the job.

## Limits

- **Few people:** 6 vs 6 in the main study, and only 2 with chronic inactive lesions. Results are hypotheses, not findings.
- **Only progressive MS** and only chronic lesions. No early or remyelinating lesions in the main study.
- **Contamination flags are approximate.** They rely on healthy-brain reference data.
- **The state labels are the authors'.** They weren't re-derived here.

## Next steps

- **Add a larger dataset.** Pick a bigger single-nucleus MS cohort with lesion annotations for better power, ideally one that includes remyelinated lesions.
- **Use remyelinated areas where available.** Jäkel's "RM" samples are too small here, but comparing lesions that repaired with ones that didn't would be the most informative contrast.
- **Correct for contamination properly,** with ambient-RNA removal on the raw files rather than flags after the fact.
- **Bring this into Track C version 2.** GPR17 and the disease-state signature can feed the target ranking.
