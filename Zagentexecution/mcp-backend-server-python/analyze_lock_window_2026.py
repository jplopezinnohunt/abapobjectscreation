"""
analyze_lock_window_2026.py
==========================
Infer the 2026 upgrade END-TO-END maintenance window (user lock -> release).
The explicit EWZ5/login-restriction lock is NOT in RFC-readable logs (0 UFLAG
change docs; RSAU audit log empty though rsau/enable=1), so the window is
inferred from the GAP in real-user business change documents (CDHDR): when
users are locked out, no change docs are created. Read-only P01.
"""
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

SYS = ("DDIC", "SAP*", "TMSADM", "WF-BATCH", "JOBBATCH", "BATCH")


def real(u):
    u = (u or "").strip()
    return u and u not in SYS and not u.startswith("SAP")


def main():
    conn = get_connection("P01")
    rows = rfc_read_paginated(conn, "CDHDR",
        ["OBJECTCLAS", "UDATE", "UTIME", "USERNAME", "TCODE"],
        [{"TEXT": "UDATE >= '20260605'"}, {"TEXT": "AND UDATE <= '20260609'"},
         {"TEXT": "AND OBJECTCLAS <> 'IDENTITY'"}], batch_size=1_000_000, throttle=0)
    conn.close()
    rows = [r for r in rows if real(r["USERNAME"])]
    rows.sort(key=lambda r: r["UDATE"] + r["UTIME"])
    print(f"real-user business change docs 06-05..06-09: {len(rows)}")

    biggest = None
    for i in range(1, len(rows)):
        a = rows[i-1]["UDATE"] + rows[i-1]["UTIME"]
        b = rows[i]["UDATE"] + rows[i]["UTIME"]
        h = (datetime.strptime(b, "%Y%m%d%H%M%S") -
             datetime.strptime(a, "%Y%m%d%H%M%S")).total_seconds() / 3600
        if h > 2:
            print(f"  GAP {h:>5.1f}h : {a[:8]} {a[8:12]} ({rows[i-1]['USERNAME']}) "
                  f"-> {b[:8]} {b[8:12]} ({rows[i]['USERNAME']})")
        if not biggest or h > biggest[0]:
            biggest = (h, a, b)
    h, a, b = biggest
    print(f"\nINFERRED MAINTENANCE WINDOW (largest gap = users locked out):")
    print(f"  locked  (last activity) : {a[:8]} {a[8:10]}:{a[10:12]}")
    print(f"  released (first activity): {b[:8]} {b[8:10]}:{b[10:12]}")
    print(f"  duration: {h:.1f} h  (vs 5.7 h disruptive import)")


if __name__ == "__main__":
    main()
