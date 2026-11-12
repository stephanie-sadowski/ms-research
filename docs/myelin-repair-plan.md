# Plan: connecting public data to research myelin repair

**Goal:** use public data to find and rank promising ways to help the body **replace lost myelin (remyelination)** in MS, and to understand why earlier attempts failed.

**What this repo can and can't do:** public-data analysis can **generate and prioritise hypotheses**: which targets and drugs look most promising, and why. It can't prove that anything works in people. That requires lab experiments and clinical trials. A realistic end product is a well-documented, ranked shortlist of targets and drug candidates with the evidence for each, which can be shared with researchers.

Nothing here is medical advice.

## Background: why myelin doesn't come back

- The brain keeps a supply of **oligodendrocyte precursor cells (OPCs)**, which can mature into myelin-making oligodendrocytes.
- In many chronic MS lesions, OPCs are **present but stuck**: they don't mature. The causes include signals that hold them back (LINGO-1, RGMa, the muscarinic M1 receptor), inflammation, debris, and **ageing of OPCs**.
- Drugs so far have tried to **release the brakes**:
  - Clemastine and PIPE-307 (M1 receptor)
  - Opicinumab (LINGO-1)
  - Elezanumab (RGMa)
  - Bexarotene (RXR)
  - Metformin (rejuvenating aged OPCs)
- Results are mixed. Small trials with sensitive tests (VEP latency) show signals. Large trials with clinical endpoints have failed. In progressive MS, one clemastine arm caused harm. Details are in [public-data-inventory.md](public-data-inventory.md#1-clinicaltrialsgov).

**The research questions that follow:**
1. **What separates the drugs that showed a signal from those that didn't?** Mechanism, patient group, disease stage, outcome measure.
2. **Which genes and pathways keep OPCs stuck in human MS lesions**, as opposed to in mouse models?
3. **Which approved or late-stage drugs act on those pathways, reach the brain and are safe?** These are repurposing candidates.
4. **Which outcome measures detect remyelination best?** This matters for designing better trials.

## Part 1: Connect the data

Build a small Python pipeline. Each source gets one script that downloads into a **gitignored** folder and writes a tidy, small output that is safe to commit.

```
ms-research/
├── catalog/sources.csv          # existing: where each source lives and its rules
├── docs/                        # inventory, plan, findings
├── src/msr/
│   ├── fetch/                   # one module per source
│   │   ├── clinicaltrials.py    #   ClinicalTrials.gov API v2
│   │   ├── pubmed.py            #   E-utilities + Europe PMC
│   │   ├── geo.py               #   GEO search + download
│   │   ├── cellxgene.py         #   CELLxGENE Census
│   │   ├── gwas.py              #   GWAS Catalog v2 + summary statistics
│   │   ├── opentargets.py       #   GraphQL
│   │   ├── chembl.py            #   REST
│   │   └── lincs.py             #   L1000 signatures
│   └── analysis/                # reusable analysis code
├── notebooks/                   # exploration, one per research track
├── data/
│   ├── raw/        (gitignored) # downloads, never committed
│   └── derived/                 # small tables, committed only if the license allows
└── pyproject.toml               # dependencies
```

**Shared rules:**
- Every fetch records the **date, query and source version** in a small manifest next to the output.
- Use a cache so APIs aren't hit over and over, and respect each API's rate limits.
- A licence check stops data from a `no` or `unverified` source being written into `data/derived/`.
- **Join keys:**

  | What | Key |
  |---|---|
  | Genes | Ensembl gene ID |
  | Drugs | ChEMBL ID |
  | Trials | NCT ID |
  | Papers | PMID or DOI |
  | Datasets | GEO accession (GSE) |

**Core tables to build first:**

| Table | Built from | Content |
|---|---|---|
| `trials_remyelination` | ClinicalTrials.gov, PubMed | Each myelin-repair trial: drug, target, phase, population, outcome measure, result, linked paper |
| `targets_repair` | Literature, Open Targets, Human Protein Atlas | Genes with evidence of controlling OPC maturation, with expression in OPCs and oligodendrocytes |
| `drugs_targets` | ChEMBL, Open Targets | Which approved or clinical-stage drugs hit each repair target, potency, brain penetration |
| `lesion_signatures` | GEO, CELLxGENE | Genes up or down in OPCs and oligodendrocytes in MS lesions vs control tissue |
| `datasets_index` | GEO, CELLxGENE, OpenNeuro | Hand-checked list of the most useful datasets, with sample sizes |

## Part 2: Research tracks

### Track A: What has been tried (start here)
- Build `trials_remyelination` for every myelin-repair trial, including those outside ClinicalTrials.gov (ISRCTN, the WHO registry).
- Compare trials by mechanism, MS type, age, disease duration, outcome measure and sample size.
- **Output:** a written review of why trials succeeded or failed, and what that implies for picking targets and designing trials.
- **Effort:** low. **Payoff:** high, because it frames everything else.

### Track B: Map the "stuck OPC" biology in human tissue
- Start from the CELLxGENE "Oligodendrocytes in MS" dataset and the human single-nucleus MS lesion series in GEO.
- Compare OPC and oligodendrocyte states in lesions vs normal white matter. Which maturation genes are switched off, and which inhibitory signals are switched on?
- Check the findings against the cuprizone time courses: which genes turn on when mice repair myelin naturally?
- **Output:** `lesion_signatures`, a "stuck OPC" gene signature and a "successful repair" gene signature.

### Track C: Rank repair targets
- Combine evidence for each gene:
  - It controls OPC maturation (literature, mouse models)
  - It changes in human MS lesions (Track B)
  - It is expressed in OPCs (Human Protein Atlas)
  - It has a genetic link to MS severity (GWAS Catalog)
  - It can be targeted by a drug (ChEMBL, Open Targets)
- **Check that the method works** before using it: known targets (CHRM1, LINGO1, RXRG, RGMA) should rank near the top.
- **Output:** `targets_repair` with transparent scores.

### Track D: Drug repurposing
- **Approach 1: by target.** For the top targets from Track C, list approved drugs that hit them (ChEMBL), and filter for brain penetration and safety (drug labels).
- **Approach 2: by signature.** Use LINCS L1000 to find compounds whose effect resembles OPC maturation, or reverses the "stuck OPC" signature from Track B.
- **Check that the method works:** compounds already shown to promote myelination in lab screens should score well. Examples are clemastine, benztropine, miconazole and clobetasol.
- **Safety filter:** the TRAP-MS clemastine result shows that a drug can help myelin and still cause harm (inflammation through pyroptosis). Flag candidates with inflammatory or pyroptosis-related effects.
- **Output:** a shortlist of candidates, each with its evidence and risks.

### Track E: Outcome measures and imaging (later)
- Review how sensitive each repair outcome measure is, using trial results and papers: VEP latency, MTR, myelin water imaging, myelin PET, NfL.
- Optionally, explore OpenNeuro MS datasets that include myelin-sensitive MRI.
- **Output:** a guide to which tests detect remyelination best.

## Milestones

| Step | Deliverable |
|---|---|
| 1 ✅ | Python project setup (`pyproject.toml`, `src/`, `.gitignore` for `data/raw/`) and the ClinicalTrials.gov and PubMed fetchers. Done 2026-11-12: 102 trials and 1,740 papers fetched. |
| 2 ✅ | Track A: complete `trials_remyelination` table and written trial review. Done 2026-11-12: 105 trials reviewed; see [track-a-trial-review.md](track-a-trial-review.md). |
| 3 | Open Targets, ChEMBL and Human Protein Atlas fetchers; first `targets_repair` table (Track C, literature-based) |
| 4 | CELLxGENE/GEO single-cell analysis (Track B); feed results into target ranking |
| 5 | Drug repurposing (Track D), first by target, then by signature with LINCS |
| 6 | Write-up of the ranked targets and drugs, with evidence, caveats and open questions |

## Rules that apply throughout

- Only public data. Raw downloads go in `data/raw/` (gitignored). Commit derived tables only if the source license allows it (see `catalog/sources.csv`).
- No individual-level data in the repo, even from public datasets. Commit summaries only.
- Record where every number came from (query, date, source version).
- Every analysis has a check with a known answer, and known positives must rank well before the results are trusted.
- Findings are hypotheses for researchers to test, not treatment advice.
