# -*- coding: utf-8 -*-
"""ABSND es la identificacion del REMITENTE del extracto (lo que trae el fichero en :25:)
y es lo que FF67 pinta como 'Bank Key | Account'. Aqui se mide:

  A. que ABSND ha llegado alguna vez con UNO* y hasta cuando
  B. si algun extracto entro YA con UNO18EUR (aunque fuera a parar a otro sitio)
  C. el job que importa los extractos y su variante (donde estan las rutas de fichero)

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


# ---- A. todo ABSND que contenga UNO ------------------------------------------
print("\n==== A. FEBKO — todo extracto cuyo REMITENTE (ABSND) lleva 'UNO' ====")
rows = rd("FEBKO", ["BUKRS", "HBKID", "HKTID", "ABSND", "AZDAT", "AZNUM", "ASTAT", "EFART"],
          "ABSND LIKE '%UNO%'", 0)
agg = collections.Counter()
last = {}
for r in rows:
    k = (r["HBKID"].strip(), r["HKTID"].strip(), r["ABSND"].strip())
    agg[k] += 1
    d = r["AZDAT"].strip()
    if d and (k not in last or d > last[k]):
        last[k] = d
for k, n in sorted(agg.items(), key=lambda x: -x[1]):
    print("  %-6s %-6s ABSND=[%s]  n=%-6d  ultimo=%s" % (k[0], k[1], k[2], n, last[k]))

print("\n  >>> ¿algun extracto con UNO18EUR? %s"
      % ([k for k in agg if "UNO18" in k[2]] or "NINGUNO"))

# ---- B. el ultimo extracto de CADA cuenta de NTB02 ----------------------------
print("\n==== B. NTB02 — ultimo extracto por cuenta ====")
rows2 = rd("FEBKO", ["BUKRS", "HBKID", "HKTID", "ABSND", "AZDAT", "AZNUM", "ASTAT", "EFART"],
           "BUKRS = 'UNES' AND HBKID = 'NTB02'", 0)
per = {}
for r in rows2:
    k = r["HKTID"].strip()
    d = r["AZDAT"].strip()
    if k not in per or d > per[k]["AZDAT"].strip():
        per[k] = r
for k, r in sorted(per.items()):
    print("  %-6s ultimo=%s  AZNUM=%s  ABSND=[%s]  ASTAT=%s" %
          (k, r["AZDAT"].strip(), r["AZNUM"].strip(), r["ABSND"].strip(), r["ASTAT"].strip()))

# ---- C. jobs de importacion de extractos -------------------------------------
print("\n==== C. jobs que ejecutan programas de extracto bancario ====")
progs = ["RFEBKA00", "RFEBKA30", "RFEBBU10", "RFEBLB20", "YTBAI001"]
for p in progs:
    try:
        st = rd("TBTCP", ["JOBNAME", "PROGNAME", "VARIANT", "JOBCOUNT"],
                "PROGNAME = '%s'" % p, 300)
    except Exception as e:
        print("  %s: ERROR %s" % (p, str(e)[:70]))
        continue
    names = collections.Counter((r["JOBNAME"].strip(), r["VARIANT"].strip()) for r in st)
    print("\n  --- %s : %d pasos de job ---" % (p, len(st)))
    for (j, v), n in names.most_common(20):
        print("     JOB=%-32s VARIANT=%-16s pasos=%d" % (j, v, n))

# ---- D. ultimas ejecuciones de esos jobs --------------------------------------
print("\n==== D. TBTCO — ejecuciones desde 01.08.2026 de los jobs de extracto ====")
jobs = set()
for p in progs:
    try:
        for r in rd("TBTCP", ["JOBNAME"], "PROGNAME = '%s'" % p, 300):
            jobs.add(r["JOBNAME"].strip())
    except Exception:
        pass
for j in sorted(jobs):
    try:
        runs = rd("TBTCO", ["JOBNAME", "STRTDATE", "STRTTIME", "STATUS", "ENDDATE"],
                  "JOBNAME = '%s' AND STRTDATE >= '20260801'" % j.replace("'", "''"), 200)
    except Exception as e:
        print("  %s: ERROR %s" % (j, str(e)[:60]))
        continue
    if not runs:
        continue
    st = collections.Counter(r["STATUS"].strip() for r in runs)
    lastr = max(runs, key=lambda r: r["STRTDATE"].strip() + r["STRTTIME"].strip())
    print("  %-34s corridas=%-5d estados=%-22s ultima=%s %s (%s)" %
          (j, len(runs), dict(st), lastr["STRTDATE"].strip(), lastr["STRTTIME"].strip(),
           lastr["STATUS"].strip()))

print("\nOK")
