# -*- coding: utf-8 -*-
"""Read the REAL sibling order of CdtrAgt/FinInstnId/PstlAdr children in P01.

WHY: the SocGen validator rejected v2 of /CGI_XML_CT_UNESCO with
"element 'StrtNm' is not expected here ... expected: 'AdrLine'" — a pain.001
xs:sequence violation. PstlAdr children must follow AdrTp Dept SubDept StrtNm
BldgNb PstCd TwnNm CtrySubDvsn Ctry AdrLine. This proves what P01 actually holds.

READ-ONLY. DMEE_TREE_NODE rejects WHERE-pushdown on this system (string cols) —
so read the tree unfiltered and filter in Python (rule: reference_p01_strg_columns_unreadable).
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from rfc_helpers import get_connection

TREE = "/CGI_XML_CT_UNESCO"
FIELDS = ["TREE_TYPE", "TREE_ID", "VERSION", "NODE_ID", "PARENT_ID",
          "BROTHER_ID", "FIRSTCHILD_ID", "TECH_NAME", "NODE_TYPE",
          "MP_SC_TAB", "MP_SC_FLD", "MP_EXIT_FUNC"]

SYS = sys.argv[1] if len(sys.argv) > 1 else "P01"
print("SYSTEM:", SYS)
conn = get_connection(SYS)
rows, off, CH = [], 0, 8
# chunk fields (RFC_READ_TABLE 512-byte line buffer)
def read(fields):
    # This P01 runs a hardened RFC_READ_TABLE: passing ROWSKIPS raises
    # OPTION_NOT_VALID "ROWSKIPS requires GET_SORTED". So: no paging, ROWCOUNT=0
    # (= all rows) in one call. Known constraint, same family as the FIKRS
    # ROWCOUNT=0 rule in reference_fm_ps_bcs_masterdata_refresher.
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_NODE",
                  DELIMITER="|", FIELDS=[{"FIELDNAME": f} for f in fields],
                  ROWCOUNT=0)
    return [d["WA"].split("|") for d in r["DATA"]]

a = read(FIELDS[:6])
b = read(FIELDS[6:])
recs = []
for x, y in zip(a, b):
    v = [c.strip() for c in x + y]
    recs.append(dict(zip(FIELDS, v)))
print("DMEE_TREE_NODE rows read from P01:", len(recs))

tree = [r for r in recs if r["TREE_ID"] == TREE]
print(f"{TREE}: {len(tree)} rows; versions =",
      sorted({r['VERSION'] for r in tree}))

by_id = {r["NODE_ID"]: r for r in tree}

def path(r, depth=0):
    names, cur = [], r
    while cur and depth < 20:
        names.append(cur["TECH_NAME"])
        cur = by_id.get(cur["PARENT_ID"]); depth += 1
    return " > ".join(reversed(names))

# find every PstlAdr whose ancestry contains CdtrAgt
AGENTS = ("CdtrAgt", "DbtrAgt", "IntrmyAgt1", "IntrmyAgt2")
targets = [r for r in tree if r["TECH_NAME"] == "PstlAdr"
           and any(a in path(r) for a in AGENTS)]
print(f"\nPstlAdr nodes under CdtrAgt: {len(targets)}")
ISO = ["AdrTp","Dept","SubDept","StrtNm","BldgNb","PstCd","TwnNm",
       "CtrySubDvsn","Ctry","AdrLine"]
for t in targets:
    print("\n" + "=" * 74)
    print(f"V{t['VERSION']}  NODE_ID={t['NODE_ID']}  {path(t)}")
    # walk the FIRSTCHILD -> BROTHER chain: that IS the emission order
    kids, cur = [], by_id.get(t["FIRSTCHILD_ID"])
    while cur:
        kids.append(cur)
        cur = by_id.get(cur["BROTHER_ID"])
    print(f"  emission order ({len(kids)} children):")
    for i, k in enumerate(kids, 1):
        src = f"{k['MP_SC_TAB']}-{k['MP_SC_FLD']}" if k["MP_SC_TAB"] else ""
        ex = f" exit={k['MP_EXIT_FUNC']}" if k["MP_EXIT_FUNC"] else ""
        print(f"    {i}. {k['TECH_NAME']:<14} {k['NODE_ID']:<14} {src}{ex}")
    seq = [k["TECH_NAME"] for k in kids if k["TECH_NAME"] in ISO]
    idx = [ISO.index(n) for n in seq]
    ok = idx == sorted(idx)
    print(f"  ISO order  : {seq}")
    print(f"  XSD-VALID  : {'YES' if ok else 'NO  <-- xs:sequence VIOLATION'}")
    if not ok:
        print(f"  expected   : {[n for n in ISO if n in seq]}")
conn.close()
