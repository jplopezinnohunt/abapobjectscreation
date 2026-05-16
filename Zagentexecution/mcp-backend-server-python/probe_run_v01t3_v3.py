"""V3: zoom in on V01T3 — DFPAYG, proposal runs, client check."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

# Force UTF-8 stdout for Windows
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# 1) Confirm client + system
print("=== Connection client ===")
try:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="T000",
               OPTIONS=[], FIELDS=[{"FIELDNAME":"MANDT"},{"FIELDNAME":"MTEXT"}],
               ROWCOUNT=20)
    rows = r.get("DATA", [])
    print(f"  T000 rows: {len(rows)}")
except Exception as e:
    print(f"  T000 ERROR: {e}")

# Better: who am I?
try:
    r = c.call("RFC_PING")
    # via RFC_SYSTEM_INFO
    info = c.call("RFC_SYSTEM_INFO")
    sys_info = info.get("RFCSI_EXPORT", {})
    print(f"  System: {sys_info.get('RFCSYSID')} | Client: {sys_info.get('RFCMANDT')} | "
          f"User: {sys_info.get('RFCUSER')} | Host: {sys_info.get('RFCHOST')}")
except Exception as e:
    print(f"  RFC_SYSTEM_INFO: {e}")

# 2) DFPAYG — that's where SAPFPAYM looks; if V01T3 exists here it's processable
print("\n=== DFPAYG D01 LAUFD=20260507 (all UNES, all formats) ===")
try:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="DFPAYG",
               OPTIONS=[{"TEXT": "LAUFD = '20260507' AND ZBUKR = 'UNES'"}],
               FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                       {"FIELDNAME":"XVORL"},{"FIELDNAME":"GRPNO"},
                       {"FIELDNAME":"FORMI"},{"FIELDNAME":"ZBUKR"},
                       {"FIELDNAME":"HBKID"},{"FIELDNAME":"RZAWE"},
                       {"FIELDNAME":"ANZ_ERZ"},{"FIELDNAME":"ANZ_ERL"}],
               ROWCOUNT=200, DELIMITER='|')
    rows = r.get("DATA", [])
    print(f"  count: {len(rows)}")
    for row in rows:
        parts = [p.strip() for p in row['WA'].split('|')]
        print(f"  {parts}")
except Exception as e:
    print(f"  DFPAYG ERROR: {str(e)[:300]}")

# 3) DFPAYG — LIKE V01% (any LAUFI starting with V01)
print("\n=== DFPAYG D01 ZBUKR='UNES' LAUFI LIKE 'V01%' (any date) ===")
try:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="DFPAYG",
               OPTIONS=[{"TEXT": "ZBUKR = 'UNES' AND LAUFI LIKE 'V01%'"}],
               FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                       {"FIELDNAME":"XVORL"},{"FIELDNAME":"GRPNO"},
                       {"FIELDNAME":"FORMI"}],
               ROWCOUNT=100, DELIMITER='|')
    rows = r.get("DATA", [])
    print(f"  count: {len(rows)}")
    for row in rows:
        parts = [p.strip() for p in row['WA'].split('|')]
        print(f"  {parts}")
except Exception as e:
    print(f"  DFPAYG LIKE ERROR: {str(e)[:300]}")

# 4) REGUV — the run-level header (created by F110 even if no payments yet)
print("\n=== REGUV D01 LAUFD=20260507 ZBUKR=UNES ===")
try:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUV",
               OPTIONS=[{"TEXT": "LAUFD = '20260507'"}],
               FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                       {"FIELDNAME":"STATUS"},{"FIELDNAME":"ANZER"},
                       {"FIELDNAME":"ANZGB"}],
               ROWCOUNT=50, DELIMITER='|')
    rows = r.get("DATA", [])
    print(f"  count: {len(rows)}")
    for row in rows:
        parts = [p.strip() for p in row['WA'].split('|')]
        if parts[1].upper().startswith('V01') or parts[1] in ('10001B','10002B','10003B'):
            print(f"  {parts}")
except Exception as e:
    print(f"  REGUV ERROR: {str(e)[:300]}")

# 5) Try LAUFI exact 'V01T3 ' (with trailing space, 6 chars) and 'V01T 3'
print("\n=== REGUH variants of V01T3 ===")
for variant in ("V01T3", "V01T3 ", " V01T3", "VO1T3", "V01T_3", "V01T03"):
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUH",
                   OPTIONS=[{"TEXT": f"ZBUKR = 'UNES' AND LAUFI = '{variant}'"}],
                   FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"}],
                   ROWCOUNT=5, DELIMITER='|')
        rows = r.get("DATA", [])
        print(f"  '{variant}' (len={len(variant)}): {len(rows)} rows")
        for row in rows[:3]:
            print(f"    {row['WA']}")
    except Exception as e:
        print(f"  '{variant}': ERROR {str(e)[:120]}")
