"""Check XINTB on all 4 UBA01 G/L accounts + ECO09 reference in both systems."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

GLS = ["0001065421","0001165421","0001065424","0001165424",
       "0001094421","0001194421","0001094424","0001194424"]

for system in ["D01","P01"]:
    print(f"\n{'='*60}")
    print(f"  {system} — XINTB check")
    print(f"{'='*60}")
    try:
        conn = get_connection(system)
    except Exception as e:
        print(f"  ERROR: {e}")
        continue

    for gl in GLS:
        rows = rfc_read_paginated(conn, "SKB1",
            ["BUKRS","SAKNR","XINTB","HBKID","HKTID"],
            f"BUKRS = 'UNES' AND SAKNR = '{gl}'",
            batch_size=10, throttle=0.3)
        if rows:
            r = rows[0]
            xintb = r.get("XINTB","").strip()
            hbkid = r.get("HBKID","").strip()
            flag = " ** BLOCKED" if xintb == "X" else ""
            print(f"  {gl} HBKID={hbkid:6s} XINTB={xintb or '(empty)':8s}{flag}")
        else:
            print(f"  {gl} NOT FOUND")

    conn.close()
