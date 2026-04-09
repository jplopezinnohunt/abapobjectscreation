"""Check transport D01K9B0F5F status in both systems."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

TR = "D01K9B0F5F"

for system in ["D01", "P01"]:
    print(f"\n{'='*60}")
    print(f"  {system}")
    print(f"{'='*60}")
    try:
        conn = get_connection(system)
    except Exception as e:
        print(f"  ERROR: {e}")
        continue

    # E070 header
    e070 = rfc_read_paginated(conn, "E070",
        ["TRKORR", "TRFUNCTION", "TRSTATUS", "TARSYSTEM", "AS4USER", "AS4DATE"],
        f"TRKORR = '{TR}'", batch_size=10, throttle=0.3)
    if e070:
        h = e070[0]
        status = h.get("TRSTATUS","").strip()
        status_map = {"D": "Modifiable", "L": "Modifiable (protected)",
                      "O": "Release started", "R": "Released",
                      "N": "Released (import started)"}
        print(f"  Status: {status} ({status_map.get(status, 'unknown')})")
        print(f"  Target: {h.get('TARSYSTEM','').strip()}")
        print(f"  Owner: {h.get('AS4USER','').strip()}")
        print(f"  Date: {h.get('AS4DATE','').strip()}")
    else:
        print(f"  Transport {TR} not found in E070")

    # TSTRFCOFIL — import log (P01 only matters)
    if system == "P01":
        # Check TMSBUFFER for import queue
        tmsbuf = rfc_read_paginated(conn, "TMSBUFFER",
            ["TRKORR", "IMPDATE", "IMPTIME", "IMPUSER"],
            f"TRKORR = '{TR}'", batch_size=10, throttle=0.3)
        if tmsbuf:
            for r in tmsbuf:
                print(f"  Import: {r.get('IMPUSER','').strip()} "
                      f"{r.get('IMPDATE','').strip()} {r.get('IMPTIME','').strip()}")
        else:
            print(f"  Not found in TMSBUFFER (not yet imported)")

        # Check E07T for description
        e07t = rfc_read_paginated(conn, "E07T",
            ["TRKORR", "AS4TEXT"],
            f"TRKORR = '{TR}'", batch_size=10, throttle=0.3)
        if e07t:
            print(f"  Description: {e07t[0].get('AS4TEXT','').strip()}")
        else:
            print(f"  No E07T entry in P01 (transport not arrived)")

    conn.close()
