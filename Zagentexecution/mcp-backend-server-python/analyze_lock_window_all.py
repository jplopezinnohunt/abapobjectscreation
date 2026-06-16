"""
analyze_lock_window_all.py
=========================
Infer the END-TO-END maintenance window (user lock -> release) for the last 3
upgrades, from the largest gap in real-user CDHDR change documents (when users
are locked, no change docs are written). Read-only P01. See the 2026 single
script for the method/caveats.
"""
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

SYS = ("DDIC", "SAP*", "TMSADM", "WF-BATCH", "JOBBATCH", "BATCH")
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# wide windows around each import day
WINDOWS = {
    "2026-06 (import Sun 07)": ("20260605", "20260609"),
    "2024-07 (import Fri 05)": ("20240702", "20240710"),
    "2023-06 (import Sat 10)": ("20230607", "20230614"),
}


def real(u):
    u = (u or "").strip()
    return u and u not in SYS and not u.startswith("SAP")


def main():
    conn = get_connection("P01")
    for label, (a, b) in WINDOWS.items():
        rows = rfc_read_paginated(conn, "CDHDR",
            ["UDATE", "UTIME", "USERNAME"],
            [{"TEXT": f"UDATE >= '{a}'"}, {"TEXT": f"AND UDATE <= '{b}'"},
             {"TEXT": "AND OBJECTCLAS <> 'IDENTITY'"}], batch_size=1_000_000, throttle=0)
        rows = [r for r in rows if real(r["USERNAME"])]
        rows.sort(key=lambda r: r["UDATE"] + r["UTIME"])
        biggest = (0, "", "")
        for i in range(1, len(rows)):
            t0 = rows[i-1]["UDATE"] + rows[i-1]["UTIME"]
            t1 = rows[i]["UDATE"] + rows[i]["UTIME"]
            h = (datetime.strptime(t1, "%Y%m%d%H%M%S") -
                 datetime.strptime(t0, "%Y%m%d%H%M%S")).total_seconds() / 3600
            if h > biggest[0]:
                biggest = (h, t0, t1)
        h, t0, t1 = biggest
        d0, d1 = datetime.strptime(t0[:8], "%Y%m%d"), datetime.strptime(t1[:8], "%Y%m%d")
        print(f"{label}: {len(rows)} real-user changes")
        print(f"   LOCKED  {DOW[d0.weekday()]} {t0[:8]} {t0[8:10]}:{t0[10:12]}  "
              f"-> RELEASED {DOW[d1.weekday()]} {t1[:8]} {t1[8:10]}:{t1[10:12]}"
              f"   = {h:.1f}h end-to-end\n")
    conn.close()


if __name__ == "__main__":
    main()
