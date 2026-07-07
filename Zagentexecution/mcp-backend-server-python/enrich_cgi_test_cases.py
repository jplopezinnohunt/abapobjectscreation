"""Enrich the picked CGI test-case runs with concrete creditor + alt-payee detail."""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

g = ConnectionGuard("D01"); g.connect()

PICKS = [
    ("20250326", "T0001", "/CGI_XML_CT_UNESCO"),    # AE foreign creditor
    ("20250320", "00002R", "/CGI_XML_CT_UNESCO"),   # alt-payee
    ("20250320", "00001R", "/CGI_XML_CT_UNESCO"),   # alt-payee
    ("20250307", "00001R", "/CGI_XML_CT_UNESCO_1"), # twin + EUR + alt-payee
    ("20250307", "00006R", "/CGI_XML_CT_UNESCO_1"), # twin USD
]
F = ["LIFNR","EMPFG","ZNME1","ZSTRA","ZORT1","ZPSTL","ZLAND","UBNKS","ZSWIF","WAERS","RBETR","ZIBAN"]
for laufd, laufi, fmt in PICKS:
    res = g.call("RFC_READ_TABLE", QUERY_TABLE="REGUH", DELIMITER="|",
        FIELDS=[{"FIELDNAME": f} for f in F],
        OPTIONS=[{"TEXT": f"LAUFD = '{laufd}'"},{"TEXT": f" AND LAUFI = '{laufi}'"}], ROWCOUNT=50)
    print(f"\n=== {laufd}/{laufi}  {fmt} ===")
    for r in res.get("DATA", []):
        d = dict(zip(F, [v.strip() for v in r["WA"].split("|")]))
        alt = f"  ALT-PAYEE(EMPFG)={d['EMPFG']}" if d["EMPFG"] else ""
        print(f"  vendor={d['LIFNR']} {d['WAERS']} {d['RBETR']:>10}  name='{d['ZNME1']}'  "
              f"addr='{d['ZSTRA']}, {d['ZPSTL']} {d['ZORT1']} {d['ZLAND']}'  bankCtry={d['UBNKS']} BIC={d['ZSWIF']}{alt}")
g.close()
