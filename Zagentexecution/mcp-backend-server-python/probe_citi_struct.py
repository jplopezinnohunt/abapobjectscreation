import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")
for t in ("DMEE_TREE_NODE","DMEE_TREE_COND"):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=t, NO_DATA="X")
    cols=[f["FIELDNAME"] for f in r.get("FIELDS",[])]
    print(f"=== {t} ===")
    print(", ".join(cols))
    print()
c.close()
