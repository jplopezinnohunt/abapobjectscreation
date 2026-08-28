# -*- coding: utf-8 -*-
"""El job 'EBS INTEGRATION' corre FEB_FILE_HANDLING. ¿Con que variante, y DE DONDE saca
las rutas de fichero?

Si el paso no lleva variante, las rutas no estan en el job: estan en una tabla de
customizing que el programa lee. Asi que se lee el FUENTE en P01 (RPY_PROGRAM_READ,
solo lectura) y se sacan las tablas que toca.

SOLO LECTURA.
"""
import sys, os, re, collections

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


# ---- 1. variante del paso ----------------------------------------------------
print("\n==== 1. variante del paso del job ====")
for flds in (["JOBNAME", "VARIANT"], ["VARIANT"]):
    try:
        st = rd("TBTCP", flds, "JOBNAME = 'EBS INTEGRATION'", 0)
        agg = collections.Counter(tuple(v.strip() for v in r.values()) for r in st)
        print("   %s -> %s" % (flds, dict(agg)))
        break
    except Exception as e:
        print("   %s -> ERROR %s" % (flds, str(e)[:80]))

print("\n==== variantes existentes del programa FEB_FILE_HANDLING (VARID) ====")
try:
    for r in rd("VARID", ["REPORT", "VARIANT", "ENAME", "EDAT", "AENAME", "AEDAT"],
                "REPORT = 'FEB_FILE_HANDLING'", 100):
        print("   " + " | ".join(v.strip() for v in r.values()))
except Exception as e:
    print("   ERROR:", str(e)[:100])

# ---- 2. fuente del programa --------------------------------------------------
print("\n==== 2. FEB_FILE_HANDLING — fuente en P01 ====")
src = []
try:
    res = c.call("RPY_PROGRAM_READ", PROGRAM_NAME="FEB_FILE_HANDLING", WITH_INCLUDELIST="X")
    for k, v in res.items():
        if isinstance(v, list) and v and isinstance(v[0], dict) and "LINE" in v[0]:
            src = [x["LINE"] for x in v]
            print("   lineas: %d (%s)" % (len(src), k))
except Exception as e:
    print("   RPY_PROGRAM_READ ->", str(e)[:140])

if src:
    txt = "\n".join(src)
    out = os.path.join(HERE, "FEB_FILE_HANDLING.abap")
    open(out, "w", encoding="utf-8").write(txt)
    print("   guardado en", out)
    tabs = collections.Counter(re.findall(r"\bFROM\s+([A-Z0-9_/]{3,30})", txt.upper()))
    print("\n   TABLAS que lee (SELECT ... FROM):")
    for t, n in tabs.most_common(25):
        print("      %-28s %d" % (t, n))
    print("\n   lineas con PATH / DIR / FILE / DATASET:")
    for i, l in enumerate(src):
        u = l.upper()
        if any(k in u for k in ("DIR_NAME", "OPEN DATASET", "FILE_PATH", "FILEPATH",
                                "P_PATH", "DIRECTORY", "FILE_NAME", "FILENAME", "'/")):
            print("      %5d  %s" % (i + 1, l.strip()[:150]))

# ---- 3. tablas de customizing de FEB (file handling) -------------------------
print("\n==== 3. tablas de customizing FEB* que existen y tienen filas ====")
try:
    cands = sorted({x["TABNAME"].strip() for x in
                    rd("DD02L", ["TABNAME", "TABCLASS"], "TABNAME LIKE 'FEB%' AND TABCLASS = 'TRANSP'", 300)})
    print("   candidatas:", cands)
except Exception as e:
    print("   ERROR DD02L:", str(e)[:100])
    cands = []
for t in cands:
    if not any(k in t for k in ("FILE", "PATH", "HAND", "CUST", "V_")):
        continue
    try:
        fl = [x["FIELDNAME"].strip() for x in
              rd("DD03L", ["FIELDNAME"], "TABNAME = '%s' AND AS4LOCAL = 'A'" % t, 200)]
        fl = [f for f in fl if not f.startswith(".") and f != "MANDT"][:6]
        rows = rd(t, fl, "", 50)
        print("\n   --- %s : %d filas --- %s" % (t, len(rows), fl))
        for r in rows[:20]:
            print("        " + " | ".join(v.strip() for v in r.values()))
    except Exception as e:
        print("   %-24s -> %s" % (t, str(e)[:70]))

print("\nOK")
