"""Detail inspection of D01 LAUFD=20260507 LAUFI=10003B ZBUKR=UNES."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")
WHERE = "LAUFD = '20260507' AND LAUFI = '10003B' AND ZBUKR = 'UNES'"

print("=== DFPAYG (payment groups for SAPFPAYM consumption) ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="DFPAYG",
           OPTIONS=[{"TEXT": WHERE}],
           FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                   {"FIELDNAME":"XVORL"},{"FIELDNAME":"GRPNO"},
                   {"FIELDNAME":"FORMI"},{"FIELDNAME":"HBKID"},
                   {"FIELDNAME":"HKTID"},{"FIELDNAME":"BANKS"},
                   {"FIELDNAME":"BANKL"},{"FIELDNAME":"RZAWE"},
                   {"FIELDNAME":"WAERS"},
                   {"FIELDNAME":"ANZ_ERZ"},{"FIELDNAME":"ANZ_ERL"}],
           DELIMITER='|')
for row in r.get("DATA", []):
    p = [x.strip() for x in row['WA'].split('|')]
    print(f"  {p}")

print("\n=== REGUH headers (1 row per payment) ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUH",
           OPTIONS=[{"TEXT": WHERE}],
           FIELDS=[{"FIELDNAME":"LIFNR"},{"FIELDNAME":"VBLNR"},
                   {"FIELDNAME":"WAERS"},{"FIELDNAME":"RBETR"},
                   {"FIELDNAME":"HBKID"},{"FIELDNAME":"HKTID"},
                   {"FIELDNAME":"RZAWE"},{"FIELDNAME":"UBNKS"},
                   {"FIELDNAME":"UBNKL"},{"FIELDNAME":"UBNKN"},
                   {"FIELDNAME":"ZBNKL"}],
           DELIMITER='|')
for row in r.get("DATA", []):
    p = [x.strip() for x in row['WA'].split('|')]
    print(f"  {p}")

print("\n=== REGUP items (line-level) ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUP",
           OPTIONS=[{"TEXT": "LAUFD = '20260507' AND LAUFI = '10003B'"}],
           FIELDS=[{"FIELDNAME":"LIFNR"},{"FIELDNAME":"VBLNR"},
                   {"FIELDNAME":"BELNR"},{"FIELDNAME":"BUZEI"},
                   {"FIELDNAME":"WAERS"},{"FIELDNAME":"DMBTR"},
                   {"FIELDNAME":"WRBTR"},{"FIELDNAME":"XBLNR"},
                   {"FIELDNAME":"SGTXT"}],
           ROWCOUNT=20, DELIMITER='|')
rows = r.get("DATA", [])
print(f"  total items shown: {len(rows)} (max 20)")
for row in rows:
    p = [x.strip() for x in row['WA'].split('|')]
    print(f"  {p}")

print("\n=== TFPM042F properties for /SEPA_CT_UNES ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="TFPM042F",
           OPTIONS=[{"TEXT": "FORMI = '/SEPA_CT_UNES'"}],
           FIELDS=[{"FIELDNAME":"FORMI"},{"FIELDNAME":"FORMT"},
                   {"FIELDNAME":"DTTYP"},{"FIELDNAME":"FORMTREE"},
                   {"FIELDNAME":"XDME1"}],
           DELIMITER='|')
for row in r.get("DATA", []):
    print(f"  {row['WA']}")
