"""
compare_spau_objects.py
======================
Object-level SPAU comparison ACROSS the 3 upgrades (not just 2024), to check
whether the "HR/Payroll is the fragility" conclusion holds for 2026/2023 too.
Same method as extract_spau_2024_detail.py, run per window. Read-only P01.
"""
import sys, os, json
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = os.path.join(os.path.dirname(__file__), "..",
                    "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
WINDOWS = {"2026-06": ("20260601", "20260615"),
           "2024-07": ("20240701", "20240715"),
           "2023-06": ("20230601", "20230620")}


def read_full(conn, table, fields, where=""):
    return rfc_read_paginated(conn, table, fields, where, batch_size=1_000_000, throttle=0)


def domain(pkg):
    p = (pkg or "").upper()
    if (p.startswith("P") or "HRPA" in p or "S4SIC" in p or p.startswith("XS4")
            or p.startswith("PAOC")):
        return "HR / Payroll"
    if "BANK" in p or p in ("BF", "CAJO", "FINS_FI_MIG") or "FI" in p[:3] or "PAYM" in p:
        return "FI / Banking / Payment"
    if p.startswith("/SDF") or "STPI" in p or p.startswith("ST"):
        return "Basis / tools"
    return "Other"


def main():
    import sqlite3
    db = sqlite3.connect(GOLD)
    smod = {(r[0], r[1]): r[2] for r in db.execute(
        "SELECT OBJ_NAME, TRKORR, OBJ_TYPE FROM smodilog WHERE TRIM(SPAU)<>'' AND TRIM(TRKORR)<>''")}
    # list of (TRKORR) per SPAU row
    spau_rows = [dict(zip(("OBJ_TYPE", "OBJ_NAME", "TRKORR"), (r[0], r[1], r[2])))
                 for r in db.execute(
        "SELECT OBJ_TYPE, OBJ_NAME, TRKORR FROM smodilog WHERE TRIM(SPAU)<>'' AND TRIM(TRKORR)<>''")]
    db.close()
    conn = get_connection("P01")
    out = {}
    for lab, (a, b) in WINDOWS.items():
        e = read_full(conn, "E070", ["TRKORR", "AS4DATE"],
                      [{"TEXT": f"AS4DATE >= '{a}'"}, {"TEXT": f"AND AS4DATE <= '{b}'"}])
        win_trk = set(r["TRKORR"] for r in e)
        objs = [r for r in spau_rows if r["TRKORR"] in win_trk]
        distinct = sorted(set((r["OBJ_TYPE"].strip(), r["OBJ_NAME"].strip())
                              for r in objs if r["OBJ_NAME"].strip()))
        names = sorted(set(n for _, n in distinct))
        dev = {}
        for n in names:
            try:
                rows = read_full(conn, "TADIR", ["OBJ_NAME", "DEVCLASS"],
                                 f"OBJ_NAME = '{n.replace(chr(39), chr(39)*2)}'")
                if rows:
                    dev[n] = rows[0]["DEVCLASS"].strip()
            except Exception:
                pass
        by_type = Counter(t for t, _ in distinct)
        by_dom = Counter(domain(dev.get(n, "")) for _, n in distinct)
        tot = len(distinct)
        out[lab] = {"records": len(objs), "distinct": tot,
                    "by_type": dict(by_type.most_common()),
                    "by_domain": dict(by_dom.most_common()),
                    "hr_pct": round(100 * by_dom.get("HR / Payroll", 0) / tot) if tot else 0}
        print(f"=== {lab}: {len(objs)} records / {tot} distinct objects ===")
        print("   by domain:", {k: f"{v} ({round(100*v/tot)}%)" for k, v in by_dom.most_common()})
        print("   by type  :", dict(by_type.most_common(6)))
    conn.close()
    with open(os.path.join(os.path.dirname(__file__), "spau_compare.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\n[SAVED] spau_compare.json")


if __name__ == "__main__":
    main()
