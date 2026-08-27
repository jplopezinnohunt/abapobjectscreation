"""canonical.py — ONE place that resolves a domain name to its canonical key.

THE most repeated defect in this codebase. In session 097 alone the same bug appeared
THREE times, in three different files, and was fixed three times separately:

  1. doc resolution   — 4 domain docs reported MISSING because folders are named by
                        alias (PSM_FM lives in PSM/, Payment_BCM in Payment/,
                        Treasury_EBS in Treasury/, Procurement_P2P in Procurement/).
                        Writing them would have duplicated existing knowledge.
  2. claim matching   — module names compared raw against claim domains.
  3. coherence check  — MM and Payment_BCM reported as UNSUPPORTED when both are
                        richly evidenced; the checker was comparing an alias to a
                        canonical key.

Fixing a recurring defect three times is not fixing it. `ontology.json` already holds
the alias declarations — the failure was never missing data, it was that every consumer
re-implemented the lookup. This module is the lookup. Import it; do not re-derive it.

    from canonical import canonical, aliases_of
    canonical("PSM")        -> "PSM_FM"
    canonical("Procurement")-> "Procurement_P2P"
    aliases_of("PSM_FM")    -> ["PSM_FM", "PSM"]
"""
import json
from functools import lru_cache
from pathlib import Path

ONTOLOGY = Path(__file__).parent / "capability_model" / "ontology.json"


@lru_cache(maxsize=1)
def _tables():
    """(alias_upper -> canonical, canonical -> [all spellings]) built once from the contract."""
    fwd, rev = {}, {}
    if not ONTOLOGY.exists():
        return fwd, rev
    onto = json.load(open(ONTOLOGY, encoding="utf-8"))
    for d in onto.get("domains", []):
        ck = d.get("canonical_key")
        if not ck:
            continue
        spellings = [ck] + list(d.get("aliases") or []) + list(d.get("registry_keys") or [])
        seen = []
        for s in spellings:
            s = str(s)
            fwd[s.upper()] = ck
            # hyphen/underscore are used interchangeably across stores (RE-FX vs RE_FX)
            fwd[s.upper().replace("_", "-")] = ck
            fwd[s.upper().replace("-", "_")] = ck
            if s not in seen:
                seen.append(s)
        rev[ck] = seen
    return fwd, rev


def canonical(name, default=None):
    """Any spelling of a domain -> its canonical key.

    Returns `default` (or the input unchanged when default is None) for names that are
    not declared. An UNDECLARED name is not an error here — validate_ontology.py is the
    gate for that. This function must never silently invent a mapping.
    """
    if not name:
        return default
    fwd, _ = _tables()
    hit = fwd.get(str(name).upper())
    if hit:
        return hit
    return default if default is not None else name


@lru_cache(maxsize=1)
def _subdominios():
    """nombre_upper -> canonical del PADRE, leido de `subdomain_aliases`. s106.

    Aparte de `_tables()` A PROPOSITO. Un subdominio NO es un alias: `Cost_Recovery_CRP`
    es dominio de primer nivel en domains.json y subdominio de PSM_FM en el capability
    model -- decision declarada en la propia ontologia ("Mapped as a SUBDOMAIN, not a 16th
    domain"). Colapsarlo por defecto cambiaria el resultado de los 6 modulos que ya
    importan este helper, asi que se ofrece OPT-IN.
    """
    out = {}
    if not ONTOLOGY.exists():
        return out
    try:
        onto = json.load(open(ONTOLOGY, encoding="utf-8"))
    except (OSError, ValueError):
        return out
    for k, v in (onto.get("subdomain_aliases") or {}).items():
        ck = (v or {}).get("canonical_key") if isinstance(v, dict) else None
        if ck:
            out[str(k).upper()] = ck
    return out


def canonical_or_parent(name, default=None):
    """Como `canonical()`, pero un SUBDOMINIO declarado resuelve a su dominio padre.

    Usalo cuando compares poblaciones entre stores que no coinciden en granularidad --
    p.ej. el eje de proceso, donde domains.json lista Cost_Recovery_CRP y el capability
    model lo tiene dentro de PSM_FM. Sin esto, la comparacion inventa una discrepancia
    que no existe (medido s106 en process_axis_consistency_check).
    """
    if not name:
        return default
    hit = _subdominios().get(str(name).upper())
    if hit:
        return hit
    return canonical(name, default)


def same_or_parent(a, b):
    """`same()` tolerante a granularidad: un subdominio y su padre son el mismo sujeto."""
    return bool(a) and bool(b) and canonical_or_parent(a) == canonical_or_parent(b)


def is_declared(name):
    """True when the name resolves to a declared canonical domain."""
    fwd, _ = _tables()
    return bool(name) and str(name).upper() in fwd


def aliases_of(canonical_key):
    """Every declared spelling of a canonical key — use for folder/path lookups."""
    _, rev = _tables()
    return rev.get(canonical_key, [canonical_key] if canonical_key else [])


def same(a, b):
    """Do two domain spellings refer to the same domain? Never compare names raw."""
    return bool(a) and bool(b) and canonical(a) == canonical(b)


if __name__ == "__main__":
    fwd, rev = _tables()
    print(f"{len(rev)} canonical domains, {len(fwd)} spellings")
    for probe in ["PSM", "Payment", "BCM", "Treasury", "Procurement", "RE-FX", "PBC", "co"]:
        print(f"  {probe:14s} -> {canonical(probe)}")
