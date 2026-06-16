"""
probe_spau_timing.py
====================
(A) Probe the SPAU/modification-adjustment source (SMODILOG + alternatives):
    structure + counts + sample, to measure custom-code impact per upgrade.
(B) Extract TPALOG (tp action log, per-step timestamps) for each upgrade window
    to reconstruct the REAL elapsed time of the import (PAT03.IMPLE_TIME is only
    the SPAM commit stamp, not the duration).

Read-only, P01 SNC/SSO. No ROWSKIPS (single-call reads).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

BIG = 1_000_000
SPAU_CANDIDATES = ["SMODILOG", "SMODISRC", "ADIRACCESS"]

# upgrade windows (TRTIME = NUMC14 YYYYMMDDHHMMSS)
WINDOWS = {
    "2026-06": ("20260601000000", "20260615000000"),
    "2024-07": ("20240701000000", "20240715000000"),
    "2023-06": ("20230601000000", "20230620000000"),
    "2017-03": ("20170320000000", "20170405000000"),
}


def fields_of(conn, table):
    rows = rfc_read_paginated(conn, "DD03L",
                              ["FIELDNAME", "POSITION", "ROLLNAME", "DATATYPE", "LENG"],
                              f"TABNAME = '{table}'", batch_size=BIG, throttle=0)
    rows = [r for r in rows if r["FIELDNAME"].strip() and not r["FIELDNAME"].startswith(".")]
    rows.sort(key=lambda r: int(r.get("POSITION", "0") or "0"))
    return rows


def main():
    conn = get_connection("P01")
    print("[OK] P01\n")
    report = {}

    # ---- (A) SPAU source probe ----
    for tbl in SPAU_CANDIDATES:
        print("=" * 72)
        print(f"SPAU CANDIDATE: {tbl}")
        print("=" * 72)
        fs = fields_of(conn, tbl)
        if not fs:
            print("  (does not exist)\n")
            continue
        fnames = [f["FIELDNAME"].strip() for f in fs]
        for f in fs:
            print(f"    {f['FIELDNAME']:<18} {f.get('ROLLNAME',''):<14} "
                  f"{f.get('DATATYPE',''):<6} {f.get('LENG','')}")
        sample = rfc_read_paginated(conn, tbl, fnames[:8], "", batch_size=50, throttle=0)
        print(f"\n  sample rows (first 8 fields): {len(sample)} read")
        for r in sample[:5]:
            print("    " + " | ".join(f"{k}={v}" for k, v in r.items() if v.strip()))
        report[tbl] = {"fields": fnames}
        print()

    conn.close()
    out = os.path.join(os.path.dirname(__file__), "probe_spau_timing.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False, default=str)
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    main()
