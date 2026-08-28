# -*- coding: utf-8 -*-
"""El job 'EBS INTEGRATION' corre y termina OK 12 veces al dia. Entonces, ¿que hace,
con que variante, y por que NTB02/EUR01 dejo de entrar el 14.08?

Un job en estado F (finished) NO significa que procesara algo: significa que no dumpeo.

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


for job in ("EBS INTEGRATION", "COUPA FI POSTING INTEGRATION"):
    print("\n================ JOB: %s ================" % job)
    st = rd("TBTCP", ["JOBNAME", "JOBCOUNT", "STEPCOUNT", "PROGNAME", "VARIANT", "AUTHCKNAM", "SDLUNAME", "TYP"],
            "JOBNAME = '%s'" % job, 0)
    print("  pasos registrados: %d" % len(st))
    agg = collections.Counter((r["PROGNAME"].strip(), r["VARIANT"].strip(), r["TYP"].strip(),
                               r["AUTHCKNAM"].strip()) for r in st)
    for k, n in agg.most_common(15):
        print("   PROG=%-22s VAR=%-18s TYP=%-3s USER=%-12s n=%d" % (k[0], k[1], k[2], k[3], n))

    runs = rd("TBTCO", ["JOBNAME", "JOBCOUNT", "STRTDATE", "STRTTIME", "ENDTIME", "STATUS"],
              "JOBNAME = '%s' AND STRTDATE >= '20260810'" % job, 0)
    runs.sort(key=lambda r: r["STRTDATE"].strip() + r["STRTTIME"].strip())
    print("  corridas desde 10.08: %d — ultimas 8:" % len(runs))
    for r in runs[-8:]:
        print("     %s %s->%s  st=%s  count=%s" % (r["STRTDATE"].strip(), r["STRTTIME"].strip(),
                                                   r["ENDTIME"].strip(), r["STATUS"].strip(),
                                                   r["JOBCOUNT"].strip()))

# ---- variantes: contenido -----------------------------------------------------
print("\n==== VARIANTES — contenido tecnico (VARID / VARIS) ====")
progs = sorted({r["PROGNAME"].strip() for r in rd("TBTCP", ["PROGNAME"], "JOBNAME = 'EBS INTEGRATION'", 0)})
print("  programas del job:", progs)
for p in progs:
    if not p:
        continue
    try:
        v = rd("VARID", ["REPORT", "VARIANT", "ENAME", "EDAT", "AENAME", "AEDAT"],
               "REPORT = '%s'" % p, 100)
        print("\n  --- variantes de %s : %d ---" % (p, len(v)))
        for r in v:
            print("     VAR=%-18s creada=%s por %s  modif=%s por %s" %
                  (r["VARIANT"].strip(), r["EDAT"].strip(), r["ENAME"].strip(),
                   r["AEDAT"].strip(), r["AENAME"].strip()))
    except Exception as e:
        print("  VARID %s -> %s" % (p, str(e)[:90]))

print("\nOK")
