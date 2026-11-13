# Track C, version 1: first target ranking

*Run 2026-11-12. This is part of the [myelin repair plan](myelin-repair-plan.md).*

**Bottom line: this first ranking doesn't work yet.** It ranked the genes with human repair evidence above the genes that failed in human trials in only 3 of 6 pairs, which is no better than chance. The reasons are clear and fixable, and they're useful lessons in themselves. Don't treat the current top of the list as a set of repair candidates.

## What was done

`python -m msr.analysis.targets` scored **1,229 candidate genes**. Genes entered if they were mentioned in at least 3 of 11,122 papers on remyelination and OPC maturation, or if they were clearly expressed in the oligodendrocyte lineage.

| Evidence | Weight | Source |
|---|---|---|
| Literature: how many repair papers mention the gene, and how specific that is | 40% | PubTator gene tags in PubMed |
| Expression in OPCs or oligodendrocytes, and how specific it is to them | 30% | Human Protein Atlas v26.0, human brain single-nucleus RNA |
| Druggability: approved drugs, clinical drugs, or tractable | 30% | Open Targets |

Human trial results from [Track A](track-a-trial-review.md) were kept out of the score so they could check it.

Outputs:
- [`data/derived/targets_repair.csv`](../data/derived/targets_repair.csv): all genes with their scores.
- [`data/derived/targets_repair_drugs.csv`](../data/derived/targets_repair_drugs.csv): drugs for the top 50 genes, with how they act, from ChEMBL.

## Known-answer check: failed

| Gene | Human evidence | Rank (of 1,229) |
|---|---|---|
| LINGO1 | Negative (opicinumab missed) | **18** |
| RXRG | Positive (bexarotene, partial) | 62 |
| CHRM1 | Positive (clemastine, ReBUILD) | 81 |
| HRH3 | Positive (GSK239512, partial) | 235 |
| RGMA | Negative (elezanumab missed) | 392 |

Positives beat negatives in 3 of 6 pairs. That's no better than chance.

**Caution:** with only 5 known answers, this check is weak either way. It shouldn't be "fixed" by adjusting weights until these 5 genes come out in the right order; that would just fit the method to 5 examples.

## Why it failed

1. **Literature rewards popularity, not results.** LINGO1 has 77 repair papers, much of it written while opicinumab was being developed. CHRM1 has 7, because most clemastine papers name the drug rather than the gene. Paper counts measure attention, and attention isn't evidence that something works in people.

2. **Healthy-brain expression is the wrong reference.** In the Human Protein Atlas, CHRM1, RXRG and HRH3 are all expressed at low levels in OPCs (CHRM1: 3.1 nCPM, mostly neuronal). LINGO1 is high (100 nCPM). Low baseline expression doesn't rule a gene out as a target: a receptor needs only modest expression for a drug to act on it.

3. **The top of the list is full of myelin building blocks, not regulators.** MBP, PLP1, MOG, MAG, CNP and MYRF are the *products* of myelination or markers of it. They score high on literature and expression, but they aren't drug targets for promoting repair.

4. **Direction is ignored, and this can point the wrong way.** PDGFRA ranks first, partly because it has approved drugs. But those drugs (sunitinib, avapritinib, olaratumab) **block** PDGFRA, and PDGFRA signalling is what keeps OPCs multiplying. Blocking it would likely hurt repair. A ranking without direction can recommend the opposite of what's needed.

5. **"Approved drug" can mean an unrelated drug.** APP, PSEN1, IDH1 and ARSA score full marks for druggability because of drugs for Alzheimer's, cancer or leukodystrophy. Those drugs have nothing to do with OPCs.

## Things worth noting anyway

- **S1PR5 (rank 5)** is expressed in oligodendrocytes and is hit by MS drugs already in use: ozanimod, etrasimod, fingolimod and siponimod. Whether S1P drugs help or hinder myelin repair through S1PR5 is an open question with an existing evidence base.
- **GPR17 (rank 36)** is one of the most OPC-specific genes (25× higher than in any other brain cell type) and is a known brake on OPC maturation. It has no clinical drugs yet, so it could be a target worth developing.
- **LPAR1 (rank 22)** is the target of PIPE-791, which is already in an MS imaging study (Track A).

## What version 2 needs

In order of expected impact:

1. **Use direction and known biology.** Use Gene Ontology terms for *positive* and *negative* regulation of oligodendrocyte differentiation and myelination, so each gene gets a known role (brake or accelerator). Then accept only drugs that push it the right way (an antagonist for a brake, an agonist for an accelerator).
2. **Separate regulators from building blocks.** Down-weight structural myelin proteins and markers.
3. **Count drug mentions as well as gene mentions,** so clemastine papers count toward CHRM1, bexarotene toward RXRG, and so on. PubTator also tags chemicals.
4. **Replace healthy-brain expression with MS lesion data** (Track B): is the gene changed in OPCs inside chronic lesions?
5. **Make druggability relevant:** credit drugs that reach the brain and are safe for long-term use, not just any approved drug.
6. **Test robustness:** show how the ranking changes with different weights, instead of picking one set.

Track B (MS lesion single-cell data) directly addresses points 4 and 2, so it could come before version 2. Points 1, 3 and 5 can be done without it.
