"""Probe SETHEADER audit fields — narrow field list to avoid split."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

for system in ["D01", "P01"]:
    print(f"\n{'='*60}")
    print(f"  {system} — SETHEADER audit for YBANK sets")
    print(f"{'='*60}")
    try:
        conn = get_connection(system)
    except Exception as e:
        print(f"  ERROR: {e}")
        continue

    # Two narrow queries to avoid split
    rows1 = rfc_read_paginated(conn, "SETHEADER",
        ["SETNAME", "CREUSER", "CREDATE"],
        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'",
        batch_size=100, throttle=0.3)

    rows2 = rfc_read_paginated(conn, "SETHEADER",
        ["SETNAME", "UPDUSER", "UPDDATE", "UPDTIME"],
        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'",
        batch_size=100, throttle=0.3)

    # Merge by SETNAME
    upd_map = {r["SETNAME"].strip(): r for r in rows2}

    print(f"\n  {'Set Name':<35s} {'Created By':<15s} {'Updated By':<15s} {'Upd Date':<12s} {'Upd Time'}")
    print(f"  {'-'*35} {'-'*15} {'-'*15} {'-'*12} {'-'*8}")
    for r in sorted(rows1, key=lambda x: x.get("SETNAME","")):
        sn = r.get("SETNAME","").strip()
        creuser = r.get("CREUSER","").strip()
        u = upd_map.get(sn, {})
        upduser = u.get("UPDUSER","").strip()
        upddate = u.get("UPDDATE","").strip()
        updtime = u.get("UPDTIME","").strip()
        print(f"  {sn:<35s} {creuser:<15s} {upduser:<15s} {upddate:<12s} {updtime}")

    conn.close()
