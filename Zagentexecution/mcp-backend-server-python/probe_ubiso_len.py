import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
def rd(table, where, fields):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=table,OPTIONS=[{"TEXT":where}],FIELDS=[{"FIELDNAME":x} for x in fields])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
print("=== FPAYHX-UBISO field definition (DD03L) ===")
for r in rd("DD03L","TABNAME = 'FPAYHX' AND FIELDNAME = 'UBISO'",["FIELDNAME","ROLLNAME","LENG","DATATYPE","INTLEN"]):
    print(f"  field={r['FIELDNAME']} dataElem={r['ROLLNAME']} LEN={r['LENG']} type={r['DATATYPE']}")
    de=r['ROLLNAME']
    # data element -> domain -> check
    for d in rd("DD04L",f"ROLLNAME = '{de}'",["ROLLNAME","DOMNAME","LENG","DATATYPE"]):
        print(f"    dataElem {d['ROLLNAME']}: domain={d['DOMNAME']} LEN={d['LENG']} type={d['DATATYPE']}")
        dom=d['DOMNAME']
        for dm in rd("DD01L",f"DOMNAME = '{dom}'",["DOMNAME","LENG","DATATYPE","ENTITYTAB"]):
            print(f"      domain {dm['DOMNAME']}: LEN={dm['LENG']} type={dm['DATATYPE']} checkTable={dm['ENTITYTAB']}")
print("\n=== for reference: REGUH-UBNKS definition ===")
for r in rd("DD03L","TABNAME = 'REGUH' AND FIELDNAME = 'UBNKS'",["FIELDNAME","ROLLNAME","LENG","DATATYPE"]):
    print(f"  field={r['FIELDNAME']} dataElem={r['ROLLNAME']} LEN={r['LENG']} type={r['DATATYPE']}")
c.close()
