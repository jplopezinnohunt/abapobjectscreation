"""
gold_extractor_maturity.py — extractor maturity, measured PER DOMAIN × PER TABLE
--------------------------------------------------------------------------------
The meta-capability EXTRACT score used to measure only whether we know *how* to
extract (method registry). User direction (2026-06-22): "la madurez del extractor
depende de cada dominio y cada tabla clasificada." This applies the model's
category→subcategory fractal to the extractor itself: every golden table climbs a
maturity LADDER, and a domain's extractor maturity = the mean of its tables.

Ladder (subcategories of extractor maturity, per table):
  L0 unclassified   0.00  domain=Uncatalogued OR table_type=unknown
  L1 classified     0.25  assigned to a real domain + a known table_type (auto)
  L2 contracted     0.50  curated spec: key + refresh strategy declared
  L3 delta_capable  0.75  delta is parameterized (pk key / totals value_fields / txn hwm)
  L4 synced_verified 1.00 actually refreshed with a delta (row in _gold_sync_log)

Inputs : brain_v2/gold_table_registry.json + golden DB `_gold_sync_log`.
Emits  : brain_v2/gold_extractor_maturity.json  (overall + per-domain + per-type).
Run    : python brain_v2/gold_extractor_maturity.py
"""
import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REGISTRY = HERE / "gold_table_registry.json"
GOLD = ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = HERE / "gold_extractor_maturity.json"

LADDER = {0: "L0_unclassified", 1: "L1_classified", 2: "L2_contracted",
          3: "L3_delta_capable", 4: "L4_synced_verified"}


def delta_parameterized(spec):
    strat = spec.get("delta")
    if strat == "pk-upsert":
        return bool(spec.get("key"))
    if strat == "value-compare":
        return bool(spec.get("value_fields"))
    if strat == "hwm-append":
        return bool(spec.get("hwm"))
    return False


def table_level(spec, ttype, dom, synced):
    if spec.get("source") == "curated":
        if spec["gold"] in synced and delta_parameterized(spec):
            return 4
        if delta_parameterized(spec):
            return 3
        return 2  # contracted but delta not yet parameterized (e.g. totals w/o value_fields)
    # auto
    if dom != "Uncatalogued" and ttype != "unknown":
        return 1
    return 0


def main():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    synced = set()
    try:
        con = sqlite3.connect(GOLD)
        synced = {r[0] for r in con.execute("SELECT DISTINCT gold FROM _gold_sync_log").fetchall()}
        con.close()
    except sqlite3.Error:
        pass

    per_domain = {}
    per_type = {}
    all_levels = []
    tables = []
    for dom, types in reg["domains"].items():
        for ttype, specs in types.items():
            for spec in specs:
                lvl = table_level(spec, ttype, dom, synced)
                all_levels.append(lvl)
                per_domain.setdefault(dom, []).append(lvl)
                per_type.setdefault(ttype, []).append(lvl)
                tables.append({"domain": dom, "type": ttype, "gold": spec["gold"],
                               "level": lvl, "ladder": LADDER[lvl], "source": spec.get("source")})

    def score(levels):
        return round(sum(levels) / (4 * len(levels)), 3) if levels else 0.0

    out = {
        "_design": "Extractor maturity per domain × per table. score = mean(level)/4. "
                   "Ladder L0..L4 (unclassified→synced_verified). Fractal of the capability model.",
        "overall_pct": round(100 * score(all_levels), 1),
        "n_tables": len(all_levels),
        "by_domain": {d: {"score": score(v), "n": len(v),
                          "dist": {LADDER[i]: sum(1 for x in v if x == i) for i in range(5) if any(x == i for x in v)}}
                      for d, v in sorted(per_domain.items(), key=lambda kv: -score(kv[1]))},
        "by_type": {t: {"score": score(v), "n": len(v)} for t, v in sorted(per_type.items(), key=lambda kv: -score(kv[1]))},
        "tables": sorted(tables, key=lambda t: (-t["level"], t["domain"], t["gold"])),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"=== EXTRACTOR MATURITY (per domain × per table) = {out['overall_pct']}%  "
          f"({len(all_levels)} tables) ===\n")
    print("  by table_type:")
    for t, v in out["by_type"].items():
        bar = "#" * int(v["score"] * 10)
        print(f"    {t:14s} {v['score']:.2f} {bar:<10}  ({v['n']})")
    print("\n  by domain:")
    for d, v in out["by_domain"].items():
        bar = "#" * int(v["score"] * 10)
        dist = " ".join(f"{k.split('_')[0]}:{n}" for k, n in v["dist"].items())
        print(f"    {d:14s} {v['score']:.2f} {bar:<10}  ({v['n']:>3})  {dist}")
    print(f"\n  emitted: {OUT}")


if __name__ == "__main__":
    main()
