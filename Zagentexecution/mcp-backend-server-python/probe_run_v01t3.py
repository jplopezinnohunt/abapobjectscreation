"""Probe payment run LAUFD=20260507 LAUFI='V01T3' in D01 and P01."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

LAUFD = "20260507"
LAUFI = "V01T3"

for system in ("D01", "P01"):
    print(f"\n{'='*70}\n=== {system} ===\n{'='*70}")
    try:
        c = get_connection(system)
    except Exception as e:
        print(f"  CONN FAIL: {e}")
        continue

    # 1) REGUV — run header (status + counters)
    print(f"\n--- REGUV (run status) ---")
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUV",
                   OPTIONS=[{"TEXT": f"LAUFD = '{LAUFD}' AND LAUFI = '{LAUFI}'"}],
                   FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                           {"FIELDNAME":"STATUS"},{"FIELDNAME":"X_DD_PRENOTIF"},
                           {"FIELDNAME":"ANZER"},{"FIELDNAME":"ANZGB"},
                           {"FIELDNAME":"ZALDT"},{"FIELDNAME":"NEDAT"}])
        rows = r.get("DATA", [])
        if not rows:
            print("  NO ROW (run does not exist in this system)")
        for row in rows:
            print(f"  {row['WA']}")
    except Exception as e:
        print(f"  REGUV ERROR: {e}")

    # 2) DFPAYG — payment groups (key SAPFPAYM input)
    print(f"\n--- DFPAYG (payment groups) ---")
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="DFPAYG",
                   OPTIONS=[{"TEXT": f"LAUFD = '{LAUFD}' AND LAUFI = '{LAUFI}'"}],
                   FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                           {"FIELDNAME":"GRPNO"},{"FIELDNAME":"FORMI"},
                           {"FIELDNAME":"ZBUKR"},{"FIELDNAME":"HBKID"},
                           {"FIELDNAME":"RZAWE"},
                           {"FIELDNAME":"ANZ_ERZ"},{"FIELDNAME":"ANZ_ERL"}])
        rows = r.get("DATA", [])
        if not rows:
            print("  NO ROW (no payment groups for this run)")
        for row in rows:
            print(f"  {row['WA']}")
    except Exception as e:
        print(f"  DFPAYG ERROR: {e}")

    # 3) REGUH — count payments + sample
    print(f"\n--- REGUH (payment headers, sample) ---")
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUH",
                   OPTIONS=[{"TEXT": f"LAUFD = '{LAUFD}' AND LAUFI = '{LAUFI}'"}],
                   FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                           {"FIELDNAME":"ZBUKR"},{"FIELDNAME":"LIFNR"},
                           {"FIELDNAME":"VBLNR"},{"FIELDNAME":"RZAWE"},
                           {"FIELDNAME":"WAERS"},{"FIELDNAME":"RBETR"}],
                   ROWCOUNT=10)
        rows = r.get("DATA", [])
        print(f"  count(sample, max 10): {len(rows)}")
        for row in rows[:5]:
            print(f"  {row['WA']}")
        # also do a full count via same WHERE — RFC_READ_TABLE doesn't have COUNT,
        # so just say sample. Real count comes if user wants.
    except Exception as e:
        print(f"  REGUH ERROR: {e}")

    # 4) Check format active in DFPAYG → look up TFPM042F.XDME1, FORMT
    print(f"\n--- TFPM042F (format properties for the format used) ---")
    try:
        # Get the format from DFPAYG first
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="DFPAYG",
                   OPTIONS=[{"TEXT": f"LAUFD = '{LAUFD}' AND LAUFI = '{LAUFI}'"}],
                   FIELDS=[{"FIELDNAME":"FORMI"}],
                   ROWCOUNT=10)
        formats = set()
        for row in r.get("DATA", []):
            wa = row['WA'].strip()
            if wa:
                formats.add(wa)
        for fmt in formats:
            r2 = c.call("RFC_READ_TABLE", QUERY_TABLE="TFPM042F",
                        OPTIONS=[{"TEXT": f"FORMI = '{fmt}'"}],
                        FIELDS=[{"FIELDNAME":"FORMI"},{"FIELDNAME":"FORMT"},
                                {"FIELDNAME":"DTTYP"},{"FIELDNAME":"FORMTREE"},
                                {"FIELDNAME":"XDME1"},{"FIELDNAME":"XLST1"}],
                        ROWCOUNT=5)
            for row in r2.get("DATA", []):
                print(f"  format {fmt}: {row['WA']}")
    except Exception as e:
        print(f"  TFPM042F ERROR: {e}")
