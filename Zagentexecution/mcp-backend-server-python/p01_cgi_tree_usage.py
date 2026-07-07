"""Which CGI tree is really used in P01 payments? Count real media in REGUT."""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard
from collections import defaultdict

g = ConnectionGuard("P01"); g.connect()
F = ["LAUFD","LAUFI","DTFOR","ZBUKR","XVORL","WAERS","RBETR","TSUSR"]
# DTFOR LIKE '/CGI%' is short enough for the 72-char OPTIONS limit
res = g.call("RFC_READ_TABLE", QUERY_TABLE="REGUT", DELIMITER="|",
    FIELDS=[{"FIELDNAME": f} for f in F],
    OPTIONS=[{"TEXT": "DTFOR LIKE '/CGI%'"}], ROWCOUNT=100000)
rows = [dict(zip(F,[v.strip() for v in r["WA"].split("|")])) for r in res.get("DATA",[])]
g.close()

agg = defaultdict(lambda: {"real":0,"prop":0,"yrs":defaultdict(int),"cocodes":set(),"last":""})
for r in rows:
    a = agg[r["DTFOR"]]
    if r["XVORL"].strip()=="": a["real"]+=1
    else: a["prop"]+=1
    a["yrs"][r["LAUFD"][:4]]+=1
    a["cocodes"].add(r["ZBUKR"])
    if r["LAUFD"]>a["last"]: a["last"]=r["LAUFD"]

print(f"P01 REGUT — CGI media: {len(rows)} total rows\n")
for fmt,a in sorted(agg.items()):
    print(f"=== {fmt} ===")
    print(f"  REAL media (XVORL=''): {a['real']}   proposals: {a['prop']}   last run: {a['last']}")
    print(f"  co-codes: {sorted(a['cocodes'])}")
    print(f"  by year: {dict(sorted(a['yrs'].items()))}\n")
