"""Open Targets Platform: druggability (tractability) and drugs for each target.

License: CC0 1.0. Drug data inside Open Targets comes from ChEMBL (CC BY-SA 3.0).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..http import post_json

API = "https://api.platform.opentargets.org/api/v4/graphql"
BATCH = 25

QUERY = """
query Targets($ids: [String!]!) {
  targets(ensemblIds: $ids) {
    id
    approvedSymbol
    tractability { modality label value }
    drugAndClinicalCandidates {
      count
      rows { maxClinicalStage drug { id name } }
    }
  }
}
"""

# Clinical stages, from furthest to earliest.
APPROVED = {"APPROVAL", "PHASE_4"}
CLINICAL = APPROVED | {"PHASE_3", "PHASE_2_3", "PHASE_2", "PHASE_1_2", "PHASE_1", "EARLY_PHASE_1"}


@dataclass
class TargetInfo:
    ensembl: str
    symbol: str
    small_molecule_tractable: bool = False
    antibody_tractable: bool = False
    approved_drugs: list[str] = field(default_factory=list)
    clinical_drugs: list[str] = field(default_factory=list)

    @property
    def druggability(self) -> int:
        """0 = no known route, 1 = tractable, 2 = has clinical-stage drugs, 3 = has approved drugs."""
        if self.approved_drugs:
            return 3
        if self.clinical_drugs:
            return 2
        if self.small_molecule_tractable or self.antibody_tractable:
            return 1
        return 0


def _tractable(tractability: list[dict], modality: str) -> bool:
    # Count a target as tractable if any evidence bucket for the modality is true,
    # except purely clinical ones (those are covered by the drug lists).
    return any(t["value"] for t in tractability if t["modality"] == modality)


def fetch_targets(ensembl_ids: Iterable[str], use_cache: bool = True) -> dict[str, TargetInfo]:
    ids = sorted(set(ensembl_ids))
    out: dict[str, TargetInfo] = {}
    for start in range(0, len(ids), BATCH):
        batch = ids[start : start + BATCH]
        data = post_json(API, {"query": QUERY, "variables": {"ids": batch}}, use_cache=use_cache)
        if data.get("errors"):
            raise RuntimeError(f"Open Targets error: {data['errors'][0].get('message')}")
        for t in data["data"]["targets"] or []:
            rows = (t.get("drugAndClinicalCandidates") or {}).get("rows") or []
            stage_drugs = [(r["maxClinicalStage"], r["drug"]["name"]) for r in rows if r.get("drug")]
            tract = t.get("tractability") or []
            out[t["id"]] = TargetInfo(
                ensembl=t["id"],
                symbol=t["approvedSymbol"],
                small_molecule_tractable=_tractable(tract, "SM"),
                antibody_tractable=_tractable(tract, "AB"),
                approved_drugs=sorted({d for s, d in stage_drugs if s in APPROVED}),
                clinical_drugs=sorted({d for s, d in stage_drugs if s in CLINICAL}),
            )
    return out
