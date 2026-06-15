import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
def rd(t,f,ver):
    W=f"TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '{ver}'"
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
for ver in ("000","001"):
    nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","EX_STATUS"],ver)
    byid={n["NODE_ID"]:n for n in nodes}
    kids={}
    for n in nodes: kids.setdefault(n["PARENT_ID"],[]).append(n)
    conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_FLD","ARG1_TAB","OPERATOR","ARG2_CONST","LINK_OPERATOR"],ver)
    cby={}
    for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
    def cs(nid):
        rs=sorted(cby.get(nid,[]),key=lambda r:r["COND_NUMBER"])
        if not rs: return "(SIN condicion -> siempre)"
        return " ".join(f"{r['ARG1_TAB']}-{r['ARG1_FLD']} {r['OPERATOR']} '{r['ARG2_CONST']}' {r['LINK_OPERATOR']}".strip() for r in rs)
    # find Dbtr
    dbtr=[n for n in nodes if n["TECH_NAME"]=="Dbtr"][0]
    # order children via FIRSTCHILD + BROTHER chain
    order=[]; cur=byid.get(dbtr["FIRSTCHILD_ID"])
    seen=0
    while cur and seen<50:
        order.append(cur); cur=byid.get(cur["BROTHER_ID"]); seen+=1
    print(f"\n===== D01 V{ver} — Dbtr children in EDITOR ORDER =====")
    pidx=0
    for ch in order:
        if ch["TECH_NAME"]=="PstlAdr":
            pidx+=1
            gk=[k["TECH_NAME"] for k in kids.get(ch["NODE_ID"],[])]
            struct="ESTRUCTURADO" if ("StrtNm" in gk or "BldgNb" in gk) else "no-estruct"
            print(f"  PstlAdr #{pidx}  NODE_ID={ch['NODE_ID']}  [{struct}]  EX_STATUS={ch['EX_STATUS']}")
            print(f"      hijos: {gk}")
            print(f"      cond:  {cs(ch['NODE_ID'])}")
        else:
            print(f"  ({ch['TECH_NAME']})")
c.close()
