"""
maturity_score.py — deterministic maturity of the exploration model (Layer 15).
=================================================================================
Scores the capability matrix into a maturity %, two levels:
  LEVEL 1 — MODEL maturity by CAPABILITY/theme (avg of a dimension across domains)
  LEVEL 2 — maturity by DOMAIN (avg of a domain's cells)
plus method readiness (can we even do it?) and the no-extraction-vs-extraction split.

Scoring (traceable, CP-001/003): NONE=0.0, PARTIAL=0.5, HAVE=1.0. No opinion — pure
function of the matrix. Run after editing capability_model.json.

Usage: python brain_v2/capability_model/maturity_score.py   (prints + writes maturity.json)
"""
import json, os
from pathlib import Path

HERE = Path(__file__).parent
MODEL = HERE / "capability_model.json"
OUT = HERE / "maturity.json"

CELL = {"NONE": 0.0, "PARTIAL": 0.5, "HAVE": 1.0}
# plan mapping: which dimensions are advanceable WITHOUT new SAP extraction (Bucket A)
# vs which require new extraction (Bucket B). From capability_model_execution_plan.md.
NO_EXTRACTION_DIMS = {"S_STANDARD_REF", "A_PROCESS", "B_CODE", "G_CONFORMANCE"}  # A4/A3/A6-7/A5
EXTRACTION_DIMS = {"E_AUTH", "F_INTERFACE_FILE", "R_S4_READINESS", "U_USAGE"}     # B1/B3-5 + ATC/usage + exec census
MIXED_DIMS = {"C_CONFIG", "D_DATA", "H_IMPROVE"}                                  # partly both


def pct(x):
    return round(100 * x, 1)


def run(write=True):
    model = json.load(open(MODEL, encoding="utf-8"))
    dims = list(model["dimensions"].keys())
    doms = model["domains"]
    method_tier = {d: model["dimensions"][d].get("method_tier", "?") for d in dims}

    # LEVEL 2 — per domain
    by_domain = {}
    for name, cov in doms.items():
        vals = [CELL.get(cov.get(d, "NONE"), 0.0) for d in dims]
        by_domain[name] = {
            "maturity_pct": pct(sum(vals) / len(dims)),
            "cells": {d: cov.get(d, "NONE") for d in dims},
        }

    # LEVEL 1 — per capability/theme (column average across domains)
    by_capability = {}
    for d in dims:
        vals = [CELL.get(doms[n].get(d, "NONE"), 0.0) for n in doms]
        by_capability[d] = {
            "maturity_pct": pct(sum(vals) / len(vals)) if vals else 0.0,
            "method_tier": method_tier[d],
            "method_available": method_tier[d] in ("VERIFIED", "OWN"),
            "have": sum(1 for n in doms if doms[n].get(d) == "HAVE"),
            "partial": sum(1 for n in doms if doms[n].get(d) == "PARTIAL"),
            "none": sum(1 for n in doms if doms[n].get(d) == "NONE"),
            "advance_path": ("NO_EXTRACTION" if d in NO_EXTRACTION_DIMS
                             else "EXTRACTION" if d in EXTRACTION_DIMS else "MIXED"),
        }

    # MODEL maturity — overall avg of every cell
    all_vals = [CELL.get(doms[n].get(d, "NONE"), 0.0) for n in doms for d in dims]
    model_maturity = pct(sum(all_vals) / len(all_vals)) if all_vals else 0.0

    # how much of the remaining gap is reachable with NO extraction?
    gap_no_ext = sum(1 - CELL.get(doms[n].get(d, "NONE"), 0.0)
                     for n in doms for d in dims if d in NO_EXTRACTION_DIMS)
    gap_ext = sum(1 - CELL.get(doms[n].get(d, "NONE"), 0.0)
                  for n in doms for d in dims if d in EXTRACTION_DIMS)
    gap_mixed = sum(1 - CELL.get(doms[n].get(d, "NONE"), 0.0)
                    for n in doms for d in dims if d in MIXED_DIMS)
    total_gap = gap_no_ext + gap_ext + gap_mixed

    result = {
        "_design": "Maturity of the exploration model (Layer 15). NONE=0/PARTIAL=0.5/HAVE=1.0. Deterministic.",
        "model_maturity_pct": model_maturity,
        "n_domains": len(doms),
        "n_capabilities": len(dims),
        "gap_split": {
            "no_extraction_units": round(gap_no_ext, 1),
            "extraction_units": round(gap_ext, 1),
            "mixed_units": round(gap_mixed, 1),
            "total_gap_units": round(total_gap, 1),
            "pct_gap_reachable_without_extraction": pct((gap_no_ext + 0.5 * gap_mixed) / total_gap) if total_gap else 0.0,
        },
        "level1_by_capability": dict(sorted(by_capability.items(), key=lambda kv: kv[1]["maturity_pct"], reverse=True)),
        "level2_by_domain": dict(sorted(by_domain.items(), key=lambda kv: kv[1]["maturity_pct"], reverse=True)),
    }
    if write:
        json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    r = run()
    print(f"=== EXPLORATION MODEL MATURITY: {r['model_maturity_pct']}% ===")
    print(f"({r['n_domains']} domains x {r['n_capabilities']} capabilities)")
    print(f"Gap reachable WITHOUT extraction: {r['gap_split']['pct_gap_reachable_without_extraction']}%\n")
    print("LEVEL 1 — by CAPABILITY (theme):")
    for d, v in r["level1_by_capability"].items():
        flag = "" if v["method_available"] else "  [NO METHOD YET]"
        print(f"  {v['maturity_pct']:5.1f}%  {d:18} ({v['method_tier']}, {v['advance_path']}){flag}")
    print("\nLEVEL 2 — by DOMAIN:")
    for n, v in r["level2_by_domain"].items():
        print(f"  {v['maturity_pct']:5.1f}%  {n}")
    print(f"\nsaved: {OUT}")
