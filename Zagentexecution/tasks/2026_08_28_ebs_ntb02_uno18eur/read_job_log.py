# -*- coding: utf-8 -*-
"""¿El fichero LLEGA y SAP lo rechaza, o NO llega?

Es el discriminante que decide donde esta el arreglo. El log del job 'EBS INTEGRATION'
lo dice: si el fichero entra y no se puede asignar, hay mensaje. Si no hay nada, aguas
arriba (Northern Trust / Coupa) no lo esta dejando.

SOLO LECTURA.
"""
import sys, os

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


runs = rd("TBTCO", ["JOBNAME", "JOBCOUNT", "STRTDATE", "STRTTIME", "STATUS"],
          "JOBNAME = 'EBS INTEGRATION' AND STRTDATE >= '20260825'", 0)
runs.sort(key=lambda r: r["STRTDATE"].strip() + r["STRTTIME"].strip())
print("corridas recientes: %d" % len(runs))
for r in runs[-6:]:
    print("   %s %s count=%s st=%s" % (r["STRTDATE"].strip(), r["STRTTIME"].strip(),
                                       r["JOBCOUNT"].strip(), r["STATUS"].strip()))

for r in runs[-3:]:
    jc = r["JOBCOUNT"].strip()
    print("\n==== LOG de la corrida %s %s (count %s) ====" % (r["STRTDATE"].strip(),
                                                              r["STRTTIME"].strip(), jc))
    ok = False
    for fm, kw in (("BP_JOBLOG_READ", {"JOBNAME": "EBS INTEGRATION", "JOBCOUNT": jc}),
                   ("BP_JOBLOG_SHOW", {"JOBNAME": "EBS INTEGRATION", "JOBCOUNT": jc})):
        try:
            res = c.call(fm, **kw)
            for k, v in res.items():
                if isinstance(v, list) and v:
                    for line in v[:60]:
                        if isinstance(line, dict):
                            txt = line.get("TEXT") or line.get("MSGTEXT") or str(line)
                            print("   ", str(txt)[:160])
                        else:
                            print("   ", str(line)[:160])
                    ok = True
            break
        except Exception as e:
            print("   %s -> %s" % (fm, str(e)[:110]))
    if not ok:
        print("   (sin log legible por RFC)")

print("\nOK")
