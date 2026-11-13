# ms-research

A place to bring together public research and data on multiple sclerosis (MS).

## Contents

- [`catalog/`](catalog/): a list of MS datasets, registries, trial records and statistics, with their access rules and licenses.
- [`docs/public-data-inventory.md`](docs/public-data-inventory.md): what each public source contains, how much, and how useful it is for myelin repair research.
- [`docs/myelin-repair-plan.md`](docs/myelin-repair-plan.md): the plan for connecting these sources and researching ways to restore myelin (remyelination).

- [`docs/track-a-trial-review.md`](docs/track-a-trial-review.md): review of the 105 myelin-repair trials so far, and what their results suggest.
- [`docs/track-c-target-ranking-v1.md`](docs/track-c-target-ranking-v1.md): first attempt at ranking myelin-repair target genes, why it doesn't work yet, and what to fix.
- [`docs/track-b-lesion-opcs.md`](docs/track-b-lesion-opcs.md): how myelin precursor cells (OPCs) differ in MS lesions, from two single-nucleus RNA studies.
- [`data/curation/`](data/curation/): hand-made review files (trial classifications and trials from registries other than ClinicalTrials.gov).
- [`src/msr/`](src/msr/): Python code that fetches public data. Raw downloads go to `data/raw/` (gitignored). Small shareable tables go to `data/derived/`, each with a `.manifest.json` recording the source, query, date and license.
- [`data/derived/`](data/derived/): `trials_remyelination.csv` (myelin-repair trials from ClinicalTrials.gov) and `pubmed_ms_remyelination.csv` (citations of papers on MS and remyelination).

## Setup

Needs Python 3.10 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

Fetch or refresh the data:

```bash
.venv/bin/python -m msr.fetch.clinicaltrials
.venv/bin/python -m msr.fetch.pubmed
.venv/bin/python -m msr.analysis.trials   # combine trials with the hand review
.venv/bin/python -m msr.analysis.targets  # rank target genes (about 12 minutes the first time)
.venv/bin/pip install -e ".[analysis]"   # extra packages for single-cell analysis
.venv/bin/python -m msr.analysis.lesions  # OPCs in MS lesions (downloads about 120 MB)
```

Some derived tables combine several sources. Each one's `.manifest.json` lists every source and license. Tables that include ChEMBL drug data are shared under CC BY-SA 3.0.

Add `--refresh` to skip the local cache. The derived tables are written only if `catalog/sources.csv` says the source may be shared. Data from access-controlled sources is always refused.

## Privacy

This repo is public. It holds only public material: published results, openly licensed data, code and notes. It never holds personal health information, patient records or data from access-controlled sources. Those belong in a separate private space.
