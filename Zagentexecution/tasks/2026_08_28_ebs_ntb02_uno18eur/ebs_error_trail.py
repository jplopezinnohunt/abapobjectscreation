# -*- coding: utf-8 -*-
"""¿Hay RASTRO de ficheros rechazados desde el 17.08?

Si FEB_FILE_HANDLING recoge un fichero y no puede asignarlo, lo mueve a la ruta de ERROR
y deja log de aplicacion (BALHDR/BALM, objeto FEB*). Cero rastro = el fichero no llega.

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


# ---- DIRECTORY suelto ---------------------------------------------------------
print("\n==== FEB_FILEPATH.DIRECTORY (campo suelto) ====")
try:
    dd = rd("DD03L", ["FIELDNAME", "LENG", "INTTYPE"], "TABNAME = 'FEB_FILEPATH' AND AS4LOCAL = 'A'", 50)
    for r in dd:
        print("   ", " | ".join(v.strip() for v in r.values()))
except Exception as e:
    print("   DD03L ->", str(e)[:90])
for f in (["DIRECTORY"], ["PATH"]):
    try:
        rows = rd("FEB_FILEPATH", f, "", 0)
        print("   %s -> %d filas" % (f, len(rows)))
        for r in rows:
            print("      ", list(r.values())[0].strip()[:200])
    except Exception as e:
        print("   %s -> %s" % (f, str(e)[:90]))

# ---- log de aplicacion --------------------------------------------------------
print("\n==== BALHDR — log de aplicacion de objetos FEB* / bancos, desde 01.08.2026 ====")
for obj in ("FEB%", "FI_FEB%", "BANK%"):
    try:
        rows = rd("BALHDR", ["OBJECT", "SUBOBJECT", "ALDATE", "ALTIME", "ALUSER", "ALPROG"],
                  "OBJECT LIKE '%s' AND ALDATE >= '20260801'" % obj, 0)
        print("\n   OBJECT LIKE '%s' -> %d filas" % (obj, len(rows)))
        agg = collections.Counter((r["OBJECT"].strip(), r["SUBOBJECT"].strip(),
                                   r["ALDATE"].strip()) for r in rows)
        for k, n in sorted(agg.items())[-25:]:
            print("      %s / %s / %s : %d" % (k[0], k[1], k[2], n))
    except Exception as e:
        print("   OBJECT LIKE '%s' -> ERROR %s" % (obj, str(e)[:90]))

# ---- ¿que objetos de log han tenido actividad estos dias? --------------------
print("\n==== BALHDR — TODOS los objetos con log desde 20.08.2026 (top) ====")
try:
    rows = rd("BALHDR", ["OBJECT", "SUBOBJECT", "ALDATE"], "ALDATE >= '20260820'", 0)
    agg = collections.Counter(r["OBJECT"].strip() for r in rows)
    for k, n in agg.most_common(30):
        print("   %-24s %d" % (k, n))
except Exception as e:
    print("   ERROR:", str(e)[:110])

print("\nOK")
