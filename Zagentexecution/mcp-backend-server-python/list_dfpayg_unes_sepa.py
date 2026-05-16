"""List all DFPAYG entries D01 UNES /SEPA_CT_UNES — runs reprocessable by SAPFPAYM.
RULE (s072 user directive): always search DFPAYG, not REGUH, for SAPFPAYM-eligible runs."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

print("=== DFPAYG D01 ZBUKR=UNES (all formats, last 30 days) ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="DFPAYG",
           OPTIONS=[{"TEXT": "ZBUKR = 'UNES' AND LAUFD >= '20260415'"}],
           FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},
                   {"FIELDNAME":"XVORL"},{"FIELDNAME":"GRPNO"},
                   {"FIELDNAME":"FORMI"},{"FIELDNAME":"HBKID"},
                   {"FIELDNAME":"RZAWE"},
                   {"FIELDNAME":"ANZ_ERZ"},{"FIELDNAME":"ANZ_ERL"}],
           ROWCOUNT=200, DELIMITER='|')
rows = r.get("DATA", [])
print(f"  total rows: {len(rows)}\n")
print(f"  {'LAUFD':<10} {'LAUFI':<8} {'GRP':<5} {'FORMAT':<22} {'HBKID':<7} {'RZAWE':<6} {'ANZ_ERZ':<8} {'ANZ_ERL':<8} {'STATUS'}")
print(f"  {'-'*10} {'-'*8} {'-'*5} {'-'*22} {'-'*7} {'-'*6} {'-'*8} {'-'*8} {'-'*30}")
for row in rows:
    p = [x.strip() for x in row['WA'].split('|')]
    laufd, laufi, xvorl, grpno, formi, hbkid, rzawe, anz_erz, anz_erl = p[:9]
    erz = int(anz_erz) if anz_erz.isdigit() else 0
    erl = int(anz_erl) if anz_erl.isdigit() else 0
    status = "blocked-already-executed" if erl >= erz and erz > 0 else \
             "ready-to-execute" if erz > 0 and erl < erz else "no-files-expected"
    print(f"  {laufd:<10} {laufi:<8} {grpno:<5} {formi:<22} {hbkid:<7} {rzawe:<6} {anz_erz:<8} {anz_erl:<8} {status}")

print("\n=== Filter: only /SEPA_CT_UNES ===")
sepa_rows = [r['WA'].split('|') for r in rows]
sepa_rows = [[x.strip() for x in p] for p in sepa_rows]
sepa_rows = [p for p in sepa_rows if len(p) >= 5 and p[4].strip() == '/SEPA_CT_UNES']
print(f"  {len(sepa_rows)} rows on /SEPA_CT_UNES")
for p in sepa_rows:
    print(f"  {p[0]} {p[1]:<8} GRP={p[3]:<3} HBKID={p[5]:<5} ANZ_ERZ={p[7]} ANZ_ERL={p[8]}")
