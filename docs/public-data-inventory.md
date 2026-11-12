# Public MS data inventory

This page lists what each **public** source in the [catalog](../catalog/sources.csv) contains, how much of it there is, and how useful it is for **myelin repair (remyelination)** research. Access-controlled registries (MSBase, NARCOMS, UK MS Register, UK Biobank) are left out for now.

Counts were taken from each source's API on **2026-11-12** using the queries shown. The sources grow over time, so re-run the queries to update the counts.

## Summary

| Source | What it holds | How much (MS-related) | Value for myelin repair | How to connect |
|---|---|---|---|---|
| ClinicalTrials.gov | Trial records and posted results | 3,964 studies; 599 with results; 66 that mention remyelination | **High:** what has been tried and what happened | REST API v2 (JSON) |
| PubMed | Paper citations and abstracts | 79,413 MS papers; 1,740 on MS + remyelination | **High:** evidence and mechanisms | NCBI E-utilities |
| Europe PMC *(new)* | Open-access full text | Per query; CC BY/CC0 subset can be text-mined | **High:** text mining of methods and results | REST API, bulk FTP |
| GEO | Gene activity datasets | 1,119 MS series (647 human); 216 single-cell; 100 cuprizone, 390 EAE | **High:** oligodendrocyte biology in lesions and models | E-utilities + file download |
| CELLxGENE *(new)* | Curated single-cell datasets | 4 datasets with MS donors, including "Oligodendrocytes in MS" (17,799 nuclei) | **High:** oligodendrocyte states in MS tissue | Census API (Python) |
| GWAS Catalog | Genetic association results | 103 MS studies; 1,530 associations; 41 with full summary statistics | Medium: MS risk genes are mostly immune genes | REST API v2 + FTP |
| Open Targets *(new)* | Target–disease evidence, drugs | 6,347 targets linked to MS; 279 drugs and candidates | **High:** ranking repair targets by evidence | GraphQL API, bulk files |
| ChEMBL *(new)* | Drugs, targets, bioactivity | 213 MS drug-indication records | **High:** which compounds hit a repair target | REST API |
| LINCS L1000 *(new)* | Gene-activity responses to ~20k compounds | About 1.67 million profiles (two GEO series) | **High:** drug repurposing by signature | GEO files (large) |
| OpenNeuro | Brain imaging datasets (BIDS format) | 130 datasets match the keyword "multiple sclerosis" | Medium: myelin imaging measures | Web + API, `openneuro-py` |
| Human Protein Atlas *(new)* | Gene and protein expression by cell type | Every human gene, including oligodendrocyte cell types | Medium: checking target expression | Downloads + API |
| openFDA / DailyMed | US drug labels | 1,572 labels mention MS in their indications (60 distinct generic names) | Low: none of the approved drugs repair myelin | openFDA API |
| EMA EPARs | EU drug assessments | MS medicines (not counted) | Low | Downloadable medicines table |
| Atlas of MS | Country-level statistics | 6 topic areas per country | Low for repair; context only | Web site |
| Global Burden of Disease | Modelled burden estimates | MS by country, age, sex and year | Low for repair; context only | Results tool (account) |

*(new)* marks sources this page proposes adding to the catalog.

---

## 1. ClinicalTrials.gov

**What's in it:** one record per study, covering conditions, interventions, phase, status, enrollment, eligibility, primary and secondary outcome measures, and dates. About 15% of MS records also have **posted results**: participant flow, baseline data, outcome values and adverse events.

**How much** (query `cond = multiple sclerosis`):
- 3,964 studies in total, of which 2,803 are interventional
- 599 have posted results
- 430 are recruiting now
- 66 mention remyelination, "remyelinating" or "myelin repair"

**Tests used to measure myelin repair in trials** (taken from the outcome measures of those trials):
- **Visual evoked potential (VEP) latency:** how fast a signal travels along the optic nerve. It speeds up when myelin returns, and it was the primary outcome in ReBUILD and CCMR-One.
- **Magnetization transfer ratio (MTR):** an MRI measure sensitive to myelin.
- **Myelin water imaging and ihMT:** newer MRI methods that are more specific to myelin.
- **PET with [18F]-florbetaben:** a tracer that binds myelin.
- **Optical coherence tomography (OCT):** the thickness of retinal layers.
- **Clinical scales:** EDSS, timed 25-foot walk, 9-hole peg test, low-contrast visual acuity.
- **Blood biomarkers:** serum neurofilament light (NfL).

**Myelin-repair drugs already tested** (looked up by drug name):

| Drug | How it's meant to work | Trials | What happened |
|---|---|---|---|
| Clemastine | Antihistamine; blocks the muscarinic M1 receptor, so OPCs mature | ReBUILD (NCT02040298, n=50); others recruiting | ReBUILD met its primary endpoint: VEP delay 1.7 ms/eye shorter ([Lancet 2017](https://pubmed.ncbi.nlm.nih.gov/29029896/)). **In progressive MS, the TRAP-MS clemastine arm was stopped after disability got worse faster** ([J Clin Invest 2025](https://pubmed.ncbi.nlm.nih.gov/40371642/)). |
| Opicinumab (anti-LINGO-1) | Blocks a brake on myelination | RENEW, SYNERGY (n=419), AFFINITY (n=263) | Did not meet primary endpoints ([SYNERGY](https://pubmed.ncbi.nlm.nih.gov/31285147/), [AFFINITY](https://pubmed.ncbi.nlm.nih.gov/41454463/)) |
| Elezanumab (anti-RGMa) | Blocks a repulsive guidance signal | RADIUS-R (n=208), RADIUS-P (n=123) | Did not meet primary endpoints ([Ann Neurol 2025](https://pubmed.ncbi.nlm.nih.gov/40698976/)) |
| Bexarotene | Activates the RXR-gamma receptor | CCMR-One (UK trial, not on ClinicalTrials.gov) | Signal on VEP latency that lasted at follow-up ([Mult Scler 2024](https://pubmed.ncbi.nlm.nih.gov/38426437/)); poorly tolerated |
| Metformin + clemastine | Rejuvenates aged OPCs, plus M1 blocking | CCMR-Two (NCT05131828, n=70), completed | Results not yet posted on ClinicalTrials.gov |
| PIPE-307 | Selective M1 receptor blocker | Phase 2 (NCT06083753, n=182), completed | Results not yet posted on ClinicalTrials.gov |
| Temelimab | Blocks HERV-W Env protein | Several phase 2 trials | Mixed; mainly an imaging signal |
| CNM-Au8 | Gold nanocrystals that support cell energy | VISIONARY-MS (terminated) | Inconclusive |
| GSK239512 | Histamine H3 receptor blocker | Phase 2 (n=131) | Small effect on lesion MTR |
| Others | Liothyronine (thyroid hormone), bazedoxifene, domperidone, testosterone, ifenprodil, PRO-1562, vagus nerve stimulation, exercise | Small or early trials | Mostly pending |

**Connect:** `https://clinicaltrials.gov/api/v2/studies` (JSON, no key needed). **Reuse:** conditional. Credit ClinicalTrials.gov, show the date the data was processed, and describe any changes.

**Gap:** trials registered only in Europe or the UK, such as CCMR-One (ISRCTN), are missing. Add **ISRCTN** and the **WHO ICTRP** registry to the catalog later.

## 2. PubMed and Europe PMC

**What's in it:** PubMed holds citations, abstracts, MeSH subject tags and publication types. Europe PMC adds **full text** for open-access papers, plus annotations for genes, diseases and chemicals mined from the text.

**How much:**
- 79,413 papers tagged with the MeSH term for multiple sclerosis
- 4,747 of them are clinical trial reports
- 23,586 have free full text
- 6,825 are about remyelination in general, 1,740 of them on remyelination in MS

**Connect:** NCBI E-utilities (`esearch`, `efetch`); Europe PMC REST API with a `LICENSE` filter. **Reuse:** store PMIDs, titles and your own notes. Store full text only for CC BY or CC0 articles.

## 3. GEO (Gene Expression Omnibus)

**What's in it:** raw and processed data on gene activity, measured by microarray, RNA-seq or single-cell sequencing. Each series includes sample metadata, such as tissue, lesion type and disease.

**How much** (series-level records):
- 1,119 MS series, 647 of them in humans
- 216 single-cell or single-nucleus MS series
- 100 cuprizone series (a mouse model of demyelination and remyelination)
- 390 EAE series (a mouse model of the immune attack)
- 3,126 series mentioning remyelination, oligodendrocytes or demyelination (any species)

**Why it matters:** human MS lesion data shows whether OPCs are present but **stuck before they mature**. Cuprizone time courses show which genes switch on during natural repair.

**Connect:** E-utilities (`db=gds`) to find series, then download the files from NCBI FTP. **Reuse:** depends on each dataset. Commit the list of accessions and your derived results, not the raw files.

## 4. CELLxGENE Discover

**What's in it:** single-cell datasets standardised to one format, with cell types, tissue and disease labels.

**How much:** 4 datasets include MS donors, about 4.9 million cells in total (this includes control donors and other diseases). The most relevant is **"Oligodendrocytes in MS"** (17,799 nuclei from MS and control white matter). Two large prefrontal-cortex cohorts include some MS donors.

**Connect:** the `cellxgene-census` Python package. **Reuse:** CC BY 4.0, with attribution. Confirm the license on each dataset.

## 5. GWAS Catalog

**What's in it:** genetic variants linked to MS, with effect sizes, p-values, mapped genes and ancestry.

**How much:** 103 studies and 1,530 associations. 41 studies have full summary statistics, which are CC0 unless the study says otherwise. The studies include MS **severity** studies, which matter more for repair than studies of MS risk.

**Note:** MS **risk** genes point mainly at the immune system. Genes for disease **severity**, which may reflect how well the brain copes with damage and repairs itself, are the more relevant thread for myelin repair.

**Connect:** REST API v2 (`/gwas/rest/api/v2/studies?efo_trait=multiple sclerosis`) and the FTP site for summary statistics. (The old API version is retired.)

## 6. Open Targets Platform

**What's in it:** for each disease, the genes and proteins (targets) linked to it, scored by evidence type (genetics, literature, animal models, known drugs), plus drugs and clinical candidates.

**How much:** 6,347 targets linked to MS (overall node, `EFO_0803536`); 1,011 for relapsing-remitting MS; 467 for chronic progressive MS. 279 drugs and clinical candidates.

**Note:** the top-ranked MS targets are all immune targets (S1PR1, CD20/MS4A1, IL2RA, ITGA4). **Repair targets such as CHRM1, LINGO1, RXRG and RGMA rank low**, so a repair-focused ranking has to be built separately. This is a central part of the plan.

**Connect:** GraphQL API (`api.platform.opentargets.org/api/v4/graphql`) or bulk Parquet files. **Reuse:** CC0. Data that Open Targets integrates from ChEMBL keeps ChEMBL's license (CC BY-SA 3.0).

## 7. ChEMBL

**What's in it:** drugs and research compounds, their targets, measured potency (bioactivity), mechanisms of action and approved indications.

**How much:** 213 drug-indication records for MS. Millions of bioactivity records overall, which matter for finding compounds that hit repair targets.

**Connect:** REST API (`ebi.ac.uk/chembl/api/data`). **Reuse:** CC BY-SA 3.0, which means attribution and share-alike.

## 8. LINCS L1000 / Connectivity Map

**What's in it:** how gene activity changes in cell lines after exposure to about 20,000 compounds and genetic perturbations.

**How much:** GSE92742 (Phase I, about 1.3 million profiles) and GSE70138 (Phase II, about 354,000 profiles). The main signature file is about 20 GB.

**Why it matters:** this enables **signature matching**, finding drugs whose effect looks like "OPC maturation" or reverses the "stuck OPC" pattern seen in MS lesions. Clemastine, benztropine and miconazole are known hits from lab screens and can be used to test whether the method works.

**Connect:** GEO downloads. **Reuse:** follow GEO terms; keep the data outside the repo because of its size.

## 9. OpenNeuro

**What's in it:** brain MRI and PET datasets in BIDS format, some with MS lesion masks and myelin-sensitive sequences.

**How much:** 130 datasets match the keyword "multiple sclerosis". This keyword match includes datasets that only mention MS, so the true number of MS cohorts is smaller and needs reviewing.

**Connect:** web search plus `openneuro-py` or DataLad. **Reuse:** CC0 for new datasets. Downloading requires agreeing in OpenNeuro's site banner **never to try to re-identify participants**.

## 10. Human Protein Atlas

**What's in it:** RNA and protein expression for every human gene, including brain single-nucleus data with oligodendrocyte, OPC and committed-OPC cell types. For example, OLIG2 is enhanced in OPCs and MOBP is enriched in oligodendrocytes.

**Connect:** downloadable TSV files and per-gene pages. **Reuse:** license not yet confirmed; check before copying.

## 11. Drug labels (openFDA / DailyMed) and EMA

**What's in it:** approved uses, dosing, safety and pivotal trial summaries.

**How much:** 1,572 US labels mention MS in their indications, but these cover only 60 distinct generic names. Most of the labels are steroids, generics and products for symptoms.

**Note:** none of the approved MS drugs is approved for repairing myelin. These sources matter mainly for **safety and brain penetration** of repurposing candidates.

## 12. Atlas of MS and Global Burden of Disease

**What's in it:** the Atlas of MS covers, per country, the number of people with MS, newly diagnosed people and children with MS; the diagnostic criteria used; symptom management and rehabilitation; healthcare provision (including palliative care); national standards; and World Bank income band. Global Burden of Disease adds modelled prevalence, incidence, deaths and DALYs by age, sex and year.

**Value:** context, such as how many people a myelin-repair therapy could help. Neither is used for discovery.

---

## Query reference

All counts above came from these queries on 2026-11-12:

```
ClinicalTrials.gov  /api/v2/studies?query.cond=multiple sclerosis&countTotal=true
PubMed              "multiple sclerosis"[MeSH] [AND remyelination[MeSH] OR remyelination[tiab]]
GEO                 "multiple sclerosis" AND gse[ETYP] [AND "Homo sapiens"[Organism]]
GWAS Catalog        /gwas/rest/api/v2/studies?efo_trait=multiple sclerosis
Open Targets        disease(efoId:"EFO_0803536") { associatedTargets { count } }
ChEMBL              /drug_indication?mesh_heading__iexact=Multiple Sclerosis
CELLxGENE           /curation/v1/datasets, filtered to disease label "multiple sclerosis"
openFDA             /drug/label.json?search=indications_and_usage:"multiple sclerosis"
OpenNeuro           keyword search "multiple sclerosis" on openneuro.org
```
