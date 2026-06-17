import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
PARTIES=["Dbtr","UltmtDbtr","Cdtr","UltmtCdtr"]
def load(tree):
    W=f"TREE_ID = '{tree}' AND VERSION = '000'"
    def rd(t,f):
        r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
        o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
        return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
    nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD","MP_OFFSET","LENGTH"])
    return {n["NODE_ID"]:n for n in nodes}, nodes
def src(n):
    if n["MP_EXIT_FUNC"]:
        e=n["MP_EXIT_FUNC"]; return "BADI" if "FI_CGI" in e else (e.split('/')[-1] if "CITIPMW" in e else e[:16])
    if n["MP_SC_FLD"]:
        off=f"+{n['MP_OFFSET']}({n['LENGTH']})" if n['MP_OFFSET'] not in('','0','000') else ""
        return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}{off}"
    return "·"
def party_tags(byid,nodes,party):
    # find PstlAdr under party; return list of (tagname, source) for the structured leaves
    def anc(n):
        s=0
        while n and s<30:
            if n["TECH_NAME"]==party: return True
            n=byid.get(n["PARENT_ID"]); s+=1
        return False
    def ordch(pid):
        out=[]; cur=byid.get(byid[pid]["FIRSTCHILD_ID"]); s=0
        while cur and s<40: out.append(cur); cur=byid.get(cur["BROTHER_ID"]); s+=1
        return out
    pas=[n for n in nodes if n["TECH_NAME"]=="PstlAdr" and anc(n)]
    res={}
    for pa in pas:
        for tag in ordch(pa["NODE_ID"]):
            # if container, look one level deeper for the real source
            kids=ordch(tag["NODE_ID"])
            if kids:
                res[tag["TECH_NAME"]] = " | ".join(f"{k['TECH_NAME']}:{src(k)}" for k in kids[:3])
            else:
                res.setdefault(tag["TECH_NAME"], src(tag))
    return res
ci,cin=load("/CITI/XML/UNESCO/DC_V3_01")
cg,cgn=load("/CGI_XML_CT_UNESCO")
for party in PARTIES:
    pc=party_tags(ci,cin,party); pg=party_tags(cg,cgn,party)
    tags=sorted(set(pc)|set(pg))
    print(f"\n===== {party} — CITI vs CGI =====")
    if not tags: print("   (sin PstlAdr en ninguno)")
    for t in tags:
        ct=pc.get(t,"—"); gt=pg.get(t,"—")
        print(f"   <{t:12}> CITI: {ct[:45]:45} | CGI: {gt[:45]}")
c.close()
