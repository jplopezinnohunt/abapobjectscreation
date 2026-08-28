# -*- coding: utf-8 -*-
"""¿QUIEN importa los extractos, y siguen LLEGANDO los ficheros de la cuenta EUR?

Discriminante: si el fichero LLEGA y SAP lo rechaza, la causa es la config (ABSND
UNO12EUR ya no casa con T012K). Si el fichero NO llega, la causa esta aguas arriba
(Northern Trust / Coupa). Los dos casos se arreglan en sitios distintos, asi que no
se puede responder sin mirar el directorio.

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


# ---- 1. pasos de job con programas RFEB* -------------------------------------
print("\n==== 1. TBTCP — pasos de job con PROGNAME LIKE 'RFEB%' ====")
try:
    st = rd("TBTCP", ["JOBNAME", "PROGNAME", "VARIANT"], "PROGNAME LIKE 'RFEB%'", 0)
    agg = collections.Counter((r["JOBNAME"].strip(), r["PROGNAME"].strip(), r["VARIANT"].strip()) for r in st)
    print("   filas: %d" % len(st))
    for k, n in agg.most_common(40):
        print("   JOB=%-34s PROG=%-12s VAR=%-16s n=%d" % (k[0], k[1], k[2], n))
except Exception as e:
    print("   ERROR:", str(e)[:120])

# ---- 2. jobs por nombre -------------------------------------------------------
print("\n==== 2. TBTCO — jobs cuyo NOMBRE suena a extracto bancario (desde 01.08.2026) ====")
pats = ["%BANK%", "%EBS%", "%STATEMENT%", "%940%", "%RELEVE%", "%NTB%", "%COUPA%", "%SWIFT%"]
seen = {}
for p in pats:
    try:
        runs = rd("TBTCO", ["JOBNAME", "STRTDATE", "STRTTIME", "STATUS"],
                  "JOBNAME LIKE '%s' AND STRTDATE >= '20260801'" % p, 0)
    except Exception as e:
        print("   %s -> ERROR %s" % (p, str(e)[:70]))
        continue
    for r in runs:
        j = r["JOBNAME"].strip()
        d = r["STRTDATE"].strip() + r["STRTTIME"].strip()
        e0 = seen.setdefault(j, {"n": 0, "last": "", "st": collections.Counter()})
        e0["n"] += 1
        e0["st"][r["STATUS"].strip()] += 1
        if d > e0["last"]:
            e0["last"] = d
for j, e0 in sorted(seen.items(), key=lambda x: -x[1]["n"]):
    print("   %-40s corridas=%-5d ultima=%s estados=%s" % (j, e0["n"], e0["last"], dict(e0["st"])))

# ---- 3. rutas logicas de fichero del EBS --------------------------------------
print("\n==== 3. rutas logicas de fichero (FILEPATH / PATH) que suenan a EBS ====")
for tab, flds, where in (
    ("FILEPATH", ["PATHINTERN", "PATHEXTERN"], "PATHINTERN LIKE '%EBS%'"),
    ("PATH", ["PATHINTERN", "PATHEXTERN", "OPSYS"], "PATHINTERN LIKE '%EBS%'"),
    ("FILENAME", ["FILEINTERN"], "FILEINTERN LIKE '%EBS%'"),
    ("FILEPATH", ["PATHINTERN", "PATHEXTERN"], "PATHINTERN LIKE 'Z%'"),
):
    try:
        rows = rd(tab, flds, where, 200)
        print("   %-10s %-28s -> %d" % (tab, where, len(rows)))
        for r in rows[:30]:
            print("      ", " | ".join(v.strip() for v in r.values()))
    except Exception as e:
        print("   %-10s %-28s -> ERROR %s" % (tab, where, str(e)[:70]))

# ---- 4. FEBV_FILEPATH (config de ficheros del EBS moderno) --------------------
print("\n==== 4. FEBV_FILEPATH ====")
try:
    fn = sorted(x["FIELDNAME"].strip() for x in
                rd("DD03L", ["FIELDNAME"], "TABNAME = 'FEBV_FILEPATH' AND AS4LOCAL = 'A'", 200))
    fn = [f for f in fn if not f.startswith(".") and f != "MANDT"][:8]
    print("   campos:", fn)
    for r in rd("FEBV_FILEPATH", fn, "MANDT = '350'", 200):
        print("      ", " | ".join(v.strip() for v in r.values()))
except Exception as e:
    print("   ERROR:", str(e)[:140])

print("\nOK")
