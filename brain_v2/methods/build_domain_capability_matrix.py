"""build_domain_capability_matrix.py — where our capability is, against where the work is.

The coverage-inversion finding (Treasury_EBS carries 15 assets for 98K executions while PS
carries zero documents for 1.6M) was computed once, by hand, in a script that no longer
exists. That makes it reflection. This makes it an artifact that regenerates and can
therefore be watched over time.

Per domain it crosses:
    activity   — executions from the domain map (what the system actually does)
    assets     — knowledge docs · companions · capability cells filled
    verdict    — the ratio between them

INVESTMENT_TIER encodes the product thesis: public-sector finance is the only ground where
being best is achievable, because no vendor ships process content for BCS / FM / PBC / GM /
PS-FM. Commercial modules are table stakes: be competent, do not over-invest.

Emits: domain_capability_matrix.json  ·  runs inside rebuild_all
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
sys.path.insert(0, str(BRAIN))
from canonical import canonical as C  # noqa: E402

EMAP = BRAIN / "executed_objects_domain_map.json"
REGISTRY = BRAIN / "domains" / "domains.json"
CAPMODEL = BRAIN / "capability_model" / "capability_model.json"
OUT = HERE / "domain_capability_matrix.json"

# The product thesis, made machine-readable so priorities are not a matter of memory.
INVESTMENT_TIER = {
    "DIFFERENTIATOR": {
        "domains": ["PSM_FM", "PBC", "PS", "GM", "Cost_Recovery_CRP"],
        "why": ("public-sector finance — BCS, Funds Management, Position Budgeting, Grants, "
                "PS-to-FM. No vendor ships process content for any of it. The only ground "
                "where being best is achievable and defensible."),
        "target": "EXCELLENT",
    },
    "TABLE_STAKES": {
        "domains": ["FI", "CO", "Procurement_P2P", "SD", "MM", "FI_AA", "PM"],
        "why": "commercial modules — solved, competed, commoditised. Be competent, not deep.",
        "target": "COMPETENT",
    },
    "OPERATIONAL": {
        "domains": ["Payment_BCM", "Treasury_EBS", "TRM", "HCM", "Travel", "RE_FX",
                    "BusinessPartner"],
        "why": "high consequence per event even at low volume; correctness matters more than depth",
        "target": "CORRECT",
    },
    "CROSS_CUTTING": {
        "domains": ["Integration", "HR_Workflows", "PY_Finance", "Output",
                    "Transport_Intelligence", "Security", "Support", "Closing_Activities"],
        "why": "spans modules; enriches rather than owns",
        "target": "MAPPED",
    },
}


def tier_of(dom):
    for tier, spec in INVESTMENT_TIER.items():
        if dom in spec["domains"]:
            return tier
    return "UNCLASSIFIED"


def main():
    emap = json.load(open(EMAP, encoding="utf-8")).get("by_domain", {}) if EMAP.exists() else {}
    raw = json.load(open(REGISTRY, encoding="utf-8"))
    reg = raw.get("domains", raw) if isinstance(raw, dict) else raw
    cap = json.load(open(CAPMODEL, encoding="utf-8")).get("domains", {})

    # registry keys are aliases; fold them onto canonical keys so a domain is not counted
    # twice (Payment and BCM both canonicalise to Payment_BCM)
    folded = {}
    for name, d in reg.items():
        ck = C(name)
        f = folded.setdefault(ck, {"docs": 0, "companions": 0, "registry_keys": []})
        f["docs"] += len(d.get("knowledge_docs") or [])
        f["companions"] += len(d.get("companions") or [])
        f["registry_keys"].append(name)

    rows = {}
    for ck in sorted(set(list(folded) + list(cap) + [C(k) for k in emap])):
        if ck in ("Uncatalogued", "Technical_Substrate", "Basis_Security", "ThirdParty_Addon",
                  "CTS_Transport"):
            continue
        f = folded.get(ck, {"docs": 0, "companions": 0, "registry_keys": []})
        cells = cap.get(ck, {})
        filled = sum(1 for k, v in cells.items() if not k.startswith("note") and v != "NONE")
        execs = emap.get(ck, {}).get("total_execs", 0)
        objs = emap.get(ck, {}).get("total_objects", 0)
        assets = f["docs"] + f["companions"] + filled
        rows[ck] = {
            "investment_tier": tier_of(ck),
            "execs": execs, "objects": objs,
            "docs": f["docs"], "companions": f["companions"],
            "capability_cells_filled": filled,
            "assets_total": assets,
            "execs_per_asset": round(execs / assets) if assets else None,
            "duplicate_registry_keys": f["registry_keys"] if len(f["registry_keys"]) > 1 else None,
        }

    # the inversion: high activity, low investment — and its mirror
    active = {k: v for k, v in rows.items() if v["execs"] > 0}
    under = sorted(active.items(), key=lambda x: -(x[1]["execs_per_asset"] or 0))[:5]
    over = sorted([(k, v) for k, v in active.items() if v["execs_per_asset"]],
                  key=lambda x: (x[1]["execs_per_asset"] or 0))[:5]

    # differentiator health — the thesis, measured
    diff = [k for k in rows if rows[k]["investment_tier"] == "DIFFERENTIATOR"]
    diff_execs = sum(rows[k]["execs"] for k in diff)
    diff_weak = [k for k in diff if rows[k]["capability_cells_filled"] < 6]

    out = {
        "_generated_by": "brain_v2/methods/build_domain_capability_matrix.py",
        "_what_this_answers": ("Is our capability where the work is? And is the "
                              "DIFFERENTIATOR tier actually our strongest, as the product "
                              "thesis requires?"),
        "investment_thesis": {k: {"why": v["why"], "target": v["target"]}
                              for k, v in INVESTMENT_TIER.items()},
        "differentiator_health": {
            "_meaning": ("Public-sector finance is the only defensible ground. If these "
                         "domains are not our best-modelled, the portfolio contradicts "
                         "the thesis."),
            "domains": diff, "total_execs": diff_execs,
            "under_modelled": diff_weak,
            "verdict": ("MISALLOCATED — differentiator domains below 6/11 capability cells"
                        if diff_weak else "aligned"),
        },
        "coverage_inversion": {
            "_meaning": "execs per asset. High = the work is there and we are not.",
            "most_under_invested": [{"domain": k, "execs": v["execs"],
                                     "assets": v["assets_total"],
                                     "execs_per_asset": v["execs_per_asset"]} for k, v in under],
            "most_covered": [{"domain": k, "execs": v["execs"], "assets": v["assets_total"],
                              "execs_per_asset": v["execs_per_asset"]} for k, v in over],
        },
        "redundancy": {
            "duplicate_registry_keys": {k: v["duplicate_registry_keys"]
                                        for k, v in rows.items()
                                        if v["duplicate_registry_keys"]},
        },
        "domains": rows,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"wrote {OUT}")
    print(f"  DIFFERENTIATOR tier: {len(diff)} domains, {diff_execs:,} execs — "
          f"{out['differentiator_health']['verdict']}")
    if diff_weak:
        print(f"    under-modelled: {', '.join(diff_weak)}")
    print("  most under-invested (execs per asset):")
    for k, v in under[:3]:
        print(f"    {k:20s} {v['execs']:>10,d} execs / {v['assets_total']:>2} assets "
              f"= {v['execs_per_asset']:,}")
    dup = out["redundancy"]["duplicate_registry_keys"]
    if dup:
        print(f"  REDUNDANT registry keys: {dup}")


if __name__ == "__main__":
    main()
