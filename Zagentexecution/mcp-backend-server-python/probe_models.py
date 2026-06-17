import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("D01")
TREES=["/SEPA_CT_UNES","/CITI/XML/UNESCO/DC_V3_01","/CGI_XML_CT_UNESCO","/CGI_XML_CT_UNESCO_1"]
# 1) PARAM_STRUC de cada árbol (DMEE_TREE_HEAD) - leer todo y filtrar
print("=== PARAM_STRUC (modelo de fondo) por árbol ===")
try:
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="DMEE_TREE_HEAD",FIELDS=[{"FIELDNAME":"TREE_ID"},{"FIELDNAME":"PARAM_STRUC"}])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    rows=[{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
    for x in rows:
        if any(t in x["TREE_ID"] for t in ("SEPA_CT_UNES","CITI/XML/UNESCO/DC_V3_01","CGI_XML_CT_UNESCO")):
            print(f"  {x['TREE_ID']:30} PARAM_STRUC = {x['PARAM_STRUC']}")
except Exception as e:
    print("  PARAM_STRUC err:", str(e)[:50])
# 2) exits por árbol (qué familia de exits usa)
print("\n=== Familia de exits por árbol (MP_EXIT_FUNC) ===")
for tree in TREES:
    W=f"TREE_ID = '{tree}' AND VERSION = '000'"
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="DMEE_TREE_NODE",OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":"MP_EXIT_FUNC"}])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    exits=[w["WA"][o[0][1]:o[0][1]+o[0][2]].rstrip() for w in r.get("DATA",[])]
    exits=[e for e in exits if e]
    fam=Counter()
    for e in exits:
        if "CITIPMW" in e: fam["CITIPMW"]+=1
        elif "CGI_DMEE" in e or "FI_CGI" in e: fam["FI_CGI (CGI BAdI)"]+=1
        elif "SEPA" in e: fam["SEPA exits"]+=1
        elif "Y_FI_DMEE" in e or "DMEE_ADR" in e: fam["Y_FI_DMEE (custom)"]+=1
        else: fam[e[:24]]+=1
    print(f"  {tree:28} total exits={len(exits)}  -> {dict(fam)}")
c.close()
