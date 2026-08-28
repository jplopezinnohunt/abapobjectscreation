# -*- coding: utf-8 -*-
"""Que programa corre el job 'EBS INTEGRATION', con que variante, y si se puede LISTAR
el directorio donde caen los ficheros del banco.

SOLO LECTURA.
"""
import sys, os, collections

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection

c = get_connection("P01")
print("SID real:", c.sid_real)


def rd(tab, fields, where, n=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=[{"TEXT": w} for w in ([where] if isinstance(where, str) else where)],
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, x["WA"].split("|"))) for x in r["DATA"]]


print("\n==== pasos del job EBS INTEGRATION ====")
for flds in (["JOBNAME", "PROGNAME"], ["JOBNAME", "PROGNAME", "VARIANT"],
             ["PROGNAME", "VARIANT"], ["JOBNAME", "STEPCOUNT", "PROGNAME", "VARIANT"]):
    try:
        st = rd("TBTCP", flds, "JOBNAME = 'EBS INTEGRATION'", 0)
        agg = collections.Counter(tuple(v.strip() for v in r.values()) for r in st)
        print("  campos %s -> %d filas" % (flds, len(st)))
        for k, n in agg.most_common(10):
            print("     ", k, "n=%d" % n)
        if st:
            break
    except Exception as e:
        print("  campos %s -> ERROR %s" % (flds, str(e)[:80]))

print("\n==== ¿que jobs con ese nombre existen (TBTCO) y quien los programo? ====")
try:
    for r in rd("TBTCO", ["JOBNAME", "SDLUNAME", "AUTHCKMAN", "PERIODIC", "PRDMINS"],
                "JOBNAME = 'EBS INTEGRATION' AND STRTDATE >= '20260827'", 20):
        print("   " + " | ".join(v.strip() for v in r.values()))
except Exception as e:
    print("   ERROR:", str(e)[:100])

print("\n==== listado de directorios del servidor (solo lectura) ====")
CANDS = ["/usr/sap/P01/interface/ebs", "/usr/sap/interface/ebs", "/interface/ebs",
         "/usr/sap/P01/DVEBMGS00/work", "/usr/sap/trans", "/interface", "/usr/sap/P01"]
for d in CANDS:
    for fm, key in (("RZL_READ_DIR_LOCAL", "NAME"), ("EPS2_GET_DIRECTORY_LISTING", "DIR_NAME")):
        try:
            kw = {key: d} if fm == "RZL_READ_DIR_LOCAL" else {"DIR_NAME": d}
            res = c.call(fm, **kw)
            ent = res.get("FILE_TBL") or res.get("DIR_LIST") or []
            print("  %-34s %-26s -> %d entradas" % (d, fm, len(ent)))
            for e in ent[:25]:
                nm = e.get("NAME") or e.get("FILENAME") or str(e)
                print("       ", str(nm)[:110])
            break
        except Exception as e:
            print("  %-34s %-26s -> %s" % (d, fm, str(e)[:70]))

print("\nOK")
