import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_HEAD",
           FIELDS=[{"FIELDNAME":"TREE_TYPE"},{"FIELDNAME":"TREE_ID"},{"FIELDNAME":"VERSION"}])
rows = [x["WA"] for x in r.get("DATA", [])]
print("total rows:", len(rows))
keys = ("CITI","UNES","SEPA","CGI","DC_V3")
hits = [w for w in rows if any(k in w for k in keys)]
print("\n=== matches CITI/UNES/SEPA/CGI/DC_V3:", len(hits), "===")
for w in hits: print("  ", repr(w))
paym = [w for w in rows if w[:4]=="PAYM"]
print("\n=== PAYM TREE_IDs:", len(paym), "===")
for w in paym: print("  ", repr(w[4:].rstrip()))
c.close()
