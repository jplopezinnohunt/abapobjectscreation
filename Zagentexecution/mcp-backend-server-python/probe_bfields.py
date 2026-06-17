import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("P01")
def lbl(tab,fld):
    def rd(t,w,f):
        r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":w}],FIELDS=[{"FIELDNAME":x} for x in f])
        o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
        return [{n:w2["WA"][a:a+l].rstrip() for n,a,l in o} for w2 in r.get("DATA",[])]
    dd=rd("DD03L",f"TABNAME = '{tab}' AND FIELDNAME = '{fld}'",["ROLLNAME","LENG"])
    if not dd or not dd[0]["ROLLNAME"]: return f"{tab}-{fld}: (?)"
    t=rd("DD04T",f"ROLLNAME = '{dd[0]['ROLLNAME']}' AND DDLANGUAGE = 'E'",["DDTEXT"])
    return f"{tab}-{fld:7} = '{t[0]['DDTEXT'] if t else '?'}' (len {dd[0]['LENG']})"
for tab,f in [("FPAYP","BNAME"),("FPAYP","BLAND"),("FPAYP","BORT1"),("FPAYP","BSTRAS"),
              ("FPAYP","REF01"),("FPAYHX","NAMEZ")]:
    print(" ", lbl(tab,f))
c.close()
