import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
TREES=["/SEPA_CT_UNES","/CGI_XML_CT_UNESCO","/CGI_XML_CT_UNESCO_1"]
def rd(t,tree,f):
    W=f"TREE_ID = '{tree}' AND VERSION = '000'"
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
for tree in TREES:
    nodes=rd("DMEE_TREE_NODE",tree,["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID"])
    if not nodes:
        print(f"\n##### {tree}: (sin nodos / no existe)"); continue
    byid={n["NODE_ID"]:n for n in nodes}
    kids={}
    for n in nodes: kids.setdefault(n["PARENT_ID"],[]).append(n)
    conds=rd("DMEE_TREE_COND",tree,["NODE_ID","COND_NUMBER","ARG1_FLD","ARG1_TAB","OPERATOR","ARG2_CONST","LINK_OPERATOR"])
    cby={}
    for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
    def cs(nid):
        rs=sorted(cby.get(nid,[]),key=lambda r:r["COND_NUMBER"])
        return " ".join(f"{r['ARG1_TAB']}-{r['ARG1_FLD']} {r['OPERATOR']} {r['ARG2_CONST']} {r['LINK_OPERATOR']}".strip() for r in rs) or "sin cond"
    def is_under(n,tech):
        s=0
        while n and s<30:
            if n["TECH_NAME"]==tech: return True
            n=byid.get(n["PARENT_ID"]); s+=1
        return False
    pst=[n for n in nodes if n["TECH_NAME"]=="PstlAdr" and is_under(n,"Dbtr")]
    print(f"\n##### {tree}  ({len(nodes)} nodos) — Dbtr PstlAdr: {len(pst)} #####")
    for n in pst:
        ch=[k["TECH_NAME"] for k in kids.get(n["NODE_ID"],[])]
        struct="ESTR" if ("StrtNm" in ch or "BldgNb" in ch) else "no-estr"
        print(f"  PstlAdr {n['NODE_ID']} [{struct}] cond: {cs(n['NODE_ID'])}")
        # child PstCd/TwnNm conditions
        for k in kids.get(n["NODE_ID"],[]):
            if k["TECH_NAME"] in ("PstCd","TwnNm"):
                cc=cs(k["NODE_ID"])
                if cc!="sin cond": print(f"       <{k['TECH_NAME']}> cond: {cc}")
c.close()
