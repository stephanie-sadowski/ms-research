# MS sources catalog

A list of public and access-controlled sources on multiple sclerosis: datasets, registries, trial records, statistics and literature indexes. The catalog itself is in [`sources.csv`](sources.csv); GitHub shows it as a table.

The catalog **describes** sources. It doesn't re-host them. For each source it records where the source lives, who can access it and whether its data may be shared again.

## Columns

| Column | Meaning |
|---|---|
| `id` | Short unique slug, for example `gwas-catalog` |
| `name` | Name of the source |
| `category` | `trials`, `literature`, `epidemiology`, `genetics`, `omics`, `imaging`, `registry`, `cohort`, `drug-info`, `targets`, `catalog` |
| `url` | Main landing page |
| `access` | `open` (anyone can use it), `registration` (free account needed) or `controlled` (application or data use agreement) |
| `data_level` | `aggregate` (summary figures), `individual` (one row per person or sample), `metadata` (descriptions or citations only) or `mixed` |
| `redistribution` | Whether the data may be copied into this public repo: `yes`, `conditional` (allowed if you meet the conditions in `notes`), `no`, `per-dataset` or `unverified` |
| `license` | License or terms of use, or `unverified` |
| `terms_url` | Page where the license or access terms were checked |
| `description` | What it holds that's useful for MS research |
| `notes` | Caveats, APIs or other tips |
| `verified` | Date (YYYY-MM-DD) someone last checked the URL, access and license against the source. Leave it empty if nobody has checked. |

## Rules for this public repo

- **Data from a `controlled` source never goes in this repo.** That holds even when the data is de-identified, and it applies to summary tables taken from that data too. Such data belongs in the separate private space, which isn't set up yet.
- **Copy data in only when `redistribution` is `yes`** and the license has been checked (`verified` is filled in). Keep the attribution with the data.
- **Prefer links and download scripts over copies.** For larger data, write a script that downloads it into a gitignored folder.
- **Treat individual-level public data with care.** Combining it with other public data can sometimes identify people.
- **Don't commit paper PDFs.** Cite papers by DOI or PMID instead.

## Status

On 2026-11-12, 11 of the first 15 entries were checked against their official sites or terms pages and have a `verified` date. The other 4 still need confirming: `imsgc` (how to access its data), `ms-data-alliance` (access), `narcoms` (how to request data) and `dailymed` (copyright of label text).

Six sources for myelin-repair research were added the same day: `open-targets`, `chembl`, `cellxgene`, `lincs-l1000`, `europe-pmc` and `human-protein-atlas`. Only Open Targets' license has been confirmed from its own documentation. The others are based on secondary sources and need checking.

What each public source contains, and how much, is described in [docs/public-data-inventory.md](../docs/public-data-inventory.md).

These notes summarize each source's terms. They aren't legal advice. Before copying data into this repo, read the page in `terms_url`.
