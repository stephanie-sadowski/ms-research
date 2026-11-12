# Track A: what has been tried to repair myelin

*Reviewed 2026-11-12. This is part of the [myelin repair plan](myelin-repair-plan.md).*

## How this was done

1. **Search.** `msr.fetch.clinicaltrials` found 104 trials on ClinicalTrials.gov, using a keyword search for remyelination plus searches for 15 known repair drugs. One more trial was added by hand: CCMR-One (bexarotene), which is registered only in the UK registry (ISRCTN14265371).
2. **Review.** Each of the 105 trials was read and classified by hand in [`data/curation/trial_review.csv`](../data/curation/trial_review.csv). The review records its relevance to myelin repair, the therapy, how it is meant to work, the gene targets, the patient group, the outcome measure and the published result, with the PMID of the source paper.
3. **Combine.** `python -m msr.analysis.trials` checks that every trial has exactly one valid review row and writes [`data/derived/trials_repair_curated.csv`](../data/derived/trials_repair_curated.csv).

| Relevance | Trials | Meaning |
|---|---|---|
| `repair_efficacy` | 30 | Tests whether a therapy repairs myelin or restores function |
| `repair_safety` | 30 | Safety or dosing study of a repair therapy |
| `repair_secondary` | 13 | Another therapy (usually immune) with repair as a secondary measure |
| `imaging_method` | 10 | Develops a way to measure myelin |
| `other` | 22 | Not about repair (loose search matches, such as rehabilitation studies) |

The `primary_met` column records whether each efficacy trial met its main goal:
- `yes`: met its primary endpoint.
- `partial`: missed the primary endpoint, but a pre-planned repair measure was positive.
- `no`: missed the primary endpoint, with no repair signal.
- `harm`: stopped for harm.
- `pending`: results not out yet.
- `unknown`: finished, but results haven't been found yet.

## Results so far

Of the 30 efficacy trials, **14 have a known result**:

| Result | Trials | Which |
|---|---|---|
| Met primary endpoint | 1 | Clemastine (ReBUILD) |
| Partial | 3 | Opicinumab (RENEW), GSK239512, bexarotene (CCMR-One) |
| Missed | 9 | Opicinumab (SYNERGY, AFFINITY, RENEWED), elezanumab (RADIUS-R, RADIUS-P), temelimab (CHANGE-MS), domperidone (×2), IVIG |
| Harm | 1 | Clemastine in progressive MS (TRAP-MS arm) |
| Pending | 10 | CCMR-Two, PIPE-307 (VISTA), clemastine (×3), metformin, bazedoxifene, ifenprodil, testosterone, PRO-1562 |
| Unknown | 6 | CNM-Au8 (×3), exercise, transorbital stimulation, clemastine (RESTORE, terminated) |

### Key trials

| Therapy | Target | Trial | n | Patients | Outcome measure | Result |
|---|---|---|---|---|---|---|
| Clemastine | CHRM1 | ReBUILD | 50 | Relapsing MS with old optic nerve damage | VEP latency | **Met:** 1.7 ms/eye faster ([PMID 29029896](https://pubmed.ncbi.nlm.nih.gov/29029896/)) |
| Clemastine | CHRM1 | TRAP-MS arm | 9 | Progressive MS | Disability progression | **Harm:** stopped when 3 of 9 hit safety limits ([PMID 40371642](https://pubmed.ncbi.nlm.nih.gov/40371642/)) |
| Bexarotene | RXRG | CCMR-One | 52 | Relapsing MS | Lesion MTR | **Partial:** MTR missed; VEP latency improved, still better at 27 months; poorly tolerated ([PMID 34418398](https://pubmed.ncbi.nlm.nih.gov/34418398/), [38426437](https://pubmed.ncbi.nlm.nih.gov/38426437/)) |
| Opicinumab | LINGO1 | RENEW | 82 | First optic neuritis | VEP latency | **Partial:** −3.5 ms in all patients (p=0.33); −7.6 ms in patients who followed the protocol (p=0.050) ([PMID 28229892](https://pubmed.ncbi.nlm.nih.gov/28229892/)) |
| Opicinumab | LINGO1 | SYNERGY | 419 | Relapsing MS | Disability composite | **Missed:** no dose-response; middle doses did best ([PMID 31285147](https://pubmed.ncbi.nlm.nih.gov/31285147/)) |
| Opicinumab | LINGO1 | AFFINITY | 263 | Relapsing MS | Disability composite | **Missed:** p=0.148; larger effect in older people and those with longer disease ([PMID 41454463](https://pubmed.ncbi.nlm.nih.gov/41454463/)) |
| Elezanumab | RGMA | RADIUS-R / -P | 208 / 123 | Relapsing / progressive MS | Disability composite | **Missed** in both ([PMID 40698976](https://pubmed.ncbi.nlm.nih.gov/40698976/)) |
| GSK239512 | HRH3 | Phase 2 | 131 | Relapsing MS | Lesion MTR | **Partial:** small positive effect (effect size 0.34) ([PMID 27888416](https://pubmed.ncbi.nlm.nih.gov/27888416/)) |
| Temelimab | HERV-W Env | CHANGE-MS | 270 | Relapsing MS | Inflammatory lesions | **Missed;** trends on atrophy and MTR ([PMID 34240656](https://pubmed.ncbi.nlm.nih.gov/34240656/)) |
| Domperidone | DRD2 | Phase 2 | 64 | Secondary progressive MS | Walking | **Missed** (futility) ([PMID 34038379](https://pubmed.ncbi.nlm.nih.gov/34038379/)) |

## What the pattern suggests

These are observations from 14 trial results, not firm conclusions.

1. **Every positive signal came from small trials using sensitive tests in the visual pathway.** ReBUILD, RENEW and CCMR-One all used VEP latency, which measures how fast signals travel along the optic nerve. With n of 50–82, they showed effects. The optic nerve is a good test bed because one lesion can be measured precisely, and the other eye serves as a comparison.

2. **Every large trial with a disability endpoint failed.** SYNERGY, AFFINITY and both RADIUS trials used composite disability scores over a year or more. Possible reasons:
   - The drug doesn't work well enough in humans.
   - Disability scores are too insensitive to detect repair in that time.
   - The wrong patients were studied, such as people whose lesions can't be repaired any more.

   The current data can't separate these reasons, which is a gap worth noting.

3. **The muscarinic M1 receptor (CHRM1) has the strongest human evidence.** It is the target behind ReBUILD's positive result, a third of the pending trials (clemastine, PIPE-307, CCMR-Two) and preclinical work ([PMID 39083422](https://pubmed.ncbi.nlm.nih.gov/39083422/)). PIPE-307's phase 2 (n=182, completed) is the most important result to watch. It is selective for M1, so it will help show whether TRAP-MS's harm came from clemastine's other effects or from blocking M1 itself.

4. **Clemastine may help in one setting and harm in another.** In TRAP-MS, clemastine in progressive MS increased pyroptosis, a form of inflammatory cell death, and disability worsened faster. Repurposing candidates need a safety check for inflammatory effects, especially for progressive MS (see Track D in the plan).

5. **Age matters.** AFFINITY saw larger effects in older patients with longer disease. Metformin trials (CCMR-Two and three others) test whether rejuvenating aged precursor cells unlocks repair. That makes **OPC ageing** an important thread for Track B.

6. **Blocking an inhibitory signal hasn't worked so far.** LINGO-1 and RGMa looked strong in animals, but neither antibody met its primary endpoint in humans. Both act outside the cell. The partial successes (CHRM1, RXRG, HRH3) act through receptors on or inside the precursor cells.

7. **Trials measure repair in different ways, so they're hard to compare.** Trials used VEP, MTR, myelin water fraction (MWF), low-contrast vision, walking and composites. A phase 1 trial reported VEP to be highly repeatable (intraclass correlation 0.84–0.86) ([PMID 32120028](https://pubmed.ncbi.nlm.nih.gov/32120028/)). Track E should compare these measures properly.

8. **Progressive MS is under-studied.** Most efficacy trials enrolled relapsing MS or optic neuritis. Progressive MS, where repair matters most, has few trials, and one of them showed harm.

## What this means for the next tracks

- **Known-answer checks for Tracks C and D.** Targets with human evidence of repair (CHRM1, RXRG, and HRH3 more weakly) should rank high in any target ranking. LINGO1 and RGMA are "worked in animals, failed in humans" examples. A good method should not rank them above CHRM1.
- **Track B priorities:** OPC ageing, and what's different about OPCs in chronic lesions compared with acute ones.
- **Track D safety filter:** flag candidates with inflammatory or pyroptosis-related effects, and treat progressive MS separately.

## Results to watch

- **CCMR-Two** (metformin + clemastine, NCT05131828): completed, results not yet published.
- **PIPE-307 VISTA** (NCT06083753): completed, results not yet posted.
- **Clemastine myelin water trials** (NCT05359653, NCT06065670) and the clemastine optic neuritis trial (NCT02521311).
- **Metformin** (NCT05893225), **bazedoxifene Re-WRAP** (NCT04002934), **ifenprodil** (NCT06330077), **PRO-1562** (NCT07826689).

## Follow-ups

- Fill in the 6 `unknown` results. Some have results posted on ClinicalTrials.gov (for example exercise, NCT04539002), which can be fetched from the API's results section.
- Search the EU trial register and the WHO registry for more trials outside ClinicalTrials.gov.
- Add earlier and newer repair approaches that the drug list misses (for example stem cells used for repair, or human neural precursor cells), using the 2025 systematic review ([PMID 40393003](https://pubmed.ncbi.nlm.nih.gov/40393003/)) as a checklist.
- Have someone with MS clinical expertise check the classifications in `trial_review.csv`. The `partial` and `no` labels involve judgement.
