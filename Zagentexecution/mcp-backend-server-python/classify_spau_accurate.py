"""
classify_spau_accurate.py
========================
Accurate classification of the SPAU-flagged objects per upgrade. The raw
SMODILOG SPAU set mixes THREE different things; separating them is the point:
  1. UNESCO functional modifications (the real recurring SPAU work) -> HR, FI, ...
  2. SAP-delivered objects: S/4 readiness-check (SIC, CLS4SIC_*) + note
     corrections (NOTE_*, *_CORR_*) -> NOT UNESCO's recurring work
  3. generated / technical artifacts (SMIM, WAPA, AVAS, DOCT)
Read-only P01.
"""
import sys, os, json
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated
import sqlite3

GOLD = os.path.join(os.path.dirname(__file__), "..",
                    "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
WINDOWS = {"2026-06": ("20260601", "20260615"),
           "2024-07": ("20240701", "20240715"),
           "2023-06": ("20230601", "20230620")}

HR_PKG = {"PBUN", "PCUN", "PUN_CMT", "PB06", "P06_DSN", "PC06", "PP00", "PBAS",
          "PBUN_EVE", "PAOC_PAD_INFTY_0009_XX", "PAOC_PAD_INFTY_0509_UN"}
FI_PKG = {"BF_BANK", "BF", "CAJO", "ID-FI-REU-PAYM", "FINS_FI_MIG", "FBAS",
          "FMBS_ADDON", "FMEU", "FMBS", "FMRESERV"}
BASIS_PKG = {"STTREL", "SECE", "/SDF/STPI_7X"}


def bucket(otype, name, pkg):
    n, p = name.upper(), (pkg or "").upper()
    if n.startswith("CLS4SIC") or p.startswith("XS4SIC"):
        return "S/4 readiness check (SIC)"
    if "NOTE_" in n or "_CORR_" in n or n.startswith("FIN_ML_CORR"):
        return "SAP note correction"
    if otype in ("SMIM", "WAPA", "AVAS", "DOCT", "DSYS"):
        return "generated / technical"
    if p in HR_PKG or p.startswith("PAOC") or "HRPA" in p or "HRPAY" in n:
        return "HR / Payroll (UNESCO mod)"
    if p in FI_PKG or p.startswith("FM") or "BANK" in p or "PAYM" in p:
        return "FI / Banking / Payment (UNESCO mod)"
    if p.startswith("/SDF") or p.startswith("ST") or p in BASIS_PKG:
        return "Basis / tools"
    return "Other functional (UNESCO mod)"


def main():
    db = sqlite3.connect(GOLD)
    spau = [dict(zip(("OT", "ON", "TK"), r)) for r in db.execute(
        "SELECT OBJ_TYPE,OBJ_NAME,TRKORR FROM smodilog WHERE TRIM(SPAU)<>'' AND TRIM(TRKORR)<>''")]
    db.close()
    conn = get_connection("P01")
    out = {}
    for lab, (a, b) in WINDOWS.items():
        e = rfc_read_paginated(conn, "E070", ["TRKORR", "AS4DATE"],
            [{"TEXT": f"AS4DATE >= '{a}'"}, {"TEXT": f"AND AS4DATE <= '{b}'"}],
            batch_size=1_000_000, throttle=0)
        wt = set(r["TRKORR"] for r in e)
        distinct = sorted(set((r["OT"].strip(), r["ON"].strip())
                              for r in spau if r["TK"] in wt and r["ON"].strip()))
        dev = {}
        for ot, n in distinct:
            if n not in dev:
                try:
                    r = rfc_read_paginated(conn, "TADIR", ["OBJ_NAME", "DEVCLASS"],
                        f"OBJ_NAME = '{n.replace(chr(39), chr(39)*2)}'", batch_size=5, throttle=0)
                    dev[n] = r[0]["DEVCLASS"].strip() if r else ""
                except Exception:
                    dev[n] = ""
        cat = Counter(bucket(ot, n, dev.get(n, "")) for ot, n in distinct)
        tot = len(distinct)
        unesco = sum(v for k, v in cat.items() if "UNESCO mod" in k)
        out[lab] = {"distinct": tot, "unesco_mods": unesco, "by_category": dict(cat.most_common())}
        print(f"=== {lab}: {tot} distinct objects ===")
        for k, v in cat.most_common():
            print(f"   {v:>3} ({round(100*v/tot):>2}%)  {k}")
        print(f"   --> genuine UNESCO modifications: {unesco} / {tot}\n")
    conn.close()
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "spau_accurate.json"), "w"), indent=2)
    print("[SAVED] spau_accurate.json")


if __name__ == "__main__":
    main()
