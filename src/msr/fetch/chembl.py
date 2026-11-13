"""ChEMBL: how drugs act on a target (inhibitor, agonist, antagonist...).

Direction matters for myelin repair: CHRM1 *blockers* (antagonists) help OPCs
mature, while CHRM1 *activators* (agonists) would not. Open Targets lists drugs
per target but not their direction, so this module fills that in.

License: CC BY-SA 3.0. Tables built from this data must credit ChEMBL and be
shared under the same license.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..http import get_json

API = "https://www.ebi.ac.uk/chembl/api/data"


@dataclass
class Mechanism:
    target_chembl_id: str
    molecule_chembl_id: str
    drug_name: str
    action_type: str
    mechanism: str
    max_phase: float | None


def target_ids_for_uniprot(accession: str, use_cache: bool = True) -> list[str]:
    """Single-protein ChEMBL targets for a human UniProt accession."""
    data = get_json(
        f"{API}/target.json",
        {
            "target_components__accession": accession,
            "target_type": "SINGLE PROTEIN",
            "organism": "Homo sapiens",
            "limit": 20,
        },
        use_cache=use_cache,
    )
    return [t["target_chembl_id"] for t in data.get("targets", [])]


def mechanisms_for_target(target_chembl_id: str, use_cache: bool = True) -> list[Mechanism]:
    data = get_json(
        f"{API}/mechanism.json",
        {"target_chembl_id": target_chembl_id, "limit": 1000},
        use_cache=use_cache,
    )
    mechs = data.get("mechanisms", [])
    if not mechs:
        return []
    molecules = sorted({m["molecule_chembl_id"] for m in mechs})
    names: dict[str, tuple[str, float | None]] = {}
    for start in range(0, len(molecules), 50):
        batch = molecules[start : start + 50]
        mol = get_json(
            f"{API}/molecule.json",
            {"molecule_chembl_id__in": ",".join(batch), "limit": 50, "only": "molecule_chembl_id,pref_name,max_phase"},
            use_cache=use_cache,
        )
        for m in mol.get("molecules", []):
            phase = m.get("max_phase")
            names[m["molecule_chembl_id"]] = (m.get("pref_name") or m["molecule_chembl_id"], float(phase) if phase not in (None, "") else None)
    return [
        Mechanism(
            target_chembl_id=target_chembl_id,
            molecule_chembl_id=m["molecule_chembl_id"],
            drug_name=names.get(m["molecule_chembl_id"], (m["molecule_chembl_id"], None))[0],
            action_type=m.get("action_type") or "",
            mechanism=m.get("mechanism_of_action") or "",
            max_phase=names.get(m["molecule_chembl_id"], ("", None))[1],
        )
        for m in mechs
    ]


def mechanisms_for_uniprot(accession: str, use_cache: bool = True) -> list[Mechanism]:
    out: list[Mechanism] = []
    for target_id in target_ids_for_uniprot(accession, use_cache=use_cache):
        out.extend(mechanisms_for_target(target_id, use_cache=use_cache))
    return out
