import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
def dump(tree):
    W=f"TREE_ID = '{tree}' AND VERSION = '000'"
    def rd(t,f):
        r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
        o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
        return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
    nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD"])
    byid={n["NODE_ID"]:n for n in nodes}
    conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_TAB","ARG1_FLD","ARG1_NODE","ARG1_REF_NAME","OPERATOR","ARG2_FLD","ARG2_TAB","ARG2_CONST","ARG2_NODE","LINK_OPERATOR"])
    cby={}
    for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
    def a(r,p): return f"{{{r[p+'REF_NAME']}}}" if r[p+'NODE'] else (f"{r[p+'TAB']}-{r[p+'FLD']}" if r[p+'FLD'] else f"'{r[p+'CONST']}'" if r.get(p+'CONST') else "''")
    def cs(nid):
        rs=sorted(cby.get(nid,[]),key=lambda r:r["COND_NUMBER"])
        return " ".join(f"{a(r,'ARG1_')} {r['OPERATOR']} {a(r,'ARG2_')} {r['LINK_OPERATOR']}".strip() for r in rs)
    def src(n):
        if n["MP_EXIT_FUNC"]: return f"exit {n['MP_EXIT_FUNC'].split('/')[-1]}"
        if n["MP_SC_FLD"]: return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}"
        return "(container)"
    def ordch(pid):
        out=[]; cur=byid.get(byid[pid]["FIRSTCHILD_ID"]); s=0
        while cur and s<40: out.append(cur); cur=byid.get(cur["BROTHER_ID"]); s+=1
        return out
    def walk(nid,d=0):
        for k in ordch(nid):
            cc=cs(k["NODE_ID"]); s=src(k)
            ex=[]
            if s!="(container)": ex.append(s)
            if cc: ex.append(f"IF[{cc}]")
            print(f"   {'  '*d}<{k['TECH_NAME']}> {' '.join(ex)}")
            walk(k["NODE_ID"],d+1)
    print(f"\n########## {tree} — UltmtDbtr ##########")
    ult=[n for n in nodes if n["TECH_NAME"]=="UltmtDbtr"]
    if not ult: print("  (no UltmtDbtr)")
    for u in ult:
        par=byid.get(u["PARENT_ID"],{}).get("TECH_NAME","?")
        cc=cs(u["NODE_ID"])
        print(f"  UltmtDbtr {u['NODE_ID']} (parent {par}) {('IF['+cc+']') if cc else ''}")
        walk(u["NODE_ID"],1)
for tree in ("/CITI/XML/UNESCO/DC_V3_01","/CGI_XML_CT_UNESCO"):
    dump(tree)
c.close()
