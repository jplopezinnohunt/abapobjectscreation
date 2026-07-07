"""Read real bank-master (BNKA) values for SOGEUS33 — source of CdtrAgt ZB* fields. Core-tool test + fallback."""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

F = ["BANKS","BANKL","BANKA","STRAS","ORT01","PSTLZ","REGIO","PROVZ","BRNCH","SWIFT"]
g = ConnectionGuard("P01"); g.connect()

def read(opts, tag):
    try:
        r = g.call("RFC_READ_TABLE", QUERY_TABLE="BNKA", DELIMITER="|",
            FIELDS=[{"FIELDNAME": f} for f in F], OPTIONS=opts, ROWCOUNT=20000)
        return [dict(zip(F,[v.strip() for v in x["WA"].split("|")])) for x in r.get("DATA",[])]
    except Exception as e:
        print(f"[{tag}] FAILED: {type(e).__name__}: {str(e)[:80]}"); return None

# 1) core-tool test: no WHERE, few rows
c = read([], "no-WHERE")
if c is not None:
    print(f"[core] BNKA readable: got {len(c)} rows (cap 20000). Sample SWIFTs: {[x['SWIFT'] for x in c[:3]]}")
    # filter SOGEUS33 in python across the batch
    hits = [x for x in c if x["SWIFT"].startswith("SOGEUS33")]
    print(f"[core] SOGEUS33 hits in first batch: {len(hits)}")
    for d in hits:
        print("-"*70)
        for k in F: print(f"  {k:<8}= '{d[k]}'")
    if not hits and len(c) >= 20000:
        print("[core] batch capped before reaching SOGEUS33 — trying BANKS='US' filter")
        us = read([{"TEXT":"BANKS = 'US'"}], "BANKS=US")
        if us:
            h2=[x for x in us if x["SWIFT"].startswith("SOGEUS33")]
            print(f"[BANKS=US] rows={len(us)} SOGEUS33 hits={len(h2)}")
            for d in h2:
                print("-"*70)
                for k in F: print(f"  {k:<8}= '{d[k]}'")
g.close()
