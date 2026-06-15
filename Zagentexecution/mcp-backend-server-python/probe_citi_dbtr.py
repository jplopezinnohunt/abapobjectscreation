import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")
def rd(table, where, fields):
    try:
        r=c.call("RFC_READ_TABLE",QUERY_TABLE=table,OPTIONS=[{"TEXT":where}],
                 FIELDS=[{"FIELDNAME":f} for f in fields])
        offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
        return [{nm:w["WA"][o:o+l].rstrip() for nm,o,l in offs} for w in r.get("DATA",[])]
    except Exception as e:
        print("  WHERE failed:", str(e)[:50]); return None
W = "TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
nodes = rd("DMEE_TREE_NODE", W, ["NODE_ID","TECH_NAME","PARENT_ID","NODE_TYPE","LEV","MP_SC_TAB","MP_SC_FLD","CK_EXIT_FUNC"])
print("CITI V000 nodes read:", len(nodes) if nodes else nodes)
if not nodes: sys.exit()
byid={n["NODE_ID"]:n for n in nodes}
kids={}
for n in nodes: kids.setdefault(n["PARENT_ID"],[]).append(n)
# conditions
conds = rd("DMEE_TREE_COND", W, ["NODE_ID","COND_NUMBER","ARG1_TAB","ARG1_FLD","ARG1_CONST","OPERATOR","ARG2_CONST","LINK_OPERATOR"]) or []
cond_by={}
for cr in conds: cond_by.setdefault(cr["NODE_ID"],[]).append(cr)
def cond_str(nid):
    rows=sorted(cond_by.get(nid,[]),key=lambda r:r["COND_NUMBER"])
    if not rows: return "(no condition → always emitted)"
    parts=[]
    for r in rows:
        left=f"{r['ARG1_TAB']}-{r['ARG1_FLD']}" if r['ARG1_FLD'] else r['ARG1_CONST']
        parts.append(f"{left} {r['OPERATOR']} '{r['ARG2_CONST']}' {r['LINK_OPERATOR']}".strip())
    return " ".join(parts)
def anc_is_dbtr(n):
    seen=0
    while n and seen<30:
        if n["TECH_NAME"]=="Dbtr": return True
        n=byid.get(n["PARENT_ID"]); seen+=1
    return False
# all PstlAdr under Dbtr
print("\n=== PstlAdr nodes under Dbtr ===")
for n in nodes:
    if n["TECH_NAME"]=="PstlAdr" and anc_is_dbtr(n):
        ch=[k["TECH_NAME"] for k in kids.get(n["NODE_ID"],[])]
        print(f"\nPstlAdr NODE_ID={n['NODE_ID']} LEV={n['LEV']} parent={n['PARENT_ID']}({byid.get(n['PARENT_ID'],{}).get('TECH_NAME','?')})")
        print(f"   children: {ch}")
        print(f"   CONDITION: {cond_str(n['NODE_ID'])}")
# also show the Dbtr node(s)
print("\n=== Dbtr node(s) ===")
for n in nodes:
    if n["TECH_NAME"]=="Dbtr":
        print(f"  Dbtr NODE_ID={n['NODE_ID']} LEV={n['LEV']} parent={n['PARENT_ID']}({byid.get(n['PARENT_ID'],{}).get('TECH_NAME','?')}) cond={cond_str(n['NODE_ID'])}")
        for k in kids.get(n["NODE_ID"],[]):
            print(f"     child: {k['TECH_NAME']:12} NODE_ID={k['NODE_ID']} cond={cond_str(k['NODE_ID'])}")
c.close()
