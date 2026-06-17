import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("D01")
TREES=[("SEPA","/SEPA_CT_UNES"),("CITI","/CITI/XML/UNESCO/DC_V3_01"),("CGI","/CGI_XML_CT_UNESCO")]
PARTIES=["Dbtr","UltmtDbtr","Cdtr","UltmtCdtr"]
# 1) Event 05 registration (TFPM042FB)
print("=== Event 05 por formato (TFPM042FB) ===")
try:
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="TFPM042FB",FIELDS=[{"FIELDNAME":"FORMI"},{"FIELDNAME":"EVENT"},{"FIELDNAME":"FUNC"}])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    rows=[{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
    for x in rows:
        if any(t in x["FORMI"] for t in ("SEPA_CT_UNES","CITI/XML/UNESCO","CGI_XML_CT_UNESCO")) and x["EVENT"] in ("05","5"," 05"):
            print(f"   {x['FORMI']:28} EVENT={x['EVENT']} FUNC={x['FUNC']}")
    fmts={x["FORMI"] for x in rows if any(t in x["FORMI"] for t in ("SEPA_CT_UNES","CITI/XML/UNESCO","CGI_XML_CT_UNESCO")) and x['EVENT'] in ('05','5',' 05')}
    for tn,t in TREES:
        print(f"   {tn}: {'Event05 registrado' if t in fmts else '** SIN Event 05 **'}")
except Exception as e:
    print("   TFPM042FB err:", str(e)[:60])
# 2) matriz partido x formato: exit + estructura
print("\n=== Matriz: por árbol, por partido — PstlAdr + familia de exit ===")
def fam(e):
    if "CITIPMW" in e: return "CITIPMW"
    if "FI_CGI" in e: return "FI_CGI-BAdI"
    if "Y_FI_DMEE" in e: return "Y_FI_DMEE-custom"
    if "SEPA" in e: return "SEPA-std"
    return e[:18]
for tn,tree in TREES:
    W=f"TREE_ID = '{tree}' AND VERSION = '000'"
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="DMEE_TREE_NODE",OPTIONS=[{"TEXT":W}],
             FIELDS=[{"FIELDNAME":x} for x in ("NODE_ID","TECH_NAME","PARENT_ID","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD")])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    nodes=[{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
    byid={n["NODE_ID"]:n for n in nodes}
    def ancestor_party(n):
        s=0
        while n and s<30:
            if n["TECH_NAME"] in PARTIES: return n["TECH_NAME"]
            n=byid.get(n["PARENT_ID"]); s+=1
        return None
    # collect per party: pstladr present? structured? exits + src fields under it
    print(f"\n  ##### {tn} ({tree}) #####")
    for party in PARTIES:
        # nodes under this party that are address-related
        sub=[n for n in nodes if ancestor_party(n)==party]
        if not sub: print(f"    {party:11}: (ausente)"); continue
        has_pa=any(n["TECH_NAME"]=="PstlAdr" for n in sub)
        struct=any(n["TECH_NAME"] in ("StrtNm","BldgNb") for n in sub)
        exits=Counter(fam(n["MP_EXIT_FUNC"]) for n in sub if n["MP_EXIT_FUNC"])
        flds=Counter((n["MP_SC_TAB"]) for n in sub if n["MP_SC_FLD"])
        print(f"    {party:11}: PstlAdr={'Y' if has_pa else 'N'} estruct={'Y' if struct else 'N'} | exits={dict(exits)} | campos={dict(flds.most_common(4))}")
c.close()
