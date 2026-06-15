import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")
def read(where, fields, rc=50):
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_HEAD",
                   OPTIONS=[{"TEXT": where}] if where else [],
                   FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
        return [x["WA"] for x in r.get("DATA", [])], None
    except Exception as e:
        return [], str(e)
# is it client dependent? ask for MANDT
rows, err = read("", ["MANDT","TREE_TYPE","TREE_ID","VERSION"], rc=3)
print("client-dependent? sample with MANDT:", err or "")
for w in rows: print("  ", repr(w))
# LIKE searches
for pat in ("%UNES%","%CITI%","%SEPA%","%CGI%"):
    rows, err = read(f"TREE_ID LIKE '{pat}'", ["TREE_TYPE","TREE_ID","VERSION","EX_STATUS"])
    print(f"\nTREE_ID LIKE '{pat}': {len(rows)} rows {('ERR='+err) if err else ''}")
    for w in rows[:12]: print("   ", w)
# how many PAYM total / distinct tree types
rows, err = read("", ["TREE_TYPE"], rc=0)
from collections import Counter
print("\nTotal DMEE_TREE_HEAD rows:", len(rows), err or "")
print("TREE_TYPE distribution:", dict(Counter(w[:4].strip() for w in rows)))
c.close()
