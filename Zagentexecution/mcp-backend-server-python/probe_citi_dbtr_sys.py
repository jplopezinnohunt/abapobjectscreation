import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
def analyze(sysid, ver):
    try: c = get_connection(sysid)
    except Exception as e: print(f"{sysid}: CONN FAIL {str(e)[:40]}"); return
    W=f"TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '{ver}'"
    def rd(t,f):
        try:
            r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
            o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
            return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
        except Exception as e: return []
    nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID"])
    if not nodes: print(f"\n[{sysid} V{ver}] no nodes (version may not exist)"); c.close(); return
    byid={n["NODE_ID"]:n for n in nodes}
    kids={}
    for n in nodes: kids.setdefault(n["PARENT_ID"],[]).append(n)
    conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_FLD","ARG1_TAB","OPERATOR","ARG2_CONST","LINK_OPERATOR"])
    cby={}
    for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
    def cs(nid):
        rs=sorted(cby.get(nid,[]),key=lambda r:r["COND_NUMBER"])
        if not rs: return "(NO condition -> always)"
        return " ".join(f"{r['ARG1_TAB']}-{r['ARG1_FLD']} {r['OPERATOR']} {r['ARG2_CONST']} {r['LINK_OPERATOR']}".strip() for r in rs)
    def is_dbtr(n):
        s=0
        while n and s<30:
            if n["TECH_NAME"]=="Dbtr": return True
            n=byid.get(n["PARENT_ID"]); s+=1
        return False
    pst=[n for n in nodes if n["TECH_NAME"]=="PstlAdr" and is_dbtr(n)]
    print(f"\n[{sysid} V{ver}] {len(nodes)} nodes | Dbtr PstlAdr count = {len(pst)}")
    for n in pst:
        ch=[k["TECH_NAME"] for k in kids.get(n["NODE_ID"],[])]
        struct="STRUCTURED" if ("StrtNm" in ch or "BldgNb" in ch) else "unstructured/hybrid"
        print(f"   PstlAdr {n['NODE_ID']} [{struct}] children={ch}")
        print(f"      cond: {cs(n['NODE_ID'])}")
    c.close()
for sysid in ("D01","V01"):
    for ver in ("000","001"):
        analyze(sysid, ver)
