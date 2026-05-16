"""V2 probe: try V01 system + LIKE search + recent UNES runs in May 2026."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, _build_connection_params

# Check what systems are configured in .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
configured = []
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith("SAP_") and "_ASHOST" in line:
                sysid = line.split("_")[1]
                configured.append(sysid)
print(f"Systems with credentials in .env: {configured}")

LAUFD = "20260507"
LAUFI_TARGET = "V01T3"

for system in configured + ["V01", "TS3", "TS1"]:
    if system in ("ASHOST",): continue
    print(f"\n{'='*70}\n=== {system} ===\n{'='*70}")
    try:
        c = get_connection(system)
    except Exception as e:
        print(f"  CONN FAIL: {str(e)[:200]}")
        continue

    # Search REGUH for any LAUFI starting with 'V' in early May 2026 UNES
    print(f"\n--- REGUH UNES runs 01-10 May 2026 ---")
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUH",
                   OPTIONS=[{"TEXT": f"ZBUKR = 'UNES' AND LAUFD >= '20260501' AND LAUFD <= '20260510'"}],
                   FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                           {"FIELDNAME":"ZBUKR"},{"FIELDNAME":"VBLNR"},
                           {"FIELDNAME":"RZAWE"}],
                   ROWCOUNT=200, DELIMITER='|')
        rows = r.get("DATA", [])
        # Aggregate by (LAUFD, LAUFI)
        agg = {}
        for row in rows:
            parts = row['WA'].split('|')
            laufd = parts[0].strip() if len(parts) > 0 else ''
            laufi = parts[1].strip() if len(parts) > 1 else ''
            rzawe = parts[4].strip() if len(parts) > 4 else ''
            k = (laufd, laufi)
            agg[k] = agg.get(k, [0, set()])
            agg[k][0] += 1
            agg[k][1].add(rzawe)
        for (laufd, laufi), (cnt, rzawes) in sorted(agg.items()):
            mark = " ★" if laufi.upper().startswith("V01T") or laufi.upper().startswith("V1T") else ""
            print(f"  {laufd} {laufi:8} payments={cnt} rzawe={sorted(rzawes)}{mark}")
    except Exception as e:
        print(f"  REGUH UNES recent ERROR: {str(e)[:200]}")

    # Targeted: REGUH with LAUFI like V01T% (any date)
    print(f"\n--- REGUH where LAUFI LIKE 'V01T%' (any date, UNES) ---")
    try:
        # SAP RFC_READ_TABLE supports LIKE via OPTIONS
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUH",
                   OPTIONS=[{"TEXT": f"ZBUKR = 'UNES' AND LAUFI LIKE 'V01T%'"}],
                   FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                           {"FIELDNAME":"ZBUKR"},{"FIELDNAME":"VBLNR"}],
                   ROWCOUNT=50, DELIMITER='|')
        rows = r.get("DATA", [])
        if not rows:
            print("  no match")
        else:
            seen = set()
            for row in rows:
                parts = row['WA'].split('|')
                k = (parts[0].strip(), parts[1].strip())
                if k not in seen:
                    seen.add(k)
                    print(f"  {parts[0].strip()} {parts[1].strip()}")
    except Exception as e:
        print(f"  REGUH LIKE ERROR: {str(e)[:200]}")
